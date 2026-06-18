"""
FIR (First Information Report) Generator Service
Generates structured FIR documents from police station transcripts.
Research prototype — output requires officer review.
"""

import re
from datetime import datetime


class FIRGeneratorService:
    """Generates structured FIR reports from transcript text."""

    def generate_fir(self, transcript: str, session_id: str = "") -> dict:
        """
        Parse a police dictation transcript and produce a structured FIR.
        Returns a dict with FIR fields.
        """
        lower = transcript.lower()

        complainant = self._extract_complainant(transcript)
        accused = self._extract_accused(transcript)
        incident_date = self._extract_date(transcript)
        location = self._extract_location(transcript)
        offences = self._extract_offences(lower)
        incident_summary = self._summarise_incident(transcript)
        witnesses = self._extract_witnesses(transcript)

        now = datetime.utcnow()

        return {
            "fir_number": f"FIR/{now.year}/{session_id[:6].upper() or 'DRAFT'}",
            "date_of_filing": now.strftime("%d %B %Y"),
            "time_of_filing": now.strftime("%H:%M hrs"),
            "police_station": self._extract_station(transcript) or "Not specified",
            "district": self._extract_district(transcript) or "Not specified",
            "complainant_name": complainant or "Not identified",
            "complainant_address": self._extract_address(transcript) or "As per records",
            "accused_name": accused or "Unknown / Under investigation",
            "date_of_incident": incident_date or "As stated in complaint",
            "place_of_incident": location or "As stated in complaint",
            "offences_alleged": offences if offences else ["IPC Section to be determined"],
            "incident_summary": incident_summary,
            "witnesses": witnesses if witnesses else ["None identified at time of filing"],
            "property_involved": self._extract_property(transcript) or "Nil",
            "action_taken": "FIR registered. Investigation initiated.",
            "investigating_officer": "To be assigned by SHO",
        }

    # ---------------------------------------------------------------
    # Private extraction helpers
    # ---------------------------------------------------------------

    def _extract_complainant(self, text: str) -> str:
        patterns = [
            r"complainant(?:'s)?\s+name\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
            r"my\s+name\s+is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\s+(?:has\s+filed|is\s+filing|came\s+to\s+report)",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_accused(self, text: str) -> str:
        patterns = [
            r"accused\s+(?:person\s+)?(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
            r"perpetrator\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
            r"suspect\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_date(self, text: str) -> str:
        patterns = [
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
            r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b",
            r"\b(yesterday|today|last\s+\w+)\b",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1)
        return ""

    def _extract_location(self, text: str) -> str:
        patterns = [
            r"(?:at|near|in|from)\s+([A-Z][a-zA-Z\s]{3,40}(?:Road|Street|Nagar|Colony|Market|Area|Chowk|Bazaar|Block))",
            r"incident\s+(?:took\s+place|occurred|happened)\s+(?:at|near|in)\s+([^,.]+)",
            r"location\s+(?:is|was)\s+([^,.]+)",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_address(self, text: str) -> str:
        m = re.search(r"(?:address|residing at|lives at)\s+([^,.]{5,80})", text, re.IGNORECASE)
        return m.group(1).strip() if m else ""

    def _extract_station(self, text: str) -> str:
        m = re.search(r"([A-Z][a-zA-Z\s]+)\s+Police\s+Station", text)
        return m.group(0).strip() if m else ""

    def _extract_district(self, text: str) -> str:
        m = re.search(r"([A-Z][a-zA-Z\s]+)\s+[Dd]istrict", text)
        return m.group(1).strip() if m else ""

    def _extract_offences(self, lower: str) -> list[str]:
        offences = []
        ipc_map = {
            "theft": "IPC Section 378 – Theft",
            "robbery": "IPC Section 390 – Robbery",
            "assault": "IPC Section 351 – Assault",
            "murder": "IPC Section 302 – Murder",
            "cheating": "IPC Section 420 – Cheating",
            "fraud": "IPC Section 420 – Cheating / Fraud",
            "kidnap": "IPC Section 363 – Kidnapping",
            "abduction": "IPC Section 363 – Kidnapping / Abduction",
            "harassment": "IPC Section 498A – Harassment",
            "dowry": "IPC Section 498A – Dowry Harassment",
            "trespass": "IPC Section 447 – Criminal Trespass",
            "extortion": "IPC Section 383 – Extortion",
            "hurt": "IPC Section 323 – Voluntarily causing hurt",
            "grievous": "IPC Section 325 – Grievous hurt",
            "riot": "IPC Section 147 – Rioting",
            "drug": "NDPS Act – Possession / Trafficking",
            "molestation": "IPC Section 354 – Assault on woman with intent to outrage modesty",
        }
        for keyword, section in ipc_map.items():
            if keyword in lower:
                offences.append(section)
        return offences

    def _extract_property(self, text: str) -> str:
        patterns = [
            r"(?:stolen|missing|seized)\s+(?:items?|property|goods?):\s*([^.]+)",
            r"(?:cash|mobile|phone|jewellery|jewelry|vehicle|laptop|bag)\s+(?:worth|valued at|of)\s+(?:Rs\.?\s*)?\d+",
        ]
        results = []
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                results.append(m.group(0).strip())
        return "; ".join(results) if results else ""

    def _extract_witnesses(self, text: str) -> list[str]:
        witnesses = []
        m = re.findall(r"witness(?:ed by)?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})", text)
        witnesses.extend(m)
        return witnesses

    def _summarise_incident(self, text: str) -> str:
        """Return first 3 sentences as the incident summary."""
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        summary_sentences = [s for s in sentences if len(s) > 20][:4]
        return " ".join(summary_sentences) if summary_sentences else text[:400]
