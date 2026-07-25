"""Public landing-page chatbot: lightweight RAG over a curated knowledge base,
answered by Gemini. Scoped strictly to product/research/pricing/company
questions about Lipi, never clinical or medical advice.
"""

from __future__ import annotations

import logging
import re

from google import genai
from google.genai import types

from app.services.landing_chat_knowledge import KNOWLEDGE_CHUNKS
from app.utils.config import settings

logger = logging.getLogger(__name__)

_MODEL_ID = "gemini-2.5-flash"
_STOPWORDS = {
    "the", "a", "an", "is", "are", "do", "does", "how", "what", "why", "who",
    "which", "to", "of", "in", "on", "for", "and", "or", "your", "you", "it",
    "this", "that", "with", "can", "i", "we", "us", "about", "me",
}


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def _retrieve(query: str, top_k: int = 4) -> list[dict[str, str]]:
    """Simple term-overlap retrieval over the small curated corpus. The corpus
    is small enough (a dozen chunks) that a full embeddings pipeline is not
    worth the extra API call and latency, overlap scoring is a legitimate,
    fast, and fully deterministic retrieval step for this scale."""
    query_terms = _tokenize(query)
    if not query_terms:
        return KNOWLEDGE_CHUNKS[:top_k]

    scored = []
    for chunk in KNOWLEDGE_CHUNKS:
        chunk_terms = _tokenize(chunk["title"] + " " + chunk["text"])
        overlap = len(query_terms & chunk_terms)
        if overlap > 0:
            scored.append((overlap, chunk))

    if not scored:
        return KNOWLEDGE_CHUNKS[:top_k]

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


_SYSTEM_PROMPT = """You are the assistant on Lipi's public website, answering visitor \
questions about Lipi (an AI-native OPD documentation and clinical workflow service for \
Indian doctors).

Strict rules, follow all of them:
- Answer ONLY using the context provided below. If the context does not cover the \
question, say you don't have that information and suggest emailing \
arushsinghal98@gmail.com, do not guess or invent facts.
- NEVER answer medical questions, give clinical advice, or comment on symptoms, \
diagnoses, or treatment, even hypothetically. If asked, say this assistant only \
answers questions about the Lipi product and company, and clinical questions should \
go to a doctor.
- Keep answers short: 2-4 sentences, plain language, no markdown headers.
- Do not invent statistics, prices, or claims beyond what's in the context.

Context:
{context}
"""


class LandingChatService:
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        if self.api_key and not self.api_key.isascii():
            bad_positions = [i for i, ch in enumerate(self.api_key) if ord(ch) > 127]
            logger.error(
                "GEMINI_API_KEY contains non-ASCII characters (length=%d, bad char count=%d, "
                "first bad position=%d, ordinal=%d). This will break every outbound Gemini "
                "call via httpx header encoding. Value not logged.",
                len(self.api_key), len(bad_positions), bad_positions[0], ord(self.api_key[bad_positions[0]]),
            )

    def answer(self, message: str, history: list[dict[str, str]] | None = None) -> str:
        message = (message or "").strip()
        if not message:
            return "Ask me anything about Lipi, our research, or pricing."

        chunks = _retrieve(message)
        context = "\n\n".join(f"[{c['title']}]\n{c['text']}" for c in chunks)
        system_prompt = _SYSTEM_PROMPT.format(context=context)

        if not self.client:
            return self._fallback_answer(chunks)

        convo = ""
        for turn in (history or [])[-6:]:
            role = "Visitor" if turn.get("role") == "user" else "Assistant"
            convo += f"{role}: {turn.get('text', '')}\n"
        convo += f"Visitor: {message}\nAssistant:"

        try:
            response = self.client.models.generate_content(
                model=_MODEL_ID,
                contents=convo,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.2,
                    max_output_tokens=600,
                ),
            )
            text = (response.text or "").strip()
            return text or self._fallback_answer(chunks)
        except Exception as exc:
            logger.warning("Landing chat Gemini call failed: %s", exc, exc_info=True)
            return self._fallback_answer(chunks)

    @staticmethod
    def _fallback_answer(chunks: list[dict[str, str]]) -> str:
        if not chunks:
            return "I'm not sure about that. Email arushsinghal98@gmail.com and the team will help directly."
        top = chunks[0]
        return f"{top['text']} If you'd like more detail, email arushsinghal98@gmail.com."
