import sys
from pathlib import Path
import pytest
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


# -----------------------------------------------------------------------------
# 1. Frontend Asset & HTML Serving Tests
# -----------------------------------------------------------------------------

def test_frontend_root_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Lenny Growth Assistant" in response.text
    assert "Explore the ideas, experiences, and lessons" in response.text


def test_frontend_hero_and_controls_present():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    # Hero Section
    assert 'class="hero-section"' in html or 'id="hero"' in html
    assert 'id="providerSlider"' in html
    assert 'data-provider="ollama"' in html
    assert 'data-provider="gemini"' in html
    assert 'id="sessionsToggleBtn"' in html
    # Conversation Workspace
    assert 'id="conversation"' in html
    assert 'id="promptInput"' in html
    assert 'id="sendBtn"' in html
    # Sandboxed Modal
    assert 'id="artifactModal"' in html
    assert 'sandbox="allow-same-origin"' in html


def test_frontend_static_assets_accessible():
    # CSS
    css_res = client.get("/static/css/style.css")
    assert css_res.status_code == 200
    assert "--bg-core:" in css_res.text

    # JS
    js_res = client.get("/static/js/app.js")
    assert js_res.status_code == 200
    assert "handleSendMessage" in js_res.text

    # Hero asset
    hero_res = client.get("/static/assets/hero.jpg")
    assert hero_res.status_code == 200

    # Vendor marked
    marked_res = client.get("/static/vendor/marked.min.js")
    assert marked_res.status_code == 200


# -----------------------------------------------------------------------------
# 2. Session Drawer & Navigation Endpoints
# -----------------------------------------------------------------------------

def test_sessions_list_endpoint_returns_chronological_list():
    res = client.get("/sessions")
    assert res.status_code == 200
    sessions = res.json()
    assert isinstance(sessions, list)
    if len(sessions) > 0:
        s0 = sessions[0]
        assert "session_id" in s0
        assert "created_at" in s0
        assert "message_count" in s0


def test_session_create_and_fetch_messages():
    # Create new session
    create_res = client.post("/sessions", json={"metadata": {"title": "Frontend Test Session"}})
    assert create_res.status_code == 201
    s_data = create_res.json()
    session_id = s_data["session_id"]

    # Fetch messages
    msg_res = client.get(f"/sessions/{session_id}/messages")
    assert msg_res.status_code == 200
    assert msg_res.json() == []

    # Rename session
    patch_res = client.patch(f"/sessions/{session_id}", json={"title": "Updated Session Title"})
    assert patch_res.status_code == 200
    assert patch_res.json()["metadata"]["title"] == "Updated Session Title"

    # Delete session
    del_res = client.delete(f"/sessions/{session_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "ok"



# -----------------------------------------------------------------------------
# 3. Provider Switching (Gemini / Ollama) Integration Tests
# -----------------------------------------------------------------------------

def test_chat_with_gemini_provider_flag():
    mock_resp = make_mock_response({
        "status": "ok",
        "response": "Answer from Gemini Cloud.",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [
            {
                "guest": "Rahul Vohra",
                "episode": "How Superhuman Built An Engine | Rahul Vohra",
                "speaker": "Rahul Vohra",
                "timestamp": "00:04:12",
                "source_url": "https://www.youtube.com/watch?v=0igjSRZyX-w&t=252",
                "score": 0.95,
            }
        ],
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
        response = client.post(
            "/chat",
            json={"prompt": "How to find PMF?", "provider": "gemini"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "gemini"
        assert data["model"] == "gemini-2.5-flash"
        assert len(data["sources"]) == 1
        assert "t=252" in data["sources"][0]["source_url"]

        # Verify provider in payload sent to Pi
        call_args = mock_post.call_args[1]["json"]
        assert call_args["provider"] == "gemini"


def test_chat_with_ollama_provider_flag():
    mock_resp = make_mock_response({
        "status": "ok",
        "response": "Answer from Local Ollama.",
        "provider": "ollama",
        "model": "llama3.2",
        "sources": [],
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
        response = client.post(
            "/chat",
            json={"prompt": "What is an MVP?", "provider": "ollama"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "ollama"

        call_args = mock_post.call_args[1]["json"]
        assert call_args["provider"] == "ollama"


# -----------------------------------------------------------------------------
# 4. Artifact Rendering & Modal Data Flow
# -----------------------------------------------------------------------------

def test_chat_returns_sanitized_html_artifact_for_modal():
    unsafe_html = "<div class='card' onclick='steal()'><h3>PMF Signals</h3><p>Safe content</p></div>"
    mock_resp = make_mock_response({
        "status": "ok",
        "response": "Here is the visual card.",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [],
        "skill_invoked": "artifact-html",
        "artifact": {
            "type": "html",
            "title": "PMF Signals Card",
            "content": unsafe_html,
        },
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        response = client.post(
            "/chat",
            json={"prompt": "Turn this into a visual HTML card.", "provider": "gemini"},
        )
        assert response.status_code == 200
        data = response.json()
        art = data["artifact"]
        assert art is not None
        assert art["type"] == "html"
        assert art["title"] == "PMF Signals Card"
        assert art["validation_status"] in ["valid", "sanitized"]
        assert art["original_modified"] is True
        assert "onclick" not in art["content"]
        assert "Safe content" in art["content"]


def test_chat_returns_markdown_artifact_for_modal():
    mock_resp = make_mock_response({
        "status": "ok",
        "response": "Here is the Markdown document.",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [],
        "skill_invoked": "artifact-markdown",
        "artifact": {
            "type": "markdown",
            "title": "Burnout Guide",
            "content": "# Burnout Guide\n\n## Andy Johns Advice\n- Take sabbaticals.",
        },
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        response = client.post(
            "/chat",
            json={"prompt": "Create a Markdown document on burnout.", "provider": "gemini"},
        )
        assert response.status_code == 200
        data = response.json()
        art = data["artifact"]
        assert art is not None
        assert art["type"] == "markdown"
        assert art["validation_status"] == "valid"
        assert "# Burnout Guide" in art["content"]


def test_rejected_artifact_has_clean_error_state():
    mock_resp = make_mock_response({
        "status": "ok",
        "response": "Response text",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [],
        "skill_invoked": "artifact-html",
        "artifact": {
            "type": "html",
            "title": "Unsafe Artifact",
            "content": "<script>evil()</script>",
        },
    })

    # In reject mode, sanitize_and_validate_html marks it rejected
    with patch("app.main.settings.artifact_sanitization_mode", "reject"):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
            response = client.post(
                "/chat",
                json={"prompt": "Create a visual", "provider": "gemini"},
            )
            assert response.status_code == 200
            data = response.json()
            art = data["artifact"]
            assert art["validation_status"] == "rejected"
            assert art["content"] == ""
            assert art["validation_error"] is not None
