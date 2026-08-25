# The Lenny Growth Assistant

A production-grade, grounded AI knowledge platform, product growth advisor, and structured content generator built on top of **297 Lenny's Podcast transcripts**. It combines PostgreSQL Full-Text Search (FTS), Pi Agent orchestration, multi-turn session persistence, specialized writing skills (Ship 30 for 30), dual LLM provider support (Google Gemini Cloud + Local Ollama), and dual-layer sandboxed HTML/Markdown artifact generation.

---

## 1. What the Project Is
The Lenny Growth Assistant is designed to make hundreds of hours of tactical advice from world-class product leaders, growth practitioners, and founders instantly accessible, verifiable, and actionable. Rather than generating ungrounded summaries, it synthesizes exact frameworks directly from verified transcript turns, providing deep links to YouTube timestamps and exporting clean publication-ready artifacts.

---

## 2. Architecture Overview
```
[ Browser Client (:8000) ]
        │
        ▼ (HTTP REST / Static Assets)
┌────────────────────────────────────────────────────────────┐
│                    lenny-network                           │
│                                                            │
│  FastAPI Backend (:8000)                                   │
│  ├── Session & Memory Management                           │
│  ├── PostgreSQL Full-Text Search & Topic Boosting          │
│  ├── HTML Sanitization Engine (Rust-based nh3)             │
│  └── Static File Server (/ & /static)                      │
│         │                             │                    │
│         ▼ (Private :5432)             ▼ (Private :3001)    │
│  PostgreSQL 16                     Pi Agent Service        │
│  (GIN FTS Indexes)                 (Node/TypeScript)       │
│                                       │          │         │
└───────────────────────────────────────┼──────────┼─────────┘
                                        ▼          ▼
                                  Google Gemini   Ollama
                                  (Cloud API)     (Local LLM)
```

---

## 3. Repository Structure
```text
├── agent/                       # Node.js / TypeScript Pi Agent Service
│   ├── skills/                  # Embedded writing skills (Ship 30, artifacts)
│   ├── src/                     # Agent execution & provider routing
│   ├── Dockerfile               # Production multi-stage Node build
│   └── package.json
├── backend/                     # FastAPI Application Server (Python 3.12)
│   ├── app/                     # API routes, models, database, security, RAG
│   ├── ingestion/               # Normalization, chunking, and DB loader
│   ├── Dockerfile               # Production Python image
│   └── requirements.txt
├── frontend/                    # Cinematic Web Interface
│   ├── assets/                  # Hero backgrounds and brand assets
│   ├── css/style.css            # Custom CSS3 & frosted glass tokens
│   ├── js/app.js                # Vanilla JavaScript application state
│   └── index.html               # Main application template & sandboxed modals
├── data/                        # Knowledge Base & Processed Datasets
│   └── processed/               # episodes.json, chunks.json, topics.json
├── docs/                        # Project Documentation
│   ├── ARCHITECTURE.md          # Complete system & data flow diagrams
│   ├── SECURITY.md              # Security model & sanitization guarantees
│   ├── TEST_REPORT.md           # Test suite breakdown & metrics
│   └── DEMO_SCRIPT.md           # 3-5 minute presentation walkthrough script
├── tests/                       # Pytest automated test suite (69 tests)
├── docker-compose.prod.yml      # Option C Production Hardened Compose
├── docker-compose.yml           # Local Development Compose
└── .env.example                 # Environment variable template
```

---

## 4. Quickstart: One-Command Production Run (Option C)

Start the complete production-hardened system with a single command:

```bash
docker compose -f docker-compose.prod.yml up --build
```

Then open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 5. Local Development Setup

### Step 1: Start PostgreSQL
```bash
docker compose up -d postgres
```

### Step 2: Set Up & Start Pi Agent (Node.js)
```bash
cd agent
npm install
npm run build
npm start
```

### Step 3: Set Up & Start FastAPI Backend (Python)
```bash
# In project root
python -m venv backend/.venv
# Windows:
backend\.venv\Scripts\activate
# macOS/Linux:
source backend/.venv/bin/activate

pip install -r backend/requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend --reload
```

---

## 6. PostgreSQL Database Setup & Data Ingestion
The database automatically loads the processed dataset upon first startup if empty. To manually re-ingest and build FTS vectors:
```bash
python backend/app/ingestion/db_loader.py
```

---

## 7. Pi Agent Service
The Pi Agent is an Express-based TypeScript service handling:
- Multi-turn conversation assembly and token window management.
- Dynamic skill classification (Ship 30 essays, summaries, comparison tables).
- Dispatching prompts to Gemini or Ollama.

---

