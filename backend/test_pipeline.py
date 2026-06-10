import asyncio
from app.storage.db import init_db
from app.storage.repository import SessionRepository
from app.schemas.consultation import StatusEnum

async def test():
    await init_db()
    
    repo = SessionRepository()
    session = await repo.create_session(patient_name="John Doe", doctor_name="Test Doc")
    session.transcript = "The patient has a fever and bukhar. Also a headache and nausea. Prescribed paracetamol 500 mg twice daily. BP is 150/90. Allergic to penicillin."
    session.status = StatusEnum.transcribed
    await repo.update_session(session)
    
    from fastapi.testclient import TestClient
    from app.main import app
    
    # FastApi test client manages lifespan context
    with TestClient(app) as client:
        response = client.post(f"/sessions/{session.id}/process-clinical")
        print(f"Status Code: {response.status_code}")
        import json
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(response.text)

if __name__ == "__main__":
    asyncio.run(test())
