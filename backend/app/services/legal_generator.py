"""
Legal Document Generator Service
Generates structured legal documents (affidavits, statements, proceedings) from transcripts.
Research prototype — output requires advocate/court review.
"""

import re
from datetime import datetime


class LegalGeneratorService:
    """Generates structured legal documents from spoken transcript."""

    def generate_legal_doc(self, transcript: str, session_id: str = "") -> dict:
        """
        Parse a legal dictation transcript and produce a structured legal document.
        Returns a dict with legal document fields.
        """
        lower = transcript.lower()
        now = datetime.utcnow()

        doc_type = self._detect_doc_type(lower)
        parties = self._extract_parties(transcript)
        court_details = self._extract_court(transcript)
        case_number = self._extract_case_number(transcript)
        facts = self._extract_facts(transcript)
        reliefs_sought = self._extract_reliefs(lower)
        legal_sections = self._extract_legal_sections(transcript)

        return {
            "document_type": doc_type,
            "document_ref": f"LEGAL/{now.year}/{session_id[:6].upper() or 'DRAFT'}",
            "date": now.strftime("%d %B %Y"),
            "court_name": court_details or "As per filing jurisdiction",
            "case_number": case_number or "To be assigned",
            "petitioner": parties.get("petitioner") or "As per records",
            "respondent": parties.get("respondent") or "As per records",
            "advocate": parties.get("advocate") or "As per enrollment",
            "legal_sections_cited": legal_sections if legal_sections else ["Sections to be determined by counsel"],
            "facts_of_the_case": facts if facts else [transcript[:300]],
            "reliefs_sought": reliefs_sought if reliefs_sought else ["As prayed in the petition"],
            "verification": "I, the deponent, do hereby solemnly affirm that the contents of this document are true and correct to the best of my knowledge and belief.",
            "status": "Draft — requires advocate review and notarisation",
        }

    # ---------------------------------------------------------------
    # Private extraction helpers
    # ---------------------------------------------------------------

    def _detect_doc_type(self, lower: str) -> str:
        if "affidavit" in lower:
            return "Affidavit"
        if "petition" in lower or "writ" in lower:
            return "Writ Petition"
        if "bail" in lower:
            return "Bail Application"
        if "appeal" in lower:
            return "Appeal"
        if "complaint" in lower:
            return "Legal Complaint"
        if "agreement" in lower or "contract" in lower:
            return "Legal Agreement"
        if "notice" in lower:
            return "Legal Notice"
        return "Legal Statement / Deposition"

    def _extract_parties(self, text: str) -> dict:
        parties: dict = {}
        patterns = {
            "petitioner": [
                r"petitioner\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
                r"plaintiff\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
                r"appellant\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
            ],
            "respondent": [
                r"respondent\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
                r"defendant\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
                r"opposite\s+party\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
            ],
            "advocate": [
                r"(?:advocate|counsel|lawyer|attorney)\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
            ],
        }
        for role, pats in patterns.items():
            for pat in pats:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    parties[role] = m.group(1).strip()
                    break
        return parties

    def _extract_court(self, text: str) -> str:
        patterns = [
            r"((?:High Court|Supreme Court|District Court|Sessions Court|Civil Court|Family Court|Magistrate Court)[^,.\n]{0,40})",
            r"((?:Hon'ble|Honourable)\s+[^,.\n]{5,60})",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""

    def _extract_case_number(self, text: str) -> str:
        patterns = [
            r"\b(?:Case|Writ|CRL|CIV|CS|WP|SLP)\s*(?:No\.?|Number)?\s*[\d/]+(?:/\d{4})?",
            r"\b\d{1,6}/\d{4}\b",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(0).strip()
        return ""

    def _extract_legal_sections(self, text: str) -> list[str]:
        sections = []
        # IPC, CPC, CrPC, IT Act, etc.
        patterns = [
            r"Section\s+\d+[A-Z]?\s+(?:of\s+)?(?:the\s+)?(?:IPC|CPC|CrPC|IT Act|POCSO|Evidence Act|Constitution|Transfer of Property Act|Contract Act)[^,.\n]{0,30}",
            r"Article\s+\d+\s+of\s+the\s+Constitution",
            r"Order\s+\w+\s+Rule\s+\d+\s+CPC",
        ]
        for pat in patterns:
            found = re.findall(pat, text, re.IGNORECASE)
            sections.extend([f.strip() for f in found])
        return list(dict.fromkeys(sections))  # deduplicate preserving order

    def _extract_facts(self, text: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        facts = [s.strip() for s in sentences if len(s.strip()) > 30]
        # Number them
        return [f"{i + 1}. {fact}" for i, fact in enumerate(facts[:8])]

    def _extract_reliefs(self, lower: str) -> list[str]:
        reliefs = []
        relief_keywords = {
            "injunction": "Grant of interim/permanent injunction",
            "bail": "Grant of bail to the applicant",
            "stay": "Stay of proceedings / order",
            "damages": "Award of damages and compensation",
            "declaration": "Declaration of rights as prayed",
            "mandamus": "Writ of mandamus directing the respondent",
            "certiorari": "Writ of certiorari quashing the impugned order",
            "custody": "Grant of custody as prayed",
            "compensation": "Payment of compensation",
        }
        for keyword, relief in relief_keywords.items():
            if keyword in lower:
                reliefs.append(relief)
        return reliefs
