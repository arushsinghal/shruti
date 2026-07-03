# _pgx_rules.py — Validation Report

Generated: 2026-07-02

## Schema integrity checks performed

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | File imports without error | ✅ PASS | Loaded via importlib.util from a clean interpreter; no syntax/runtime errors. |
| 2 | _PGX_RULES is a non-empty list of exactly 15 rule dicts | ✅ PASS | Found 15 rules. |
| 3 | Every rule has a non-empty trigger_drugs set | ✅ PASS | 0 violations across 15 rules. |
| 4 | Every trigger_drugs entry is a lowercase string | ✅ PASS | 0 violations. |
| 5 | Every rule_id matches PGX_### format and is unique | ✅ PASS | 15 unique rule_ids, all matching ^PGX_\d{3}$. |
| 6 | Every data_quality value is one of INDIAN_DATA | SOUTH_ASIAN_PROXY | GLOBAL_PROXY | NO_INDIAN_DATA (with optional free-text proxy note) | ✅ PASS | 0 violations; all values start with a valid prefix. |
| 7 | Every indian_frequency_source contains a PMID or a named source (CPIC/GenomeIndia/IndiGen/gnomAD/medRxiv/meta-analysis/guideline) | ✅ PASS | 0 violations after correcting PGX_014 to cite PMID:11773869 (Balram et al. 2002) instead of an unverified proxy claim. |
| 8 | Every cpic_level is '1A' or '1B' | ✅ PASS | 0 violations. |
| 9 | observability_score and opd_actionability_score are in range 0-3 | ✅ PASS | 0 violations. |
| 10 | No rule has ships_now=True AND needs_genomic_data=True simultaneously (logical contradiction) | ✅ PASS | 0 violations. |
| 11 | _PGX_RULES_NEEDS_VOLUME exactly equals {r : not r.ships_now} | ✅ PASS | Set equality confirmed: 7 rules in needs-volume list, matching ships_now=False count. |
| 12 | Every alert_template is non-empty | ✅ PASS | 0 violations. |
| 13 | get_rules_for_drug() helper returns correct rule for spot-checked drugs (clopidogrel, primaquine) | ✅ PASS | Both spot checks returned expected rule_id. |

## Summary counts

- Total rules: **15**
- `ships_now=True` (deployable today as population-level flags): **8**
- `ships_now=False` (in `_PGX_RULES_NEEDS_VOLUME`, held back pending stronger evidence/observability/genomic input): **7**
- Data quality breakdown: {'INDIAN_DATA': 13, 'NO_INDIAN_DATA': 2}

## Known residual limitations (not schema violations, but material to disclose)

- Scores (Indian frequency, OPD actionability, observability) are literature-informed **expert
  judgment**, not measurements on Lipi's own patient outcomes. They should be treated as a
  starting prioritization, not a validated risk model, until real prescribing/outcome data is
  available to check against.
- Two rules (PGX_014, PGX_015) rely partly or wholly on non-Indian proxy data; PGX_015 in
  particular (statins) is included only to document a real evidence gap and is explicitly
  excluded from `ships_now`.
- The CPIC guideline PMID lists were pulled from the live CPIC API on 2026-07-02; CPIC updates
  its guidelines periodically, so this file should be refreshed if a rule's guideline is revised.
- This validation confirms **schema integrity and internal consistency**, not clinical accuracy.
  Every alert generated from this file is designed to be reviewed and confirmed by a doctor before
  any action is taken — the file's docstring and `get_rules_for_drug()` docstring both state this
  explicitly.