## 8. Gemini Cloud Setup
1. Obtain an API key from Google AI Studio.
2. Add to your `.env` file:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key_here
   LLM_PROVIDER=gemini
   ```

---

## 9. Ollama Local Setup
1. Install [Ollama](https://ollama.ai/) locally and pull a model:
   ```bash
   ollama pull llama3.2
   ```
2. Configure `.env`:
   ```bash
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.2:latest
   ```

---

## 10. Knowledge Base & Transcript Dataset
- **297 Episodes**: Full transcripts from Lenny's Podcast.
- **14,933 Chunks**: Structured speaker turns with timestamps, duration, and guest metadata.
- **Curated Topics**: Handcrafted topic index mapping core startup themes (PMF, Growth loops, Hiring, Retention, Pricing).

---

## 11. RAG Architecture & FTS Search
1. **Query Sanitization**: Strips conversational stopwords while preserving domain concepts.
2. **PostgreSQL FTS**: Runs `tsquery` against weighted GIN indexes (`to_tsvector`).
3. **Topic Boosting**: Cross-references topic slugs to boost relevant foundational episodes.
4. **Deep Links**: Cites start timestamps with direct YouTube query links (`&t={seconds}`).

---

## 12. Session Persistence & Isolation
- Conversations and messages persist in PostgreSQL using UUIDv4 session identifiers.
- Conversations are strictly isolated at the database query level.
- Custom client modals allow creating, renaming, and deleting conversations with cascading message removal.

---

## 13. Writing Skills (Ship 30 for 30)
Triggered by prompts like *"Turn what we learned into a Ship 30 essay"*, the assistant formats outputs following the Ship 30 methodology:
- High-converting headline.
- Clear hook and modular bullet points.
- Actionable takeaway conclusion.

---

## 14. Artifact Generation (Markdown & HTML)
- **Markdown Documents**: Full structured guides and reports with syntax highlighting.
- **HTML Visual Cards**: Interactive dashboards, comparison matrices, and UI cards.
- **Exporting**: One-click download buttons for `.md` and `.html` files.

---

## 15. Dual-Layer HTML Security & Sandboxing
1. **Backend Sanitization**: Uses `nh3` (Ammonia Rust library) to enforce a strict allowlist of tags and attributes while stripping all `<script>`, `<iframe>`, `<object>`, and `on*` event handlers.
2. **Client Sandbox**: HTML rendered in an `<iframe>` configured with `sandbox="allow-same-origin"` (**NO `allow-scripts`**), preventing JavaScript execution.

---

## 16. Cinematic Frontend Interface
- **Fixed Hero**: Background image with left-aligned brand typography and smooth scroll interaction.
- **Frosted Glass Workspace**: Dark transparent glass elements.
- **Session Drawer**: Slide-out drawer with active indicators and dropdown actions.
- **Custom Modals**: Native-styled confirmation dialogs for deleting and renaming sessions.

---

## 17. Automated Testing
Run the complete automated test suite:
```bash
pytest tests/ -v
```
**Results**: **69 / 69 tests passing (100%)** across ingestion, chunking, retrieval, sessions, skills, security, and frontend.

---

## 18. Production Deployment Configuration
The system uses **Option C (Production Hardened Local Deployment)**:
- Single command execution with `docker compose -f docker-compose.prod.yml up --build`.
- PostgreSQL and Pi Agent strictly isolated on private internal network `lenny-network`.
- FastAPI server published on host `:8000` running production Uvicorn without `--reload`.

---

## 19. Environment Variables Reference
| Variable | Description | Default / Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://lenny:lenny_prod_password@postgres:5432/lenny` |
| `POSTGRES_PASSWORD` | PostgreSQL user password | `lenny_prod_password` |
| `GEMINI_API_KEY` | Google Gemini API Key | *(Secret key)* |
| `LLM_PROVIDER` | Active provider | `gemini` or `ollama` |
| `OLLAMA_BASE_URL` | Ollama API endpoint | `http://host.docker.internal:11434` |
| `OLLAMA_MODEL` | Ollama model tag | `llama3.2:latest` |
| `PI_AGENT_URL` | Internal Pi Agent URL | `http://pi-agent:3001` |
| `PI_AGENT_PORT` | Pi Agent port | `3001` |
| `ARTIFACT_SANITIZATION_MODE` | HTML safety mode | `sanitize` or `reject` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `*` or `http://localhost:8000` |

---

## 20. Known Limitations
1. **Ollama Network Routing in Docker**: When running Docker on Linux, ensure `--add-host host.docker.internal:host-gateway` is supported if connecting to a host-installed Ollama.
2. **Audio/Video Playback**: Deep links redirect to YouTube; native in-app video playback is not embedded to maintain lightweight performance.

---

## Additional Documentation
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Architectural and data-flow diagrams.
- [docs/SECURITY.md](docs/SECURITY.md) — Security boundaries, nh3 sanitization, and sandboxing rules.
- [docs/TEST_REPORT.md](docs/TEST_REPORT.md) — Detailed test suite execution report.
- [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) — 3-5 minute demo presentation script.
- [PRODUCTION_AUDIT.md](PRODUCTION_AUDIT.md) — Production audit report and findings matrix.
