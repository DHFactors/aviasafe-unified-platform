import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_reports():
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return [
        {
            "id": "r1",
            "tenant_id": "airline1",
            "report_type": "voluntary",
            "status": "NEW",
            "ai_status": "PENDING",
            "narrative": "Test report 1",
            "location": "KTM",
            "occurrence_date": now,
            "created_by": "user1",
            "created_at": now,
            "updated_at": now,
            "is_anonymous": True,
            "severity": "Low",
        },
        {
            "id": "r2",
            "tenant_id": "airline1",
            "report_type": "mandatory",
            "status": "COMPLETED",
            "ai_status": "COMPLETED",
            "narrative": "Test report 2",
            "location": "KTM",
            "occurrence_date": now,
            "created_by": "user2",
            "created_at": now,
            "updated_at": now,
            "is_anonymous": False,
            "severity": "High",
            "occurrence_type": "Bird Strike",
            "corrective_actions": [{"status": "OPEN"}],
            "investigation_status": "INVESTIGATING",
        },
    ]
