"""Backfill _extracted_facts into memory_state for demo sessions."""
import asyncio, json, os
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

async def run():
    import asyncpg
    db_url = os.environ["DATABASE_URL"]
    conn = await asyncpg.connect(db_url)

    from app.services.provenance import build_extracted_facts
    from app.services.memory_context import MemoryContextService
    memory = MemoryContextService()

    rows = await conn.fetch(
        "SELECT id, transcript, clinical_facts, memory_state FROM sessions "
        "WHERE user_id=(SELECT id::text FROM users WHERE username='lipi_demo')"
    )

    for row in rows:
        sid = row["id"]
        transcript = row["transcript"] or ""
        cf = row["clinical_facts"]
        facts = json.loads(cf) if isinstance(cf, str) else (cf or {})

        extracted = build_extracted_facts(transcript, facts)
        extracted_dicts = [
            e.model_dump() if hasattr(e, "model_dump") else dict(e)
            for e in extracted
        ]

        full_state = memory.resolve_memory([facts])
        state_with_provenance = {**full_state, "_extracted_facts": extracted_dicts}

        await conn.execute(
            "UPDATE sessions SET memory_state=$1 WHERE id=$2",
            json.dumps(state_with_provenance),
            sid,
        )
        print(f"  {sid[:8]}... → {len(extracted_dicts)} extracted facts")

    await conn.close()
    print("Done.")

asyncio.run(run())
