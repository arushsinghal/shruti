"""Ingests a patient's legacy paper records (lab reports) via Google's open-sourced
Medical Data Toolkit (https://github.com/Google-Health/medical-data-toolkit, Apache 2.0),
self-hosted and reusing the same GEMINI_API_KEY Lipi already holds.

This is deliberately separate from fhir_mapper.py: that service maps Lipi's own
live-consultation clinical_facts (already structured by local NLP) to FHIR for export.
This module goes the other direction — takes a photo/PDF of a document that predates
Lipi entirely, and turns it into clinical_facts so it can join the same patient
timeline. Toolkit currently supports laboratory/diagnostic reports only.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.utils.config import settings

logger = logging.getLogger(__name__)


class LegacyRecordImportError(Exception):
    """Raised when the toolkit call fails or returns no usable clinical data."""


def is_configured() -> bool:
    return bool(settings.medical_data_toolkit_url)


async def document_to_fhir(file_bytes: bytes, content_type: str) -> dict[str, Any]:
    """Calls the self-hosted Medical Data Toolkit's /document_to_fhir endpoint."""
    if not is_configured():
        raise LegacyRecordImportError("MEDICAL_DATA_TOOLKIT_URL is not configured.")

    url = settings.medical_data_toolkit_url.rstrip("/") + "/document_to_fhir"
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                url, content=file_bytes, headers={"Content-Type": content_type}
            )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        logger.exception("Medical Data Toolkit call failed")
        raise LegacyRecordImportError(f"Document processing failed: {e}") from e

    return resp.json()


def _observation_to_investigation_line(resource: dict[str, Any]) -> str | None:
    """Formats a FHIR Observation resource into one readable investigation line."""
    code = resource.get("code", {})
    name = code.get("text") or (code.get("coding") or [{}])[0].get("display")
    if not name:
        return None

    value = None
    if "valueQuantity" in resource:
        vq = resource["valueQuantity"]
        value = f"{vq.get('value', '')} {vq.get('unit', '')}".strip()
    elif "valueString" in resource:
        value = resource["valueString"]

    ref_range = ""
    ranges = resource.get("referenceRange") or []
    if ranges:
        r = ranges[0]
        low = r.get("low", {}).get("value")
        high = r.get("high", {}).get("value")
        if low is not None and high is not None:
            ref_range = f" (ref {low}-{high})"
        elif high is not None:
            ref_range = f" (ref <{high})"
        elif low is not None:
            ref_range = f" (ref >{low})"

    if value:
        return f"{name}: {value}{ref_range}"
    return name


def fhir_bundle_to_clinical_facts(
    toolkit_response: dict[str, Any],
) -> dict[str, Any]:
    """Translates the toolkit's response into Lipi's clinical_facts dict shape
    (same shape patient_history_service.py already reads: symptoms, medications,
    vitals, diagnoses, allergies, investigations, follow_up)."""
    investigations: list[str] = []
    report_date: str | None = None

    for doc in toolkit_response.get("standardized_medical_documents") or []:
        bundle = doc.get("fhir_bundle") or {}
        for entry in bundle.get("entry") or []:
            resource = entry.get("resource") or {}
            if resource.get("resourceType") == "Observation":
                line = _observation_to_investigation_line(resource)
                if line:
                    investigations.append(line)
                if not report_date and resource.get("effectiveDateTime"):
                    report_date = resource["effectiveDateTime"]
            elif resource.get("resourceType") == "Composition" and not report_date:
                report_date = resource.get("date")

    if not investigations:
        raise LegacyRecordImportError(
            "No lab observations could be extracted from this document."
        )

    return {
        "symptoms": [],
        "medications": {},
        "vitals": [],
        "diagnoses": [],
        "allergies": [],
        "investigations": investigations,
        "follow_up": [],
        "_imported_report_date": report_date,
    }
