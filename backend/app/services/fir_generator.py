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

    _NAME_PAT = r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})"
    _HINGLISH_STOPWORDS = re.compile(
        r"\s+(?:hai|hain|hoon|ho|tha|thi|the|ne|ko|ka|ki|ke|se|mein|par|pe|aur|bhi|"
        r"bolta|bolti|rehta|rehti|rehte|aaye|gaya|gayi|gaye|kiya|ki|kar|karte).*$",
        re.IGNORECASE,
    )

    def _extract_complainant(self, text: str) -> str:
        patterns = [
            # Label-based (most reliable)
            r"(?:complainant|filer|applicant)\s*[:\-]\s*" + self._NAME_PAT,
            r"(?:complainant(?:'s)?\s+name)\s+(?:is\s+)?" + self._NAME_PAT,
            # English
            r"(?:my name is|i am|i'm)\s+" + self._NAME_PAT,
            r"(?:filed by|reported by|lodged by)\s+" + self._NAME_PAT,
            # Hinglish
            r"(?:mera naam|hamara naam|naam hai|mein|main)\s+" + self._NAME_PAT,
            r"(?:maine|humne)\s+(?:apna naam)?\s*" + self._NAME_PAT,
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                name = m.group(1).strip()
                name = self._HINGLISH_STOPWORDS.sub("", name).strip().rstrip(".,;")
                if len(name) > 2:
                    return name
        return ""

    def _extract_accused(self, text: str) -> str:
        results = []
        seen = set()

        def add_names(raw: str):
            parts = re.split(r"\s*(?:,|and|aur|evam|tatha)\s*", raw)
            for p in parts:
                p = self._HINGLISH_STOPWORDS.sub("", p).strip().rstrip(".,;")
                # Keep only if it looks like a proper name (starts capital or title-cased)
                words = p.split()
                name_words = [w for w in words if w and w[0].isupper() and len(w) > 1]
                name = " ".join(name_words[:3])
                if name and name.lower() not in seen and len(name) > 2:
                    results.append(name)
                    seen.add(name.lower())

        patterns = [
            # Label-based (captures rest of line)
            r"(?:accused|suspect|perpetrator|offender|aaropee|aasami)\s*[:\-]\s*([^\n.]{3,80})",
            r"(?:accused|suspect)\s+(?:persons?\s+)?(?:are\s+|is\s+|named?\s+)?([^\n.]{3,60})",
            # Natural language
            r"(?:done by|committed by|carried out by)\s+([^\n.]{3,60})",
            # Hinglish — "Ramesh ne churaya", "Ramesh aur Suresh ne"
            r"((?:[A-Z][a-z]+)(?:\s*(?:,|aur|and|evam)\s*(?:[A-Z][a-z]+))*)\s+ne\b",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                add_names(m.group(1))
        return ", ".join(results) if results else ""

    def _extract_date(self, text: str) -> str:
        patterns = [
            r"(?:date of incident|incident date|on)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b",
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
            r"\b(aaj|kal|parso|yesterday|today|last\s+\w+)\b",
            # Hinglish dates
            r"\b(\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december))\b",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1)
        return ""

    def _extract_location(self, text: str) -> str:
        patterns = [
            # Label-based
            r"(?:location|place of incident|jagah|sthan|ghatna sthal)\s*[:\-]\s*([^.\n]{5,80})",
            r"(?:incident took place|occurred|happened|hua|hui)\s+(?:at|near|in|on|pe|par)\s+([^.,\n]{5,60})",
            r"(?:at|near|in|from|pe|par)\s+(\d+[,\s]+[A-Za-z\s]+(?:Nagar|Colony|Road|Street|Market|Chowk|Bazaar|Block|Sector|Ward|Mohalla|Gali|Lane|Marg|Path|Avenue))",
            r"(?:address|ghar|makaan)\s*[:\-]?\s*(\d+[^.,\n]{5,60})",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip().rstrip(".,;")
        return ""

    def _extract_address(self, text: str) -> str:
        patterns = [
            r"(?:address|residing at|lives at|rehta hai|rehti hai|ghar)\s*[:\-]?\s*([^.\n]{5,100})",
            r"\b(\d+[,\s]+[A-Za-z\s]+(?:Nagar|Colony|Road|Street|Block|Sector|Mohalla)[^.\n]{0,40})",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip().rstrip(".,;")
        return ""

    def _extract_station(self, text: str) -> str:
        patterns = [
            r"(?:police station|thana|थाना)\s*[:\-]\s*([A-Za-z\s]+?)(?:\n|,|\.|$)",
            r"([A-Za-z\s]+?)\s+(?:police station|thana)",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_district(self, text: str) -> str:
        patterns = [
            r"(?:district|zila|जिला)\s*[:\-]\s*([A-Za-z\s]+?)(?:\n|,|\.|$)",
            r"([A-Za-z\s]+?)\s+(?:district|zila)",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_offences(self, lower: str) -> list[str]:
        ipc_map = {
            # English keywords
            "theft": "IPC Section 378 – Theft",
            "stole": "IPC Section 378 – Theft",
            "stolen": "IPC Section 378 – Theft",
            "robbery": "IPC Section 390 – Robbery",
            "looted": "IPC Section 390 – Robbery",
            "assault": "IPC Section 351 – Assault",
            "beat": "IPC Section 323 – Voluntarily causing hurt",
            "beaten": "IPC Section 323 – Voluntarily causing hurt",
            "murder": "IPC Section 302 – Murder",
            "killed": "IPC Section 302 – Murder",
            "cheating": "IPC Section 420 – Cheating",
            "fraud": "IPC Section 420 – Cheating / Fraud",
            "kidnap": "IPC Section 363 – Kidnapping",
            "abduction": "IPC Section 363 – Kidnapping / Abduction",
            "harassment": "IPC Section 498A – Harassment",
            "dowry": "IPC Section 498A – Dowry Harassment",
            "trespass": "IPC Section 447 – Criminal Trespass",
            "broke": "IPC Section 447 – Criminal Trespass",
            "broke in": "IPC Section 457 – Lurking house-trespass",
            "extortion": "IPC Section 383 – Extortion",
            "hurt": "IPC Section 323 – Voluntarily causing hurt",
            "grievous": "IPC Section 325 – Grievous hurt",
            "riot": "IPC Section 147 – Rioting",
            "drug": "NDPS Act – Possession / Trafficking",
            "molestation": "IPC Section 354 – Assault on woman",
            "rape": "IPC Section 376 – Sexual Assault",
            "eve teasing": "IPC Section 354A – Sexual Harassment",
            "threatening": "IPC Section 506 – Criminal Intimidation",
            "threat": "IPC Section 506 – Criminal Intimidation",
            "damage": "IPC Section 427 – Mischief causing damage",
            # Hinglish keywords
            "churaya": "IPC Section 378 – Theft",
            "chori": "IPC Section 378 – Theft",
            "loot": "IPC Section 390 – Robbery",
            "maar": "IPC Section 323 – Voluntarily causing hurt",
            "dhamki": "IPC Section 506 – Criminal Intimidation",
            "tod": "IPC Section 427 – Mischief causing damage",
        }
        seen = set()
        offences = []
        for keyword, section in ipc_map.items():
            if keyword in lower and section not in seen:
                offences.append(section)
                seen.add(section)
        return offences

    def _extract_property(self, text: str) -> str:
        # Match items + optional value
        item_pattern = r"\b(laptop|mobile|phone|cash|money|jewellery|jewelry|jewel|gold|chain|sona|silver|chandi|vehicle|bike|car|scooter|watch|bag|purse|wallet|computer|tablet|rupees?|rs\.?\s*\d+|paisa|nakdi)\b"
        items = re.findall(item_pattern, text, re.IGNORECASE)
        # Also match "X rupees cash" style
        value_m = re.search(r"(?:rs\.?|rupees?)\s*[\d,]+", text, re.IGNORECASE)
        result = list(dict.fromkeys([i.strip() for i in items]))  # deduplicate
        if value_m and value_m.group(0) not in result:
            result.append(value_m.group(0))
        return ", ".join(result) if result else ""

    def _extract_witnesses(self, text: str) -> list[str]:
        # No IGNORECASE — names must be capitalised so [A-Z] is literal
        patterns = [
            r"(?i:witness(?:es)?|gawah|sakshi)\s*[:\-]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
            r"(?i:witnessed by|seen by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
            r"(?i:neighbor|neighbour|padosi|parosi)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:was|were)\s+(?:a\s+)?(?i:witness)",
        ]
        results = []
        seen = set()
        for pat in patterns:
            for m in re.finditer(pat, text):
                name = m.group(1).strip().rstrip(".,;")
                if name and name.lower() not in seen and len(name) > 2:
                    results.append(name)
                    seen.add(name.lower())
        return results

    def _summarise_incident(self, text: str) -> str:
        """Return first 4 meaningful sentences as the incident summary."""
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        summary_sentences = [s.strip() for s in sentences if len(s.strip()) > 20][:4]
        return " ".join(summary_sentences) if summary_sentences else text[:500]
