# Forward Deployed Engineer Take-Home: Delivery Audit

Audit date: 26 August 2026.

This audit separates repository evidence from actions that require an external service or a human demonstration. It is based on `Forward_Deployed_Engineer_Take_Home_Assignment.docx` and the current working tree.

## Required repository deliverables

| Assignment requirement | Evidence in this repository | Status |
| --- | --- | --- |
| README with setup, environment, operation, testing, and troubleshooting | `README.md` | Complete |
| Product requirements document | `PRD.md` | Complete |
| Product/design document | `design.md` | Complete |
| Technical architecture document | `architecture.md` | Complete |
| Agent transcripts with redaction | `agent-transcripts/README.md` and the two redacted JSONL transcripts | Complete |
| Automated tests of critical paths | `tests/` and `docs/TEST_REPORT.md` | Complete — 78 tests passed on 26 August 2026 |
| Manual UI test plan | `tests/MANUAL_UI_TEST_PLAN.md` | Complete |
| Demo outline | `docs/DEMO_SCRIPT.md` | Complete |
| Secrets excluded from Git | `.env` is ignored; `.env.example` is provided | Complete |

The project also has a GitHub remote configured as `ShravaniAWanjari/The-Lenny-Growth-Assistant`.

## Product requirements verified in code

- FastAPI backend with chat, retrieval, session, health, and artifact routes.
- PostgreSQL-backed sessions and persisted messages.
- Transcript ingestion, validation, chunking, full-text retrieval, and per-result source metadata.
- Pi agent service with local Ollama and cloud Gemini provider paths.
- Static chat frontend with session history, source cards, and sandboxed, backend-sanitized HTML artifact previews.
- Docker production compose configuration for PostgreSQL, Ollama, Pi agent, and backend.

## Remaining evidence-dependent work

These are not missing repository files, but should be completed before submission:

1. Push the current working tree and make the GitHub repository public. Verify it from a signed-out browser session.
2. Complete the local-model demonstration: Ollama is healthy but currently has no installed model. Run `docker compose -f docker-compose.prod.yml exec ollama ollama pull llama3.2`, then verify a local response.
3. Follow `tests/MANUAL_UI_TEST_PLAN.md` and record the remaining browser-level evidence, including source inspection and artifact preview.
4. Record and upload the required 2–3 minute, camera-enabled YouTube demo. Use `docs/DEMO_SCRIPT.md`; include the local-model demonstration and one technical trade-off.
5. Submit the public repository and YouTube link through the assignment form.

## Implementation risks to mention or address

- Application logging currently uses console/print output rather than a structured logging format. It provides basic operational output but does not fully meet a strict interpretation of the observability requirement.
- The production Docker stack was rebuilt and exercised on 26 August 2026. The remaining runtime gap is local inference: the Ollama server is healthy but no model has finished downloading.
- The assignment calls for graceful failure behavior. The Pi-agent connection path has timeout/error handling, but a live walkthrough should deliberately demonstrate the missing-key, unavailable-Ollama, and empty-retrieval states.

## Submission decision

All file-based deliverables requested by the assignment are now present. The remaining work is publication and live demonstration evidence, not documentation creation.
