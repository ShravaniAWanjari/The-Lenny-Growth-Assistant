# The Lenny Growth Assistant

A local-first, grounded assistant for exploring the supplied Lenny's Podcast transcripts. It retrieves passages from PostgreSQL, sends retrieved context and session history to a Pi Agent, and generates with either Ollama (Local) or Gemini (Cloud).

## Product overview and problem

Product managers, growth practitioners, founders, and evaluators can ask for product/growth guidance without manually searching the transcript corpus. The app returns source links/timestamps, preserves isolated sessions, creates Ship 30-style writing and Markdown/HTML artifacts, and refuses unsupported corpus questions rather than presenting them as grounded.

## Architecture overview

`Browser → FastAPI → PostgreSQL FTS` retrieves transcript chunks. `FastAPI → Pi Agent → Ollama/Gemini` generates the response. FastAPI serves the static frontend, validates HTML artifacts, and persists sessions/messages. Full details: [architecture.md](architecture.md).

## Prerequisites

- Docker Desktop with Compose, Python 3.12+, Node.js 20+, and PostgreSQL 16.
- Ollama for Local mode. The required local model is `llama3.2` (the configured default; `llama3.2:latest` also works).
- A Gemini API key only for Cloud mode.

## Install and configure

Copy `.env.example` to `.env`, then replace its placeholders. `.env` is ignored by Git.

| Variable                             | Purpose                                                   |
| ------------------------------------ | --------------------------------------------------------- |
| `POSTGRES_PASSWORD` / `DATABASE_URL` | PostgreSQL credentials/connection.                        |
| `GEMINI_API_KEY`                     | Required for Cloud provider.                              |
| `LLM_PROVIDER`                       | Default `ollama` or `gemini`; the UI begins on Local.     |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL`    | Local endpoint/model; model is `llama3.2`.                |
| `PI_AGENT_URL`, `PI_AGENT_PORT`      | Pi Agent connection.                                      |
| `ARTIFACT_SANITIZATION_MODE`         | `sanitize` or `reject`.                                   |
| `ALLOWED_ORIGINS`                    | Comma-separated CORS origins or `*` for local evaluation. |

### PostgreSQL

Production Compose creates PostgreSQL 16 with the `lenny_prod_pgdata` named volume. When the database is empty, the backend loads `data/processed/episodes.json`, `chunks.json`, and `topics.json`, then builds FTS vectors and a GIN index.

### Gemini / Cloud

Set `GEMINI_API_KEY` in `.env`, start the stack, then select **Cloud**. A missing/invalid key is surfaced as an error; the app does not silently fall back to Local.

### Ollama / Local

Compose provisions Ollama and automatically pulls `OLLAMA_MODEL` (default: `llama3.2`) on the first startup. The model is retained in the named Docker volume, so later startups do not download it again. The first run needs network access and may take several minutes; the Pi Agent and backend wait until the pull succeeds. Local provider failure does not silently fall back to Cloud.

## Start

### One-command production startup

```bash
docker compose -f docker-compose.prod.yml up --build
```

Open <http://localhost:8000>. Use <http://localhost:8000/health>, <http://localhost:8000/status>, and <http://localhost:8000/health/db> for diagnostics.

### Development startup

Start PostgreSQL: `docker compose up -d postgres`.

In one terminal:

```bash
cd agent
npm install
npm run build
npm start
```

In another terminal, create/activate a Python virtual environment, install `backend/requirements.txt`, then run from the repository root:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend --reload
```

## Use

- Select **Local** or **Cloud**.
- Ask a product/growth question; source pills open timestamps in a new tab.
- Follow up in the same session; the backend passes its latest eight messages plus relevant retrieval context.
- Use **Sessions** to create, select, rename, or delete isolated conversations.
- Ask for a Ship 30 essay to invoke the `agent/skills/ship30` skill.
- Request Markdown or an HTML/CSS visual. Choose **View Artifact** to use the modal and download `.md`/`.html`.

## RAG and artifacts

Retrieval uses PostgreSQL FTS plus topic/guest boosting and a relevance threshold. Sources include guest, episode, speaker, timestamp, and YouTube URL. The agent uses only retrieved context and session history for domain answers.

Generated HTML is untrusted: FastAPI applies an `nh3` allowlist and safe URL schemes, either sanitizing or rejecting unsafe content. Accepted HTML renders only in `iframe sandbox="allow-same-origin"` with no `allow-scripts`; the modal reports valid/sanitized/rejected state. Markdown is displayed by the frontend's vendored Markdown renderer and is not an HTML security boundary.

## Testing

Run:

```bash
python -m pytest tests -v
```

There are 78 pytest tests covering API, retrieval/routing, persistence/sessions, artifact security, frontend contracts, and production configuration. The suite passed on 26 August 2026 using `backend/.venv`. See [docs/TEST_REPORT.md](docs/TEST_REPORT.md) and [tests/MANUAL_UI_TEST_PLAN.md](tests/MANUAL_UI_TEST_PLAN.md).

## Troubleshooting

- **“Setting up” persists:** inspect `docker compose -f docker-compose.prod.yml logs`; Postgres, Pi Agent, and Ollama health must become reachable.
- **Local unavailable:** confirm Ollama is running and `ollama list` contains `llama3.2`.
- **Cloud unavailable:** verify `GEMINI_API_KEY` and outbound network access.
- **Database health fails:** check Postgres health and the database URL/credentials.
- **Artifact blocked:** request HTML/CSS without scripts, inline handlers, iframes, forms, or unsafe URL schemes.

## Known limitations

No web search or corpus freshness mechanism exists. There is no authentication, multi-user collaboration, public deployment, autonomous action, or complex document editing. Retrieval is FTS rather than semantic embeddings. Artifact data is response/message metadata, not a dedicated database record. Local model quality/latency depends on host hardware.

## Submission documents

- [PRD.md](PRD.md)
- [design.md](design.md)
- [architecture.md](architecture.md)
- [Final deliverable checklist](docs/FINAL_DELIVERABLE_CHECKLIST.md)
