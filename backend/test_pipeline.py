import asyncio
from app.storage.db import init_db
from app.storage.repository import SessionRepository
from app.schemas.consultation import StatusEnum

async def run_test():
    await init_db()
    
    repo = SessionRepository()
    session = await repo.create_session("test_user_id", patient_name="John Doe", doctor_name="Test Doc")
    session.transcript = "The patient has a fever and bukhar. Also a headache and nausea. Prescribed paracetamol 500 mg twice daily. BP is 150/90. Allergic to penicillin."
    session.status = StatusEnum.transcribed
    await repo.update_session(session)
    
    from fastapi.testclient import TestClient
    from app.main import app
    
    # FastApi test client manages lifespan context
    with TestClient(app) as client:
        # Override auth for test client
        from app.api.routes_auth import get_current_user
        app.dependency_overrides[get_current_user] = lambda: {"id": "test_user_id", "username": "test_user"}
        response = client.post(f"/api/sessions/{session.id}/process-clinical")
        print(f"Status Code: {response.status_code}")
        import json
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(response.text)
        app.dependency_overrides.clear()

if __name__ == "__main__":
    asyncio.run(run_test())
