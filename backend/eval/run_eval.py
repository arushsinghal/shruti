"""Lipi Eval Harness — offline clinical extraction evaluation.

Usage:
    # Describe-only: print extracted fields
    python -m eval.run_eval --transcript path/to/transcript.txt

    # Ground-truth comparison: print precision/recall/F1
    python -m eval.run_eval --transcript path/to/transcript.txt --ground-truth path/to/gt.json

    # Directory mode: process all case_XXX.txt / case_XXX_gt.json pairs
    python -m eval.run_eval --dir path/to/eval_cases/ --output results.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Import the extractor directly — no HTTP calls
from app.services.clinical_extractor import ClinicalExtractorService

_extractor = ClinicalExtractorService()


# ──────────────────────────────────────────────────────────────────────────────
# Normalisation helpers
# ──────────────────────────────────────────────────────────────────────────────

import re as _re

def _normalise(value: str) -> str:
    """Lowercase, strip, collapse whitespace, strip parenthetical annotations."""
    s = value.lower().strip()
    # Strip trailing parenthetical like "(3 days)" or "('bukhar')"
    s = _re.sub(r"\s*\(.*?\)\s*$", "", s)
    return " ".join(s.split())


def _normalise_set(values: list[str]) -> set[str]:
    return {_normalise(v) for v in values if v}


def _med_name(med: dict) -> str:
    """Extract normalised medication name from either format."""
    name = med.get("name", "") if isinstance(med, dict) else str(med)
    return _normalise(name)


# ──────────────────────────────────────────────────────────────────────────────
# Extraction wrapper
# ──────────────────────────────────────────────────────────────────────────────

def extract_from_transcript(transcript: str) -> dict[str, Any]:
    """Run clinical extraction and map to eval-friendly format."""
    raw = _extractor.extract(transcript)

    # Map extractor output to eval fields.
    # Fields not returned by the extractor are empty lists.
    return {
        "symptoms": raw.get("symptoms", []),
        "medications": raw.get("medications", []),
        "vitals": raw.get("vitals", []),
        "allergies": raw.get("allergies", []),
        "investigations": raw.get("investigations", []),
        "diagnoses": raw.get("diagnoses", []),
        "follow_up": raw.get("follow_up", []),
        # Fields that ground truth may contain but extractor does not produce
        "labs": raw.get("labs", []),
        "advice": raw.get("advice", []),
        "red_flags": raw.get("red_flags", []),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Scoring
# ──────────────────────────────────────────────────────────────────────────────

def _score_set_field(
    extracted: list[str], ground_truth: list[str]
) -> dict[str, Any]:
    """Score a simple string-list field by normalised set match."""
    ext_set = _normalise_set(extracted)
    gt_set = _normalise_set(ground_truth)

    tp = ext_set & gt_set
    fp = ext_set - gt_set
    fn = gt_set - ext_set

    precision = len(tp) / len(ext_set) if ext_set else (1.0 if not gt_set else 0.0)
    recall = len(tp) / len(gt_set) if gt_set else (1.0 if not ext_set else 0.0)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": len(tp),
        "fp": len(fp),
        "fn": len(fn),
        "false_positives": sorted(fp),
        "missed": sorted(fn),
    }


def _score_medications(
    extracted: list[dict], ground_truth: list[dict]
) -> dict[str, Any]:
    """Score medications by name match; dosage/frequency shown as warnings."""
    ext_names = {_med_name(m) for m in extracted if _med_name(m)}
    gt_names = {_normalise(m.get("name", "")) for m in ground_truth if m.get("name")}

    tp_names = ext_names & gt_names
    fp_names = ext_names - gt_names
    fn_names = gt_names - ext_names

    precision = len(tp_names) / len(ext_names) if ext_names else (1.0 if not gt_names else 0.0)
    recall = len(tp_names) / len(gt_names) if gt_names else (1.0 if not ext_names else 0.0)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    # Dosage/frequency warnings for matched medications
    warnings: list[str] = []
    gt_by_name = {_normalise(m.get("name", "")): m for m in ground_truth if m.get("name")}
    ext_by_name = {_med_name(m): m for m in extracted if isinstance(m, dict) and _med_name(m)}

    for name in tp_names:
        gt_med = gt_by_name.get(name, {})
        ext_med = ext_by_name.get(name, {})
        gt_dose = _normalise(gt_med.get("dosage", gt_med.get("dose", "")))
        ext_dose = _normalise(ext_med.get("dosage", ext_med.get("dose", "")))
        gt_freq = _normalise(gt_med.get("frequency", ""))
        ext_freq = _normalise(ext_med.get("frequency", ""))

        if gt_dose and ext_dose and gt_dose != ext_dose:
            warnings.append(f"{name}: dosage mismatch (extracted='{ext_dose}', gt='{gt_dose}')")
        if gt_freq and ext_freq and gt_freq != ext_freq:
            warnings.append(f"{name}: frequency mismatch (extracted='{ext_freq}', gt='{gt_freq}')")

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": len(tp_names),
        "fp": len(fp_names),
        "fn": len(fn_names),
        "false_positives": sorted(fp_names),
        "missed": sorted(fn_names),
        "warnings": warnings,
    }


def _score_vitals_or_labs(
    extracted: list[str], ground_truth: list[str]
) -> dict[str, Any]:
    """Score vitals/labs by normalised partial match with value mismatch warnings."""
    ext_set = _normalise_set(extracted)
    gt_set = _normalise_set(ground_truth)

    tp: set[str] = set()
    warnings: list[str] = []

    for gt_val in gt_set:
        gt_type = gt_val.split()[0] if gt_val.split() else gt_val
        matched = False
        for ext_val in ext_set:
            ext_type = ext_val.split()[0] if ext_val.split() else ext_val
            if gt_type == ext_type or gt_val in ext_val or ext_val in gt_val:
                tp.add(gt_val)
                matched = True
                if gt_val != ext_val:
                    warnings.append(f"value mismatch: extracted='{ext_val}', gt='{gt_val}'")
                break
        if not matched:
            pass  # counted as FN

    fp = ext_set - {e for e in ext_set for g in tp if g.split()[0] in e.split()[0] or g in e or e in g}
    fn = gt_set - tp

    precision = len(tp) / len(ext_set) if ext_set else (1.0 if not gt_set else 0.0)
    recall = len(tp) / len(gt_set) if gt_set else (1.0 if not ext_set else 0.0)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": len(tp),
        "fp": len(fp),
        "fn": len(fn),
        "false_positives": sorted(fp),
        "missed": sorted(fn),
        "warnings": warnings,
    }


def score(extracted: dict, ground_truth: dict) -> dict[str, Any]:
    """Score all fields and return a full results dict."""
    results: dict[str, Any] = {}

    # Simple set-match fields
    set_fields = ["symptoms", "diagnoses", "allergies", "investigations",
                  "advice", "follow_up", "red_flags"]
    for field in set_fields:
        ext_list = extracted.get(field, [])
        gt_list = ground_truth.get(field, [])
        # Flatten if any items are dicts (shouldn't be, but defensive)
        ext_strs = [str(x) for x in ext_list] if ext_list else []
        gt_strs = [str(x) for x in gt_list] if gt_list else []
        results[field] = _score_set_field(ext_strs, gt_strs)

    # Medications — scored by name, dosage/frequency as warnings
    results["medications"] = _score_medications(
        extracted.get("medications", []),
        ground_truth.get("medications", []),
    )

    # Vitals and labs — partial match with value warnings
    results["vitals"] = _score_vitals_or_labs(
        extracted.get("vitals", []),
        ground_truth.get("vitals", []),
    )
    results["labs"] = _score_vitals_or_labs(
        extracted.get("labs", []),
        ground_truth.get("labs", []),
    )

    return results


# ──────────────────────────────────────────────────────────────────────────────
# Display
# ──────────────────────────────────────────────────────────────────────────────

def print_extracted(extracted: dict, case_id: str = "") -> None:
    """Print extracted fields in human-readable format."""
    header = f"=== Extracted: {case_id} ===" if case_id else "=== Extracted Fields ==="
    print(f"\n{header}")
    for field, values in extracted.items():
        if not values:
            continue
        print(f"\n  {field}:")
        if field == "medications":
            for med in values:
                if isinstance(med, dict):
                    parts = [med.get("name", "?")]
                    if med.get("dosage"):
                        parts.append(med["dosage"])
                    if med.get("frequency"):
                        parts.append(med["frequency"])
                    print(f"    - {' | '.join(parts)}")
                else:
                    print(f"    - {med}")
        else:
            for v in values:
                print(f"    - {v}")


def print_scores(results: dict, case_id: str = "") -> None:
    """Print scoring table."""
    header = f"\n=== Scores: {case_id} ===" if case_id else "\n=== Scores ==="
    print(header)
    print(f"  {'Field':<16} {'Prec':>6} {'Rec':>6} {'F1':>6} {'TP':>4} {'FP':>4} {'FN':>4}")
    print(f"  {'─'*16} {'─'*6} {'─'*6} {'─'*6} {'─'*4} {'─'*4} {'─'*4}")

    for field, data in results.items():
        print(f"  {field:<16} {data['precision']:>6.2f} {data['recall']:>6.2f} {data['f1']:>6.2f} {data['tp']:>4d} {data['fp']:>4d} {data['fn']:>4d}")

        if data.get("false_positives"):
            print(f"    false positives: {', '.join(data['false_positives'])}")
        if data.get("missed"):
            print(f"    missed: {', '.join(data['missed'])}")
        if data.get("warnings"):
            for w in data["warnings"]:
                print(f"    ⚠ {w}")


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

def _run_single(transcript_path: Path, gt_path: Path | None) -> dict[str, Any] | None:
    """Run eval on a single transcript. Returns scores dict if ground truth provided."""
    transcript = transcript_path.read_text(encoding="utf-8").strip()
    case_id = transcript_path.stem

    extracted = extract_from_transcript(transcript)
    print_extracted(extracted, case_id)

    if gt_path and gt_path.exists():
        ground_truth = json.loads(gt_path.read_text(encoding="utf-8"))
        results = score(extracted, ground_truth)
        print_scores(results, case_id)
        return {"case_id": case_id, "scores": results}

    return None


def _run_dir(dir_path: Path, output_path: Path | None) -> None:
    """Run eval on all transcript files in a directory."""
    txt_files = sorted(dir_path.glob("*.txt"))
    if not txt_files:
        print(f"No .txt files found in {dir_path}")
        return

    all_results: list[dict] = []

    for txt_file in txt_files:
        gt_file = dir_path / f"{txt_file.stem}_gt.json"
        result = _run_single(txt_file, gt_file if gt_file.exists() else None)
        if result:
            all_results.append(result)

    if output_path and all_results:
        output_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
        print(f"\n✓ Results written to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lipi Eval Harness — offline clinical extraction evaluation"
    )
    parser.add_argument("--transcript", type=str, help="Path to a single transcript .txt file")
    parser.add_argument("--ground-truth", type=str, help="Path to ground truth .json file")
    parser.add_argument("--dir", type=str, help="Directory of case_XXX.txt / case_XXX_gt.json pairs")
    parser.add_argument("--output", type=str, help="Path to write machine-readable results JSON")

    args = parser.parse_args()

    if not args.transcript and not args.dir:
        parser.print_help()
        sys.exit(1)

    if args.transcript:
        tp = Path(args.transcript)
        if not tp.exists():
            print(f"Error: transcript file not found: {tp}")
            sys.exit(1)
        gt = Path(args.ground_truth) if args.ground_truth else None
        result = _run_single(tp, gt)
        if args.output and result:
            Path(args.output).write_text(json.dumps([result], indent=2), encoding="utf-8")
            print(f"\n✓ Results written to {args.output}")

    elif args.dir:
        dp = Path(args.dir)
        if not dp.is_dir():
            print(f"Error: directory not found: {dp}")
            sys.exit(1)
        _run_dir(dp, Path(args.output) if args.output else None)


if __name__ == "__main__":
    main()
