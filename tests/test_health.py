import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "lenny-growth-assistant",
    }


def test_database_health():
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "postgresql",
    }
