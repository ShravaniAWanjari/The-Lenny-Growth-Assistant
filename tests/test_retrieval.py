import sys
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.retrieval import search


def test_retrieval_empty_query():
    results = search("")
    assert results == []


def test_retrieval_guest_specific():
    results = search("Andy Johns burnout", top_k=5)
    assert len(results) > 0
    # Andy Johns should be in top results
    assert any("Andy Johns" in r["guest"] for r in results)
    top = results[0]
    assert "chunk_id" in top
    assert "text" in top
    assert "source_url" in top
    assert "timestamp" in top
    assert top["relevance_score"] > 0.0


def test_retrieval_topic_pmf():
    results = search("product market fit", top_k=5)
    assert len(results) > 0
    top = results[0]
    assert top["relevance_score"] > 0.0
    assert "https://www.youtube.com/watch?v=" in top["source_url"]


def test_retrieval_unsupported_query():
    results = search("Explain quantum computing algorithms in Hilbert space", top_k=5)
    # Unsupported query should return 0 results or near-zero scores
    assert len(results) == 0 or all(r["relevance_score"] < 0.1 for r in results)


def test_retrieval_meta_only_prompt_constructs_a_valid_tsquery():
    # Artifact-oriented prompts can contain only stopwords. They must not cause
    # PostgreSQL `to_tsquery` syntax errors before the Pi Agent is reached.
    results = search("Create a visual", top_k=5)
    assert isinstance(results, list)
