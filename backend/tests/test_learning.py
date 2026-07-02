"""Tests for the privacy-preserving learning flywheel.

Covers: LearningService.record_correction(), duplicate confirmation,
auto-promotion, admin approve/reject/revert, privacy invariants.
"""

import pytest

import app.storage.db as db_module
from app.storage.db import db_connect
from app.services.learning_service import LearningService


# ── Module-level service instance (convention from test_services.py) ──────────
learning = LearningService()


@pytest.fixture(autouse=True)
async def isolated_db(tmp_path):
    """Fresh SQLite for each test — mirrors test_routes.py pattern."""
    original = db_module._DB_PATH
    db_module._DB_PATH = str(tmp_path / "test_learning.db")
    await db_module.init_db()
    yield
    db_module._DB_PATH = original


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _count(table: str, where: str = "1=1", params: tuple = ()) -> int:
    async with db_connect() as db:
        cursor = await db.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params)
        row = await cursor.fetchone()
    return int(row[0])


async def _get_entry(entry_id: int) -> dict | None:
    async with db_connect() as db:
        cursor = await db.execute(
            "SELECT id, knowledge_type, canonical_value, surface_form, field, "
            "confidence, confirmations, rejections, unique_clinics, status, "
            "confirming_users, promoted_at, promoted_by, rejected_at, rejected_by "
            "FROM extraction_knowledge WHERE id = ?",
            (entry_id,),
        )
        row = await cursor.fetchone()
    if not row:
        return None
    cols = [
        "id", "knowledge_type", "canonical_value", "surface_form", "field",
        "confidence", "confirmations", "rejections", "unique_clinics", "status",
        "confirming_users", "promoted_at", "promoted_by", "rejected_at", "rejected_by",
    ]
    return dict(zip(cols, row))


# ══════════════════════════════════════════════════════════════════════════════
# 1. record_correction() creates candidate entries
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_record_correction_creates_candidate():
    entry_id = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="paracetamol",
        surface_form="paracetemol",
        field="medications",
    )
    assert entry_id is not None
    entry = await _get_entry(entry_id)
    assert entry is not None
    assert entry["status"] == "candidate"
    assert entry["confirmations"] == 1
    assert entry["canonical_value"] == "paracetamol"
    assert entry["surface_form"] == "paracetemol"
    assert entry["field"] == "medications"


@pytest.mark.anyio
async def test_record_correction_returns_id():
    entry_id = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="symptom_synonym",
        canonical_value="fever",
        surface_form="bukhar",
        field="symptoms",
    )
    assert isinstance(entry_id, int)
    assert entry_id > 0


@pytest.mark.anyio
async def test_record_correction_base_prior_confidence():
    """New entries start at the base prior confidence (0.3)."""
    entry_id = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="amoxicillin",
        surface_form="amoxicilin",
        field="medications",
    )
    entry = await _get_entry(entry_id)
    assert entry["confidence"] == pytest.approx(0.3, abs=0.01)


# ══════════════════════════════════════════════════════════════════════════════
# 2. Duplicate corrections increment confirmation_count
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_duplicate_correction_increments_confirmations():
    id1 = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="paracetamol",
        surface_form="paracetemol",
        field="medications",
    )
    id2 = await learning.record_correction(
        user_id="doc_2",
        knowledge_type="asr_correction",
        canonical_value="paracetamol",
        surface_form="paracetemol",
        field="medications",
    )
    assert id1 == id2, "Same correction from different users should return same entry"
    entry = await _get_entry(id1)
    assert entry["confirmations"] == 2


@pytest.mark.anyio
async def test_same_user_idempotent():
    """Same user confirming again must NOT increment."""
    id1 = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="paracetamol",
        surface_form="paracetemol",
        field="medications",
    )
    id2 = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="paracetamol",
        surface_form="paracetemol",
        field="medications",
    )
    assert id1 == id2
    entry = await _get_entry(id1)
    assert entry["confirmations"] == 1, "Same user should not double-count"


