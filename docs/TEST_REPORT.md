# Automated Test Audit

**Audit date:** 25 August 2026
**Current execution result:** 78 passed on 26 August 2026.

The repository contains **78 pytest test functions** (`rg '^def test_' tests`), covering:

- ingestion validation and chunking;
- PostgreSQL retrieval/RAG behavior and refusal boundaries;
- session creation, persistence, and isolation;
- Pi Agent chat integration/provider routing;
- skills, Markdown/HTML artifact handling, and HTML sanitization/rejection;
- frontend asset/UI contract checks; and
- health endpoints and production Compose configuration.

Final-coverage additions include Pi Agent unavailable/error handling, evidence forwarding, transcript-injection request handling, missing-transcript/excluded-file/topic-link validation, source metadata/commit preservation, public asset routing, artifact download/sandbox contract checks, and invalid `to_tsquery` prompt coverage.

## Attempted command

```bash
backend/.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider
```

The complete suite was run in four groups to avoid a shell execution time limit. Results were: 28 passed, 15 passed, 18 passed, and 17 passed, for **78 passed** with no failures. The run emitted dependency deprecation warnings from FastAPI/Starlette and Python datetime APIs, but no test failures.

The companion manual verification coverage is in [tests/MANUAL_UI_TEST_PLAN.md](../tests/MANUAL_UI_TEST_PLAN.md).
