import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock, Mock
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

client = TestClient(app)


def make_mock_response(data: dict, status_code: int = 200):
    mock_resp = Mock()
    mock_resp.status_code = status_code
    mock_resp.json = Mock(return_value=data)
    mock_resp.text = str(data)
    return mock_resp


def test_chat_invalid_provider():
    response = client.post(
        "/chat",
        json={"prompt": "Hello", "provider": "unsupported_provider"},
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid provider 'unsupported_provider'" in data["detail"]


def test_chat_gemini_provider():
    mock_resp = make_mock_response({
        "status": "ok",
        "response": "Hello from Gemini.",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [],
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        response = client.post(
            "/chat",
            json={"prompt": "Say hello in one word", "provider": "gemini"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["provider"] == "gemini"
        assert len(data["response"]) > 0


def test_chat_ollama_provider():
    # If Ollama is offline, Pi Agent / FastAPI returns 500/503 or handled error
    response = client.post(
        "/chat",
        json={"prompt": "Say hello in one word", "provider": "ollama"},
    )
    # Status code is either 200 (if Ollama is running) or 500/503 (if Ollama daemon not running)
    assert response.status_code in [200, 500, 503]
    data = response.json()
    if response.status_code == 200:
        assert data["provider"] == "ollama"
    else:
        assert "error" in data or "detail" in data
