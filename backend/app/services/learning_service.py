"""Privacy-preserving flywheel learning service.

Consumes correction signals from two sources and aggregates them into
``extraction_knowledge`` entries with confidence scoring and admin review.

Signal sources (hybrid model):
    - Explicit:  doctor flags a specific entity correction via a dedicated
                 endpoint.  Weight = 1.0 (high-confidence, actionable).
    - Inferred:  derived from PUT /facts diffs by fuzzy-matching the added
                 canonical term against the scrubbed transcript.  Weight = 0.3
                 (lower-friction, noisier, requires more confirmations).

Key design invariants:
    - Only extraction knowledge is stored, never patient data.
    - A correction like ``paracetemol → paracetamol`` is PHI-free by
      construction: it is a fact about ASR behaviour / terminology, not a
      clinical observation.
    - Confidence is Bayesian: starts at 0.3 (base prior), rises as independent
      clinics confirm, auto-promotes at ≥0.9 AND ≥3 unique clinics.
    - Per-user idempotency caps prevent one noisy user from dominating.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.storage.db import db_connect

logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────
_PROMOTION_CONFIDENCE_THRESHOLD = 0.9
_PROMOTION_MIN_CLINICS = 3
_PROMOTION_MIN_CONFIRMATIONS = 3
_BASE_PRIOR = 0.3
_PRIOR_WEIGHT = 2.0  # weight of the base prior in the confidence formula

# Signal weights — explicit corrections carry far more signal than inferred ones.
WEIGHT_EXPLICIT = 1.0
WEIGHT_INFERRED = 0.3


class LearningService:
    """Aggregate correction signals into extraction knowledge with confidence scoring."""

    # ── Ingestion ──────────────────────────────────────────────────────────

    async def record_false_positive(
        self,
        *,
        user_id: str,
        surface_form: str,
        field: str,
        clinic_id: Optional[str] = None,
    ) -> Optional[int]:
        """Record that a surface form was a false positive (doctor rejected it).

        Increments the rejection counter on any candidate entry for this surface
        form, which lowers confidence and makes auto-promotion harder. If no
        entry exists yet, seeds one with a rejection so future occurrences must
        overcome the negative prior.
        """
        now = datetime.now(timezone.utc).isoformat()
        try:
            async with db_connect() as db:
                cursor = await db.execute(
                    """SELECT id, rejections, weighted_score, confirmations, status
                       FROM extraction_knowledge
                       WHERE surface_form = ? AND field = ?
                       LIMIT 1
                    """,
                    (surface_form, field),
                )
                row = await cursor.fetchone()
                if row is None:
                    # Seed with one rejection so future occurrences must overcome it
                    await db.execute(
                        """INSERT INTO extraction_knowledge
                           (knowledge_type, canonical_value, surface_form, field,
                            confidence, weighted_score, confirmations, rejections,
                            unique_clinics, status, confirming_users, created_at, updated_at)
                           VALUES (?, ?, ?, ?, ?, 0, 0, 1, 1, 'candidate', '[]', ?, ?)
                        """,
                        ("lexicon_term", surface_form, surface_form, field,
                         round(_BASE_PRIOR * _PRIOR_WEIGHT / (_PRIOR_WEIGHT + 1), 4),
                         now, now),
                    )
                    await db.commit()
                    logger.info("Seeded false-positive entry surface=%r field=%s", surface_form, field)
                    return None

                entry_id, rejections, weighted_score, confirmations, status = row
                if status == "promoted":
                    # Don't silently un-promote — requires admin review
                    logger.info("False positive on promoted entry id=%d — flagging for review", entry_id)
                    await db.execute(
                        "UPDATE extraction_knowledge SET rejections = ?, updated_at = ? WHERE id = ?",
                        (rejections + 1, now, entry_id),
                    )
                else:
                    new_rejections = rejections + 1
                    new_conf = (
                        _BASE_PRIOR * _PRIOR_WEIGHT + max(0, weighted_score)
                    ) / (_PRIOR_WEIGHT + max(0, weighted_score) + new_rejections)
                    await db.execute(
                        """UPDATE extraction_knowledge
                           SET rejections = ?, confidence = ?, updated_at = ?
                           WHERE id = ?
                        """,
                        (new_rejections, round(new_conf, 4), now, entry_id),
                    )
                await db.commit()
                logger.info("Recorded false positive surface=%r field=%s", surface_form, field)
                return entry_id
        except Exception:
            logger.exception("Failed to record false positive surface=%r", surface_form)
            return None

    async def record_correction(
        self,
        *,
        user_id: str,
        knowledge_type: str,
        canonical_value: str,
        surface_form: str,
        field: str,
        clinic_id: Optional[str] = None,
        weight: float = WEIGHT_EXPLICIT,
    ) -> Optional[int]:
        """Record a single correction signal.

        If a matching candidate already exists, this is treated as an
        independent confirmation (idempotent per user).  If no match,
        a new candidate entry is created.

        ``weight`` scales how much this observation moves the confidence:
        explicit corrections (1.0) dominate; inferred-from-diff (0.3) need
        more independent confirmations to reach the promotion threshold.

        Returns the knowledge entry id, or None on error / rejected entry.
        """
        now = datetime.now(timezone.utc).isoformat()

        try:
            async with db_connect() as db:
                # Check for existing entry
                cursor = await db.execute(
                """SELECT id, status, confirmations, rejections, unique_clinics,
                          confidence, weighted_score, confirming_users, confirming_clinics
                       FROM extraction_knowledge
                       WHERE knowledge_type = ? AND canonical_value = ? AND surface_form = ?
                    """,
                    (knowledge_type, canonical_value, surface_form),
                )
                row = await cursor.fetchone()

                if row is None:
                    # New candidate — seed confidence with this observation's weight
                    initial_confidence = _BASE_PRIOR
                    confirming_clinics_json = _to_json_list({clinic_id} if clinic_id else set())
                    cursor = await db.execute(
                        """INSERT INTO extraction_knowledge
                           (knowledge_type, canonical_value, surface_form, field,
                            confidence, weighted_score, confirmations, rejections,
                    unique_clinics, status, confirming_users, confirming_clinics, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 1, 0, ?, 'candidate', ?, ?, ?, ?)
                        """,
                        (
                            knowledge_type, canonical_value, surface_form, field,
                            round(initial_confidence, 4), weight,
                            1 if clinic_id else 0,
                        f'["{user_id}"]', confirming_clinics_json, now, now,
                        ),
                    )
                    await db.commit()
                    entry_id = cursor.lastrowid or 0
                    logger.info(
                        "Created correction candidate id=%d type=%s canonical=%r surface=%r field=%s weight=%.2f clinic=%s",
                        entry_id, knowledge_type, canonical_value, surface_form, field, weight, clinic_id,
                    )
                    return entry_id

                (entry_id, status, confirmations, rejections, unique_clinics,
                 conf, weighted_score, confirming_users_json, confirming_clinics_json) = row
                confirming_users = set(_parse_json_list(confirming_users_json))
                confirming_clinics = set(_parse_json_list(confirming_clinics_json))

                # Idempotent: skip if this user already confirmed (per-user cap)
                if user_id in confirming_users:
                    await db.commit()
                    return entry_id

                # Can't confirm rejected entries without admin re-approval
                if status == "rejected":
                    await db.commit()
                    return None

                confirming_users.add(user_id)
                new_confirmations = confirmations + 1
                new_weighted_score = max(weighted_score + weight, new_confirmations * weight)

                # Count distinct clinics exactly using the companion JSON list.
                if clinic_id:
                    confirming_clinics.add(clinic_id)
                new_clinics = len(confirming_clinics) if confirming_clinics else unique_clinics

                # Recalculate confidence (Bayesian: prior + accumulated weights)
                new_confidence = (
                    _BASE_PRIOR * _PRIOR_WEIGHT + new_weighted_score
                ) / (_PRIOR_WEIGHT + new_weighted_score + rejections)

                await db.execute(
                    """UPDATE extraction_knowledge
                    SET confirmations = ?, weighted_score = ?, confidence = ?,
                        confirming_users = ?, confirming_clinics = ?, unique_clinics = ?, updated_at = ?
                       WHERE id = ?
                    """,
                    (new_confirmations, round(new_weighted_score, 4),
                     round(new_confidence, 4),
                     _to_json_list(confirming_users), _to_json_list(confirming_clinics),
                     new_clinics, now, entry_id),
                )
                await db.commit()

                logger.info(
                    "Confirmed correction id=%d confirmations=%d weighted=%.3f confidence=%.3f clinics=%d",
                    entry_id, new_confirmations, new_weighted_score, new_confidence, new_clinics,
                )

                # Auto-promote check
                if (new_confidence >= _PROMOTION_CONFIDENCE_THRESHOLD
                        and new_clinics >= _PROMOTION_MIN_CLINICS
                        and new_confirmations >= _PROMOTION_MIN_CONFIRMATIONS):
                    await self._promote(db, entry_id, user_id, now)

                return entry_id

        except Exception:
            logger.exception("Failed to record correction type=%s canonical=%r", knowledge_type, canonical_value)
            return None

    # ── Admin review ──────────────────────────────────────────────────────

    async def admin_review_queue(
        self,
        status: str = "candidate",
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """Return knowledge entries pending admin review."""
        async with db_connect() as db:
            cursor = await db.execute(
                """SELECT id, knowledge_type, canonical_value, surface_form, field,
                          confidence, confirmations, rejections, unique_clinics, status,
                          created_at
                   FROM extraction_knowledge
                   WHERE status = ? ORDER BY confidence DESC
                   LIMIT ? OFFSET ?
                """,
                (status, limit, offset),
            )
            rows = await cursor.fetchall()
            columns = [
                "id", "knowledge_type", "canonical_value", "surface_form", "field",
                "confidence", "confirmations", "rejections", "unique_clinics", "status",
                "created_at",
            ]
            return [dict(zip(columns, row)) for row in rows]

    async def admin_approve(self, entry_id: int, admin_user_id: str) -> bool:
        """Manually promote a candidate to promoted status."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            async with db_connect() as db:
                await self._promote(db, entry_id, admin_user_id, now)
                return True
        except Exception:
            logger.exception("Failed to approve entry id=%d", entry_id)
            return False

    async def admin_reject(self, entry_id: int, admin_user_id: str) -> bool:
        """Reject a knowledge entry. Reversibly marks it as rejected."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            async with db_connect() as db:
                await db.execute(
                    """UPDATE extraction_knowledge
                       SET status = 'rejected', rejected_at = ?, rejected_by = ?, updated_at = ?
                       WHERE id = ? AND status != 'rejected'
                    """,
                    (now, admin_user_id, now, entry_id),
                )
                await db.commit()
                logger.info("Rejected knowledge entry id=%d by admin %s", entry_id, admin_user_id)
                return True
        except Exception:
            logger.exception("Failed to reject entry id=%d", entry_id)
            return False

    async def admin_revert(self, entry_id: int, admin_user_id: str) -> bool:
        """Restore a rejected entry back to candidate status."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            async with db_connect() as db:
                await db.execute(
                    """UPDATE extraction_knowledge
                       SET status = 'candidate', rejected_at = NULL, rejected_by = NULL,
                           updated_at = ?
                       WHERE id = ? AND status = 'rejected'
                    """,
                    (now, entry_id),
                )
                await db.commit()
                logger.info("Reverted knowledge entry id=%d back to candidate", entry_id)
                return True
        except Exception:
            logger.exception("Failed to revert entry id=%d", entry_id)
            return False

    # ── Stats ──────────────────────────────────────────────────────────────

    async def get_stats(self) -> dict:
        """Return flywheel statistics for admin dashboard."""
        async with db_connect() as db:
            cursor = await db.execute(
                """SELECT status, COUNT(*), AVG(confidence)
                   FROM extraction_knowledge GROUP BY status
                """,
            )
            rows = await cursor.fetchall()
            by_status = {}
            for row in rows:
                by_status[row[0]] = {"count": row[1], "avg_confidence": round(row[2], 4) if row[2] else 0}

            cursor = await db.execute("SELECT COUNT(*) FROM fact_corrections")
            total_corrections = (await cursor.fetchone())[0] or 0

            return {
                "knowledge_by_status": by_status,
                "total_corrections_recorded": total_corrections,
                "promotion_threshold": _PROMOTION_CONFIDENCE_THRESHOLD,
                "min_clinics": _PROMOTION_MIN_CLINICS,
                "signal_weights": {"explicit": WEIGHT_EXPLICIT, "inferred": WEIGHT_INFERRED},
            }

    # ── Knowledge retrieval for extractor overlay ──────────────────────────

    async def load_promoted_knowledge(self) -> dict[str, dict[str, str]]:
        """Load all promoted knowledge for injection into the extractor.

        Returns a dict keyed by overlay category the extractor understands:
            - ``asr_correction``  → {wrong: right}   (ASR normalization layer)
            - ``lexicon_term``    → {surface: canonical}  (symptom/med/diagnosis maps)

        The ``field`` column distinguishes which map a lexicon_term belongs to,
        but the extractor merges them into a single overlay per category and
        lets the per-stage merge logic route them.
        """
        async with db_connect() as db:
            cursor = await db.execute(
                """SELECT knowledge_type, field, surface_form, canonical_value
                   FROM extraction_knowledge WHERE status = 'promoted'
                """,
            )
            rows = await cursor.fetchall()

        overlay: dict[str, dict[str, str]] = {}
        for ktype, field, surface, canonical in rows:
            # ASR corrections always go to the asr_correction bucket.
            # Lexicon terms go to lexicon_term (the extractor's symptom/med maps
            # already filter by their own domain, so a med term won't fire in
            # the symptom stage and vice versa).
            bucket = field or ktype
            if bucket not in overlay:
                overlay[bucket] = {}
            overlay[bucket][surface] = canonical

        logger.info(
            "Loaded %d promoted knowledge entries across %d buckets",
            len(rows), len(overlay),
        )
        return overlay

    # ── Inference bridge (PUT /facts diff → knowledge) ─────────────────────

    async def infer_from_diff(
        self,
        *,
        user_id: str,
        added_canonical: str,
        field: str,
        scrubbed_transcript: str,
    ) -> Optional[int]:
        """Try to derive a lexicon_term correction from an added fact.

        When a doctor adds a missing entity via PUT /facts, search the scrubbed
        transcript for a fuzzy match to the canonical term.  If a close match
        exists (≥0.85 ratio) AND is not negated, record it as an inferred
        lexicon_term correction (weight 0.3).

        Returns the knowledge entry id, or None if no surface form could be
        derived (i.e. the term genuinely wasn't in the transcript — the doctor
        may be adding context they spoke but ASR dropped entirely).
        """
        surface = _find_surface_form(added_canonical, scrubbed_transcript)
        if surface is None:
            return None

        # Negation guard — don't learn a surface form that was negated in context
        if _is_surface_negated(surface, scrubbed_transcript):
            logger.info(
                "Skipping inferred correction: surface=%r is negated in transcript", surface,
            )
            return None

        logger.info(
            "Inferred lexicon correction: surface=%r → canonical=%r (field=%s)",
            surface, added_canonical, field,
        )
        return await self.record_correction(
            user_id=user_id,
            knowledge_type="lexicon_term",
            canonical_value=added_canonical,
            surface_form=surface,
            field=field,
            weight=WEIGHT_INFERRED,
        )

    # ── Internal ────────────────────────────────────────────────────────────

    @staticmethod
    async def _promote(db, entry_id: int, user_id: str, now: str) -> None:
        """Set status to promoted and record metadata.

        Task 33: confidence is kept at its Bayesian-computed value — no artificial
        1.0 ceiling that would mask low-evidence entries.
        Task 32: promotion_status = 'global' only when ≥ _PROMOTION_MIN_CLINICS unique
        clinics confirmed; otherwise stays 'clinic_scoped'.
        """
        cursor = await db.execute(
            "SELECT unique_clinics FROM extraction_knowledge WHERE id = ?", (entry_id,)
        )
        row = await cursor.fetchone()
        unique_clinics = row[0] if row else 0
        scope = "global" if unique_clinics >= _PROMOTION_MIN_CLINICS else "clinic_scoped"

        await db.execute(
            """UPDATE extraction_knowledge
               SET status = 'promoted', promoted_at = ?, promoted_by = ?, updated_at = ?,
                   promotion_status = ?
               WHERE id = ?
            """,
            (now, user_id, now, scope, entry_id),
        )
        await db.commit()
        logger.info("Promoted knowledge entry id=%d by %s scope=%s", entry_id, user_id, scope)

        # Task 38: reload extractor overlay in background so promotion takes effect immediately
        import asyncio
        try:
            from app.services.clinical_extractor import async_reload_knowledge
            asyncio.get_event_loop().create_task(async_reload_knowledge())
        except Exception:
            pass


