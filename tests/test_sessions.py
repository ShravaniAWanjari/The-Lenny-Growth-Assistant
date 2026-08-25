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
# 1. Session Lifecycle Tests
# -----------------------------------------------------------------------------

def test_create_session():
    response = client.post("/sessions", json={"metadata": {"tags": ["pmf", "startup"]}})
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["session_id"].startswith("session_")
    assert "created_at" in data
    assert data["message_count"] == 0
    assert data["metadata"] == {"tags": ["pmf", "startup"]}


def test_get_session():
    # Create session
    create_res = client.post("/sessions", json={"metadata": {"title": "Test Session"}})
    assert create_res.status_code == 201
    sid = create_res.json()["session_id"]

    # Get session
    get_res = client.get(f"/sessions/{sid}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["session_id"] == sid
    assert data["message_count"] == 0
    assert data["metadata"]["title"] == "Test Session"


def test_get_unknown_session_returns_404():
    response = client.get("/sessions/session_non_existent_999999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_get_empty_session_messages():
    create_res = client.post("/sessions", json={})
    sid = create_res.json()["session_id"]

    response = client.get(f"/sessions/{sid}/messages")
    assert response.status_code == 200
    assert response.json() == []


def test_get_messages_unknown_session_returns_404():
    response = client.get("/sessions/session_invalid_abc/messages")
    assert response.status_code == 404


# -----------------------------------------------------------------------------
# 2. Chat with Sessions & Message Persistence
# -----------------------------------------------------------------------------

def test_chat_with_valid_session_persists_messages():
    create_res = client.post("/sessions", json={"metadata": {"topic": "MVPs"}})
    sid = create_res.json()["session_id"]

    mock_resp = make_mock_response({
        "status": "ok",
        "response": "Lenny and Eric Ries discuss MVPs extensively in the Lean Startup reflections episode.",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [
            {
                "guest": "Eric Ries",
                "episode": "Reflections on a movement | Eric Ries",
                "speaker": "Eric Ries",
                "timestamp": "00:19:41",
                "source_url": "https://www.youtube.com/watch?v=xzebbzIntFc&t=1181",
                "score": 0.85,
            }
        ],
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        chat_res = client.post(
            "/chat",
            json={"session_id": sid, "prompt": "What does Lenny say about MVPs?", "provider": "gemini"},
        )
        assert chat_res.status_code == 200
        chat_data = chat_res.json()
        assert chat_data["session_id"] == sid
        assert len(chat_data["response"]) > 0
        assert len(chat_data["sources"]) > 0

    # Retrieve messages and verify chronological order & metadata
    msgs_res = client.get(f"/sessions/{sid}/messages")
    assert msgs_res.status_code == 200
    msgs = msgs_res.json()
    assert len(msgs) == 2

    # User message
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "What does Lenny say about MVPs?"
    assert msgs[0]["session_id"] == sid

    # Assistant message
    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["content"] == chat_data["response"]
    assert msgs[1]["session_id"] == sid
    assert msgs[1]["metadata"]["provider"] == "gemini"
    assert len(msgs[1]["metadata"]["sources"]) > 0

    # Verify session metadata updated message_count
    session_meta = client.get(f"/sessions/{sid}").json()
    assert session_meta["message_count"] == 2


def test_chat_with_unknown_session_returns_404():
    response = client.post(
        "/chat",
        json={"session_id": "session_non_existent_12345", "prompt": "Hello", "provider": "gemini"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_chat_auto_generates_session_when_omitted():
    mock_resp = make_mock_response({
        "status": "ok",
        "response": "Here is information on MVPs.",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [],
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        response = client.post(
            "/chat",
            json={"prompt": "What does Lenny say about MVPs?", "provider": "gemini"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"].startswith("session_")

        msgs = client.get(f"/sessions/{data['session_id']}/messages").json()
        assert len(msgs) == 2


def test_chat_empty_prompt_returns_400():
    response = client.post(
        "/chat",
        json={"prompt": "   ", "provider": "gemini"},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 3. Conversational Context & Multi-turn Continuity
# -----------------------------------------------------------------------------

def test_multiturn_conversational_context():
    create_res = client.post("/sessions", json={})
    sid = create_res.json()["session_id"]

    mock_resp_1 = make_mock_response({
        "status": "ok",
        "response": "Andy Johns discussed burnout in tech in his episode 'When enough is enough'.",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [],
    })

    mock_resp_2 = make_mock_response({
        "status": "ok",
        "response": "Andy Johns estimated that 50% to 60% of tech workers with 5-7 years experience face distress.",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [],
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=[mock_resp_1, mock_resp_2]) as mock_post:
        # Turn 1
        t1_res = client.post(
            "/chat",
            json={"session_id": sid, "prompt": "What does Andy Johns say about burnout?", "provider": "gemini"},
        )
        assert t1_res.status_code == 200
        assert "Andy Johns" in t1_res.json()["response"]

        # Turn 2: Follow-up question
        t2_res = client.post(
            "/chat",
            json={
                "session_id": sid,
                "prompt": "What percentage of tech employees did he estimate were affected?",
                "provider": "gemini",
            },
        )
        assert t2_res.status_code == 200
        assert "50%" in t2_res.json()["response"]

        # Verify that Turn 2 call forwarded Turn 1 conversation history to Pi Agent
        second_call_payload = mock_post.call_args_list[1][1]["json"]
        assert "conversationHistory" in second_call_payload
        history = second_call_payload["conversationHistory"]
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "What does Andy Johns say about burnout?"
        assert history[1]["role"] == "assistant"

    # Verify all 4 messages in history
    msgs = client.get(f"/sessions/{sid}/messages").json()
    assert len(msgs) == 4
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"
    assert msgs[2]["role"] == "user"
    assert msgs[3]["role"] == "assistant"


# -----------------------------------------------------------------------------
# 4. Strict Session Isolation
# -----------------------------------------------------------------------------

def test_session_isolation():
    sA = client.post("/sessions", json={"metadata": {"title": "Burnout Session"}}).json()["session_id"]
    sB = client.post("/sessions", json={"metadata": {"title": "MVP Session"}}).json()["session_id"]

    mock_resp_A = make_mock_response({
        "status": "ok",
        "response": "Andy Johns discussed tech burnout.",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [],
    })

    mock_resp_B = make_mock_response({
        "status": "ok",
        "response": "Lenny discusses MVPs and startup validation.",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [],
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=[mock_resp_A, mock_resp_B]):
        client.post(
            "/chat",
            json={"session_id": sA, "prompt": "What does Andy Johns say about burnout?", "provider": "gemini"},
        )
        client.post(
            "/chat",
            json={"session_id": sB, "prompt": "What does Lenny say about MVPs?", "provider": "gemini"},
        )

    msgs_A = client.get(f"/sessions/{sA}/messages").json()
    msgs_B = client.get(f"/sessions/{sB}/messages").json()

    assert len(msgs_A) == 2
    assert len(msgs_B) == 2

    # Verify Session A contains Andy Johns and not MVPs
    assert any("Andy Johns" in m["content"] for m in msgs_A)
    assert not any("Eric Ries" in m["content"] for m in msgs_A)

    # Verify Session B contains MVPs and not Andy Johns
    assert any("MVP" in m["content"] for m in msgs_B)
    assert not any("Andy Johns" in m["content"] for m in msgs_B)


def test_update_session_title_and_metadata():
    res = client.post("/sessions", json={"metadata": {"title": "Original Title"}}).json()
    sid = res["session_id"]

    patch_res = client.patch(f"/sessions/{sid}", json={"title": "Renamed Title", "metadata": {"custom_tag": "product"}})
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["session_id"] == sid
    assert updated["metadata"]["title"] == "Renamed Title"
    assert updated["metadata"]["custom_tag"] == "product"

    # Verify persistent in GET /sessions/{sid}
    get_res = client.get(f"/sessions/{sid}")
    assert get_res.status_code == 200
    assert get_res.json()["metadata"]["title"] == "Renamed Title"


def test_update_unknown_session_returns_404():
    res = client.patch("/sessions/session_non_existent", json={"title": "New Title"})
    assert res.status_code == 404


def test_delete_session_and_cascaded_messages():
    sid = client.post("/sessions", json={"metadata": {"title": "To Delete"}}).json()["session_id"]

    mock_resp = make_mock_response({
        "status": "ok",
        "response": "Some message content",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [],
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        client.post("/chat", json={"session_id": sid, "prompt": "Hello to be deleted", "provider": "gemini"})

    # Ensure messages exist
    msgs_before = client.get(f"/sessions/{sid}/messages").json()
    assert len(msgs_before) == 2

    # Delete session
    del_res = client.delete(f"/sessions/{sid}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "ok"
    assert del_res.json()["deleted_session_id"] == sid

    # Verify session is gone
    get_res = client.get(f"/sessions/{sid}")
    assert get_res.status_code == 404

    # Verify messages endpoint returns 404
    msg_res = client.get(f"/sessions/{sid}/messages")
    assert msg_res.status_code == 404


def test_delete_unknown_session_returns_404():
    res = client.delete("/sessions/session_non_existent")
    assert res.status_code == 404

