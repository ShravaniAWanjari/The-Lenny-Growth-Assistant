# Manual UI Test Plan

**Pass/Fail:** record `Pass` only after observing the expected result; otherwise record `Fail` and evidence. Run against the documented Compose command with a populated Ollama `llama3.2` model and a valid Gemini key for cloud-specific cases.

| ID | Action | Expected result | Pass/Fail |
| --- | --- | --- | --- |
| UI-01 | Open `http://localhost:8000`. | Hero, Local/Cloud selector, Sessions, workspace, composer, and readiness UI appear. | ☐ Pass ☐ Fail |
| UI-02 | Choose Local; ask a supported corpus question. | Request identifies Ollama; grounded response and source pills appear. | ☐ Pass ☐ Fail |
| UI-03 | Configure key, choose Cloud; ask a supported question. | Request identifies Gemini; grounded response and source pills appear. | ☐ Pass ☐ Fail |
| UI-04 | Stop Ollama; choose Local and send. | Clear Local-unavailable error appears; no silent Gemini fallback. | ☐ Pass ☐ Fail |
| UI-05 | Ask about product-market fit. | Response is based on retrieved corpus content. | ☐ Pass ☐ Fail |
| UI-06 | Open a source pill. | Link opens safely in a new tab and includes the episode timestamp. | ☐ Pass ☐ Fail |
| UI-07 | Ask a follow-up in the active session. | Response uses prior context and relevant retrieval. | ☐ Pass ☐ Fail |
| UI-08 | Create two sessions; add different prompts; switch between them. | Each history is isolated. | ☐ Pass ☐ Fail |
| UI-09 | Restart the stack; reopen a session. | Existing sessions/messages remain available from PostgreSQL volume. | ☐ Pass ☐ Fail |
| UI-10 | Ask an unrelated unsupported question. | Assistant explains corpus limitation without unsupported claim/sources. | ☐ Pass ☐ Fail |
| UI-11 | Request a Ship 30 essay from a grounded topic. | Essay-style structured result is displayed. | ☐ Pass ☐ Fail |
| UI-12 | Request a Markdown document. | Artifact card opens a Markdown modal. | ☐ Pass ☐ Fail |
| UI-13 | Download that Markdown artifact. | Browser downloads a `.md` file with artifact content. | ☐ Pass ☐ Fail |
| UI-14 | Request an HTML/CSS visual. | Artifact opens in modal iframe without script permission. | ☐ Pass ☐ Fail |
| UI-15 | Generate HTML containing an inline handler/script in sanitize mode. | UI marks it sanitized; unsafe material is absent. | ☐ Pass ☐ Fail |
| UI-16 | Inspect HTML artifact iframe. | `sandbox="allow-same-origin"` is present and no `allow-scripts` token exists. | ☐ Pass ☐ Fail |
| UI-17 | Download an accepted HTML artifact. | Browser downloads `.html`. | ☐ Pass ☐ Fail |
| UI-18 | Use reject mode and generate forbidden HTML. | Rejected state shows reason; content/download is unavailable. | ☐ Pass ☐ Fail |
| UI-19 | Test narrow mobile and tablet viewports. | Header, drawer, composer, modal, and source cards remain usable without permanent sidebar. | ☐ Pass ☐ Fail |
| UI-20 | Use keyboard only: selector, artifact card, modal Close/Escape, drawer Escape. | Controls have discernible names; Enter/Space/Escape work as documented. | ☐ Pass ☐ Fail |
| UI-21 | On a clean evaluator machine, run `docker compose -f docker-compose.prod.yml up --build`. | Stack becomes usable at `:8000`; health endpoints respond; record setup time and Ollama model pull step. | ☐ Pass ☐ Fail |

