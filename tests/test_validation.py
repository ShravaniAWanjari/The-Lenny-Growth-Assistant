import sys
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ingestion.validator import (
    validate_frontmatter,
    validate_transcript_body,
    run_validation,
)


def test_validate_frontmatter_valid():
    valid_fm = {
        "guest": "Test Guest",
        "title": "Test Title",
        "youtube_url": "https://www.youtube.com/watch?v=123",
        "video_id": "123",
        "publish_date": "2023-01-01",
        "description": "Test description",
        "duration": "1:00:00",
        "duration_seconds": 3600.0,
        "view_count": 1000,
        "channel": "Lenny's Podcast",
        "keywords": ["growth", "product"],
    }
    is_valid, errors = validate_frontmatter(valid_fm, "dummy/path.md")
    assert is_valid is True
    assert len(errors) == 0


def test_validate_frontmatter_missing_fields():
    invalid_fm = {
        "guest": "Test Guest",
        "title": "Test Title",
    }
    is_valid, errors = validate_frontmatter(invalid_fm, "dummy/path.md")
    assert is_valid is False
    assert any("youtube_url" in e for e in errors)
    assert any("publish_date" in e for e in errors)


def test_validate_frontmatter_invalid_types():
    invalid_fm = {
        "guest": "Test Guest",
        "title": "Test Title",
        "youtube_url": "https://www.youtube.com/watch?v=123",
        "video_id": "123",
        "publish_date": 12345,
        "description": "Test",
        "duration": "1:00:00",
        "duration_seconds": "not_a_number",
        "view_count": -5,
        "channel": "Lenny's Podcast",
        "keywords": "not_a_list",
    }
    is_valid, errors = validate_frontmatter(invalid_fm, "dummy/path.md")
    assert is_valid is False
    assert any("duration_seconds" in e for e in errors)
    assert any("view_count" in e for e in errors)
    assert any("keywords" in e for e in errors)


def test_validate_transcript_body_valid():
    body = """
## Transcript

Lenny (00:00:00):
Welcome to the show.

Guest (00:00:15):
Thank you for having me.
"""
    is_valid, errors = validate_transcript_body(body, "dummy/path.md")
    assert is_valid is True
    assert len(errors) == 0


def test_validate_transcript_body_empty():
    is_valid, errors = validate_transcript_body("   ", "dummy/path.md")
    assert is_valid is False
    assert "empty" in errors[0].lower()


def test_validate_transcript_body_no_timestamps():
    body = "Just plain text with no speaker turns."
    is_valid, errors = validate_transcript_body(body, "dummy/path.md")
    assert is_valid is False
    assert any("timestamp" in e.lower() for e in errors)