@pytest.mark.anyio
async def test_confidence_increases_with_confirmations():
    """More independent confirmations should raise confidence."""
    entry_id = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="metformin",
        surface_form="metformin",
        field="medications",
    )
    initial = (await _get_entry(entry_id))["confidence"]

    await learning.record_correction(
        user_id="doc_2",
        knowledge_type="asr_correction",
        canonical_value="metformin",
        surface_form="metformin",
        field="medications",
    )
    after_second = (await _get_entry(entry_id))["confidence"]
    assert after_second > initial


# ══════════════════════════════════════════════════════════════════════════════
# 3. maybe_promote() — auto-promotion when confidence >= threshold
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_auto_promotion_requires_min_clinics():
    """Even with enough confirmations, unique_clinics < 3 blocks auto-promote.

    Note: The current implementation doesn't separately track unique clinics
    from unique users, so unique_clinics stays at 1 after creation.
    With 3+ confirmations and high confidence, the unique_clinics gate
    prevents auto-promotion.
    """
    entry_id = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="azithromycin",
        surface_form="azithromycin",
        field="medications",
    )
    # Add confirmations from different users
    for i in range(2, 6):
        await learning.record_correction(
            user_id=f"doc_{i}",
            knowledge_type="asr_correction",
            canonical_value="azithromycin",
            surface_form="azithromycin",
            field="medications",
        )

    entry = await _get_entry(entry_id)
    # unique_clinics stays at 1 (not updated by record_correction currently),
    # so auto-promotion should NOT fire even though confirmations >= 3
    assert entry["status"] == "candidate"


@pytest.mark.anyio
async def test_auto_promotion_fires_when_all_conditions_met():
    """Force the conditions via direct DB manipulation, then confirm auto-promotion.

    The Bayesian formula requires ~12 confirmations to reach 0.9 confidence
    organically: (0.3*2 + n) / (2 + n) >= 0.9 => n >= 12.
    We set unique_clinics=3 and confirmations=11 with high confidence via DB,
    then add the 12th confirmation via record_correction to trigger auto-promote.
    """
    import json

    entry_id = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="ibuprofen",
        surface_form="ibuprofan",
        field="medications",
    )
    # Set preconditions: 11 confirmations, unique_clinics=3, high confidence
    # Confidence at 11: (0.6 + 11) / (2 + 11) = 11.6/13 = 0.892 (just below 0.9)
    async with db_connect() as db:
        await db.execute(
            """UPDATE extraction_knowledge
               SET unique_clinics = 3, confirmations = 11,
                   confirming_users = ?,
                   confidence = 0.892
               WHERE id = ?""",
            (json.dumps([f"doc_{i}" for i in range(1, 12)]), entry_id),
        )
        await db.commit()

    # The 12th confirmation should push confidence to (0.6+12)/(2+12) = 0.9 and trigger auto-promote
    await learning.record_correction(
        user_id="doc_12",
        knowledge_type="asr_correction",
        canonical_value="ibuprofen",
        surface_form="ibuprofan",
        field="medications",
    )

    entry = await _get_entry(entry_id)
    assert entry["status"] == "promoted"
    assert entry["confidence"] >= 0.8  # Bayesian-computed; no artificial 1.0 ceiling (task 33)
    assert entry["promoted_at"] is not None


# ══════════════════════════════════════════════════════════════════════════════
# 4. Admin approve() and reject() change status correctly
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_admin_approve_promotes():
    entry_id = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="cetirizine",
        surface_form="cetrizine",
        field="medications",
    )
    result = await learning.admin_approve(entry_id, admin_user_id="admin_1")
    assert result is True

    entry = await _get_entry(entry_id)
    assert entry["status"] == "promoted"
    assert entry["promoted_by"] == "admin_1"
    # Admin override promotes regardless of confidence — confidence stays Bayesian (task 33)
    assert entry["confidence"] > 0


@pytest.mark.anyio
async def test_admin_reject_sets_rejected():
    entry_id = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="aspirin",
        surface_form="asprin",
        field="medications",
    )
    result = await learning.admin_reject(entry_id, admin_user_id="admin_1")
    assert result is True

    entry = await _get_entry(entry_id)
    assert entry["status"] == "rejected"
    assert entry["rejected_by"] == "admin_1"
    assert entry["rejected_at"] is not None


