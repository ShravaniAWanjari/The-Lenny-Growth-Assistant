import sys
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ingestion.normalizer import (
    parse_timestamp_to_seconds,
    seconds_to_timestamp_str,
    parse_speaker_turns,
    chunk_speaker_turns,
)


def test_parse_timestamp_to_seconds():
    assert parse_timestamp_to_seconds("00:00:00") == 0
    assert parse_timestamp_to_seconds("00:01:30") == 90
    assert parse_timestamp_to_seconds("01:05:46") == 3946
    assert parse_timestamp_to_seconds("05:20") == 320


def test_seconds_to_timestamp_str():
    assert seconds_to_timestamp_str(0) == "00:00:00"
    assert seconds_to_timestamp_str(90) == "00:01:30"
    assert seconds_to_timestamp_str(3946) == "01:05:46"


def test_parse_speaker_turns():
    body = """
Lenny (00:00:00):
Welcome to the show. Today we discuss growth.

Andy Johns (00:00:15):
Thanks Lenny. Growth is all about loops.
"""
    turns = parse_speaker_turns(body)
    assert len(turns) == 2
    assert turns[0]["speaker"] == "Lenny"
    assert turns[0]["seconds"] == 0
    assert "growth" in turns[0]["text"].lower()

    assert turns[1]["speaker"] == "Andy Johns"
    assert turns[1]["seconds"] == 15
    assert "loops" in turns[1]["text"].lower()


def test_chunk_speaker_turns_metadata_preservation():
    turns = [
        {
            "speaker": "Lenny",
            "timestamp_str": "00:00:00",
            "seconds": 0,
            "text": "What is product market fit?",
        },
        {
            "speaker": "Guest",
            "timestamp_str": "00:00:30",
            "seconds": 30,
            "text": "Product market fit is when customers pull the product from you.",
        },
    ]
    meta = {
        "guest": "Test Guest",
        "title": "Finding PMF",
        "video_id": "xyz123",
        "youtube_url": "https://www.youtube.com/watch?v=xyz123",
        "publish_date": "2023-05-10",
        "keywords": ["pmf", "growth"],
    }
    chunks = chunk_speaker_turns(turns, "ep_test", "test", meta, max_words_per_chunk=500)
    assert len(chunks) == 1
    c = chunks[0]
    assert c["chunk_id"] == "chunk_test_0000"
    assert c["guest"] == "Test Guest"
    assert c["timestamp_start"] == "00:00:00"
    assert c["timestamp_end"] == "00:00:30"
    assert c["start_seconds"] == 0
    assert "t=0" in c["youtube_url"]
    assert "pmf" in c["keywords"]