# ── Helpers ────────────────────────────────────────────────────────────────

def _parse_json_list(raw: str | None) -> list[str]:
    """Parse a JSON list string, returning empty list on failure."""
    if not raw:
        return []
    try:
        import json
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _to_json_list(items: set[str] | list[str]) -> str:
    """Serialize a list/set of strings as a JSON array."""
    import json
    return json.dumps(sorted(items))


def _find_surface_form(canonical: str, transcript: str) -> Optional[str]:
    """Find the surface form in the transcript that best matches the canonical term.

    Uses fuzzy matching (rapidfuzz if available, else difflib).  Returns the
    surface form if ratio ≥ 0.85, else None.
    """
    canonical_lower = canonical.lower().strip()
    if not canonical_lower or not transcript:
        return None

    # Exact substring → no learning needed (extractor should've caught it)
    if canonical_lower in transcript.lower():
        return None

    # Tokenize transcript and fuzzy-match against canonical
    import re as _re
    tokens = _re.findall(r"\b[\w'-]+\b", transcript.lower())

    # Try single-token match first (covers "fevr" → "fever")
    best_ratio = 0.0
    best_token: Optional[str] = None
    for tok in tokens:
        ratio = _fuzzy_ratio(canonical_lower, tok)
        if ratio > best_ratio:
            best_ratio = ratio
            best_token = tok

    if best_ratio >= 0.85 and best_token and best_token != canonical_lower:
        return best_token

    return None


def _fuzzy_ratio(a: str, b: str) -> float:
    """Return similarity ratio in [0, 1].  Uses rapidfuzz if available."""
    try:
        from rapidfuzz import fuzz
        return fuzz.ratio(a, b) / 100.0
    except ImportError:
        import difflib
        return difflib.SequenceMatcher(None, a, b).ratio()


_NEGATION_WORDS = {
    "no", "not", "without", "denies", "denied", "deny", "absent",
    "negative", "rule out", "ruled out", "without",
}


def _is_surface_negated(surface: str, transcript: str) -> bool:
    """Check if the surface form appears negated within ±3 words in the transcript."""
    lower = transcript.lower()
    surface_lower = surface.lower()
    idx = lower.find(surface_lower)
    if idx < 0:
        return False

    # Grab the window of words around the match
    before = lower[max(0, idx - 30):idx]
    words_before = before.split()[-3:]
    return any(w in _NEGATION_WORDS for w in words_before)


# Module-level singleton (convention per AGENTS.md)
learning_service = LearningService()