@pytest.mark.anyio
async def test_rejected_entry_blocks_further_confirmation():
    """A rejected entry cannot receive new confirmations."""
    entry_id = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="metoprolol",
        surface_form="metoprolal",
        field="medications",
    )
    await learning.admin_reject(entry_id, admin_user_id="admin_1")

    # Another user tries to confirm — should return None
    result = await learning.record_correction(
        user_id="doc_2",
        knowledge_type="asr_correction",
        canonical_value="metoprolol",
        surface_form="metoprolal",
        field="medications",
    )
    assert result is None

    entry = await _get_entry(entry_id)
    assert entry["confirmations"] == 1, "Rejected entry must not accept new confirmations"


@pytest.mark.anyio
async def test_admin_revert_restores_candidate():
    entry_id = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="losartan",
        surface_form="losarton",
        field="medications",
    )
    await learning.admin_reject(entry_id, admin_user_id="admin_1")
    result = await learning.admin_revert(entry_id, admin_user_id="admin_1")
    assert result is True

    entry = await _get_entry(entry_id)
    assert entry["status"] == "candidate"
    assert entry["rejected_at"] is None
    assert entry["rejected_by"] is None


# ══════════════════════════════════════════════════════════════════════════════
# 5. Privacy invariant: corrections are PHI-free by construction
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_correction_stores_drug_names_not_patient_data():
    """key + canonical_value must be drug names, symptoms, or ASR patterns —
    never patient names, IDs, or contact info."""
    entry_id = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="paracetamol",
        surface_form="paracetemol",
        field="medications",
    )
    entry = await _get_entry(entry_id)
    # Structural assertion: the stored values are clinical terms, not PHI
    assert entry["canonical_value"] == "paracetamol"
    assert entry["surface_form"] == "paracetemol"
    assert entry["knowledge_type"] == "asr_correction"
    # No patient-identifying columns exist in extraction_knowledge
    async with db_connect() as db:
        cursor = await db.execute("PRAGMA table_info(extraction_knowledge)")
        columns = [row[1] for row in await cursor.fetchall()]
    phi_columns = {"patient_name", "patient_id", "phone", "email", "aadhaar", "abha"}
    assert phi_columns.isdisjoint(set(columns)), (
        f"extraction_knowledge must not contain PHI columns, found: {phi_columns & set(columns)}"
    )


@pytest.mark.anyio
async def test_symptom_correction_is_phi_free():
    """Symptom corrections store clinical terms, not patient data."""
    entry_id = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="symptom_synonym",
        canonical_value="fever",
        surface_form="bukhar",
        field="symptoms",
    )
    entry = await _get_entry(entry_id)
    assert entry["canonical_value"] == "fever"
    assert entry["surface_form"] == "bukhar"
    # These are vocabulary facts — structurally PHI-free


# ══════════════════════════════════════════════════════════════════════════════
# 6. Stats and knowledge retrieval
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_get_stats_empty():
    stats = await learning.get_stats()
    assert "knowledge_by_status" in stats
    assert stats["total_corrections_recorded"] == 0


@pytest.mark.anyio
async def test_load_promoted_knowledge_returns_only_promoted():
    id1 = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="paracetamol",
        surface_form="paracetemol",
        field="medications",
    )
    id2 = await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="cough",
        surface_form="khansi",
        field="symptoms",
    )
    # Promote only the first
    await learning.admin_approve(id1, admin_user_id="admin_1")

    overlay = await learning.load_promoted_knowledge()
    assert "medications" in overlay
    assert overlay["medications"]["paracetemol"] == "paracetamol"
    # The non-promoted entry should NOT appear
    assert "symptoms" not in overlay


@pytest.mark.anyio
async def test_admin_review_queue_returns_candidates():
    await learning.record_correction(
        user_id="doc_1",
        knowledge_type="asr_correction",
        canonical_value="amoxicillin",
        surface_form="amoxicilin",
        field="medications",
    )
    queue = await learning.admin_review_queue(status="candidate")
    assert len(queue) == 1
    assert queue[0]["canonical_value"] == "amoxicillin"
    assert queue[0]["status"] == "candidate"
