"""Per-doctor clinical memory assistant — Phase 1 (context-stuffing, no vector search).

See docs/obsidian/27_CLINICAL_MEMORY_ASSISTANT_SPEC.md for the full spec.

Hard rule, enforced here not just documented: this module must NEVER call a
foreign-hosted inference API with patient-derived data. ABDM's Health Data
Management Policy requires India-hosted processing for this data; Sarvam is
the only inference provider this module is allowed to call. The assertion in
_CHAT_URL below is a deliberate trip-wire, not decoration — if someone edits
this file to point at a foreign endpoint, the import fails loudly instead of
silently shipping a compliance violation.

Retrieval-only, never writes. This module never touches clinical_facts,
memory_state, or soap_note. Every answer must carry a citation back to the
specific visit(s) it drew from.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.services.patient_history_service import (
    build_patient_timeline,
    format_history_for_prompt,
)
from app.utils.config import settings

_log = logging.getLogger(__name__)

_CHAT_URL = "https://api.sarvam.ai/v1/chat/completions"
assert "sarvam.ai" in _CHAT_URL, "clinical_memory_service must only call Sarvam (on-shore) — see module docstring"

_SYSTEM_PROMPT = (
    "You are a clinical memory assistant for an Indian doctor using Lipi. You answer "
    "questions about a patient's own visit history using ONLY the visit summaries "
    "provided below. Never invent a fact that is not in the provided history. If the "
    "history doesn't answer the question, say so plainly. Reference visit dates in "
    "your answer, but never mention the visit ID string — the UI shows that "
    "separately. This is decision support only — the doctor makes all clinical "
    "decisions. Answer in 1-2 sentences, directly, no preamble."
)


class ClinicalMemoryError(Exception):
    pass


def _api_key() -> str:
    key = settings.sarvam_llm_api_key or settings.sarvam_api_key
    if not key:
        raise ClinicalMemoryError("No Sarvam API key configured (sarvam_llm_api_key or sarvam_api_key)")
    return key


async def query(
    *,
    user_id: str,
    doctor_name: str,
    patient_name: str,
    question: str,
) -> dict[str, Any]:
    """Answer a doctor's question about one patient's own confirmed history.

    Phase 1 scope only: single patient, one doctor's own sessions. No cross-patient
    search — that's Phase 2 (pgvector), not built yet. Returns an empty-history
    response rather than raising if the patient has no confirmed visits yet, so the
    UI can show a clean "nothing on file" state instead of an error.
    """
    if not settings.memory_assistant_enabled:
        raise ClinicalMemoryError("Memory assistant is disabled (memory_assistant_enabled=False)")

    timeline = await build_patient_timeline(user_id, patient_name)
    if timeline["total_visits"] == 0:
        return {
            "answer": "No confirmed visits on file for this patient yet.",
            "citations": [],
        }

    history_text = format_history_for_prompt(timeline)

    payload = {
        # sarvam-30b, not the 105b flagship: verified 2026-07-03 with two live test
        # calls (a single-fact lookup and a 3-visit multi-step reasoning question —
        # "did this patient ever have a bad reaction, what did we switch to") that
        # 30b matches 105b's answer quality on this retrieval task while costing
        # ~40% less per token and responding faster (~0.5s vs ~0.7-7s). This task is
        # lookup-and-synthesis over provided context, not open-ended reasoning, so
        # the smaller model has no real disadvantage here.
        "model": "sarvam-30b",
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"{history_text}\n\nDoctor's question: {question}",
            },
        ],
        "temperature": 0.2,
        # Verified 2026-07-03 against a live Sarvam-105B call: "medium" (default)
        # reasoning burned 729-860 completion tokens and ~7s on trivial questions.
        # Disabling reasoning entirely dropped that to ~34 tokens and ~0.7s with no
        # loss of answer accuracy on the same test prompt. Live-demo latency matters
        # more here than chain-of-thought quality for a single-fact lookup.
        "reasoning_effort": None,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                _CHAT_URL,
                headers={"api-subscription-key": _api_key(), "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        _log.warning("clinical_memory_service: Sarvam call failed: %s", exc)
        raise ClinicalMemoryError(f"Assistant unavailable: {exc}") from exc

    answer = data["choices"][0]["message"]["content"].strip()

    # Citations: every visit referenced in the prompt is a candidate citation. Phase 1
    # cites the whole visit set used, not per-sentence attribution — that refinement
    # can wait until real usage shows it's needed.
    citations = [
        {"session_id": v["session_id"], "visit_date": v["date"][:10]}
        for v in timeline["visits"]
    ]

    return {"answer": answer, "citations": citations}
