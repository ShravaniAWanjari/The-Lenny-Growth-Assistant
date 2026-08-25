Absolutely. For the **final automated test suite**, I'd organize it by functionality rather than just by phase.

### Automated Tests

| #         | Area                              | Tests                                                                                                                                                                                                                  |
| --------- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1–4**   | **Health / Infrastructure**       | FastAPI health, PostgreSQL health, Pi health, production configuration                                                                                                                                                 |
| **5–7**   | **Chat / API**                    | Valid chat request, invalid provider, Pi unavailable/error handling                                                                                                                                                    |
| **8–13**  | **Knowledge Base / Validation**   | Episode validation, frontmatter validation, missing transcript detection, topic-index validation, excluded files, source integrity                                                                                     |
| **14–17** | **Chunking**                      | Speaker-turn parsing, timestamp extraction, timestamp → seconds, chunk/source metadata preservation                                                                                                                    |
| **18–21** | **Retrieval**                     | FTS retrieval, topic boosting, guest boosting, retrieval ranking / Hit@5                                                                                                                                               |
| **22–27** | **RAG / Grounding**               | Relevant evidence accepted, irrelevant evidence rejected, grounded response, source metadata, unsupported-question refusal, prompt-injection resistance                                                                |
| **28–38** | **Sessions / Persistence**        | Create session, retrieve session, retrieve messages, message ordering, auto-create session, message persistence, conversation history, follow-up context, session isolation, metadata persistence, restart persistence |
| **39–49** | **Skills / Structured Content**   | Ship 30 skill detection, Ship 30 structure, structured summary, takeaways, comparison table, Markdown artifact generation, Markdown metadata, HTML artifact generation, skill grounding, unsupported skill request     |
| **50–58** | **HTML Security**                 | Safe HTML preservation, `<script>` removal, `onclick` removal, `onerror` removal, `javascript:` removal, iframe removal, object/embed removal, dangerous CSS removal, safe CSS preservation                            |
| **59–61** | **Artifact Security / Rendering** | Sanitization status, reject-mode fallback, transcript-injection safety                                                                                                                                                 |
| **62–65** | **Frontend / Artifact UI**        | Frontend loads, chat interaction, artifact modal, artifact download                                                                                                                                                    |
| **66–69** | **Production**                    | Docker Compose validity, production health checks, production startup/configuration, database initialization/idempotency                                                                                               |

### The critical tests I'd make sure are actually present

These are the ones an evaluator is most likely to care about:

```text
RAG
✓ relevant question → grounded answer
✓ irrelevant question → refusal
✓ sources → correct guest + timestamp
✓ transcript injection → cannot override instructions

LLM
✓ Local → Ollama
✓ Cloud → Gemini
✓ invalid provider → clean error
✓ provider unavailable → clean failure

Sessions
✓ create session
✓ persist messages
✓ follow-up understands previous turn
✓ Session A cannot access Session B

Artifacts
✓ Markdown generated
✓ HTML generated
✓ artifact opens
✓ artifact downloads
✓ safe HTML preserved
✓ malicious HTML sanitized
✓ reject mode works
✓ transcript injection cannot become executable HTML

Production
✓ PostgreSQL initializes
✓ existing sessions survive initialization
✓ production Docker starts
✓ health checks pass
✓ complete system works after clean restart
```

### One correction to our previous “69 tests”

Don't force the final suite to be exactly **69**.

The important thing is that **every critical requirement has an automated test**. If the agent discovers that something important isn't actually covered, adding tests and ending up at 72 or 75 is better than preserving “69” for the sake of the number.

For the assignment, the strongest final statement is:

> **All critical API, retrieval, routing, persistence, security, artifact, and production-path behaviors are covered by automated tests, with the complete suite passing.**
