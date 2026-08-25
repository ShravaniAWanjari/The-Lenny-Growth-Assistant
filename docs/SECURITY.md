# Security Architecture & Safeguards — The Lenny Growth Assistant

This document outlines the defense-in-depth security model implemented in **The Lenny Growth Assistant**.

---

## 1. Untrusted Transcript & Ingestion Isolation

- **Source Code Isolation**: All transcript data is treated as untrusted text. No scripts, executable files, or build scripts from source transcript repositories are ever executed.
- **Normalization Pipeline**: Ingestion parses raw transcripts into static JSON (`episodes.json`, `chunks.json`, `topics.json`) through strict schema validators (`app/ingestion/validator.py`).
- **Prompt Injection Defense**: When transcript chunks are passed to LLMs, system prompts use explicit boundary delimiters (`<<<TRANSCRIPT_CONTEXT>>>` and `<<<USER_QUERY>>>`), instructing the model to treat transcript text exclusively as reference data and ignore any embedded instructions.

---

## 2. Dual-Layer HTML Artifact Sanitization & Sandboxing

HTML Visual Artifacts undergo two independent defensive layers before display:

### Layer 1: Backend Rust-Based `nh3` Sanitization
- Implemented in [`backend/app/security.py`](file:///c:/Users/shrav/Desktop/12%20week%20thing/Lenny/backend/app/security.py) using the `nh3` library (Rust Ammonia engine).
- **Tag Allowlist**: Only safe formatting and structural tags are permitted (`div`, `span`, `p`, `table`, `h1`-`h6`, `style`, `section`, etc.).
- **Strict Tag Stripping**: All `<script>`, `<iframe>`, `<object>`, `<embed>`, `<applet>`, `<form>`, and `<meta http-equiv>` tags are stripped or rejected.
- **Attribute Allowlist**: Event handlers (`onclick`, `onerror`, `onload`, `onmouseover`, etc.) are stripped.
- **URL Scheme Validation**: Only `http`, `https`, and `mailto` URL schemes are allowed; `javascript:`, `data:`, and `vbscript:` schemes are neutralized.

### Layer 2: Client-Side Isolated Iframe Sandboxing
- Rendered in [`frontend/index.html`](file:///c:/Users/shrav/Desktop/12%20week%20thing/Lenny/frontend/index.html) inside an `<iframe>` configured with:
  ```html
  <iframe id="artifactIframe" sandbox="allow-same-origin" title="Sandboxed Artifact Viewer"></iframe>
  ```
- **Omission of `allow-scripts`**: The `sandbox` attribute deliberately **omits `allow-scripts`**, rendering it impossible for even zero-day bypass payloads to execute JavaScript in the parent or frame context.
- **Content Injection**: Content is injected strictly via `srcdoc` after server-side sanitization.

---

## 3. Network & Service Isolation

```
[ Evaluator Host ]
       │
       ▼ (Exposed Port 8000)
┌─────────────────────────────────────────────────────────┐
│                    lenny-network                        │
│                                                         │
│   FastAPI (Public Proxy & Sanitizer)                    │
│      │                           │                      │
│      ▼ (Private :5432)           ▼ (Private :3001)      │
│   PostgreSQL                  Pi Agent                  │
└─────────────────────────────────────────────────────────┘
```

- **PostgreSQL**: Bound only to the internal Docker network. External clients cannot connect directly to port 5432.
- **Pi Agent**: Internal service listening on port 3001 within the container bridge network.
- **CORS Protection**: FastAPI enforces CORS rules configured through the `ALLOWED_ORIGINS` environment variable.

---

## 4. Secret & Credential Handling

- **Server-Side API Keys**: `GEMINI_API_KEY` is loaded exclusively into backend/agent environments and never transmitted or exposed to the browser client.
- **Version Control Exclusion**: `.env` is listed in `.gitignore` and audited to ensure no live keys are committed. A placeholder reference is maintained in `.env.example`.
- **Database Passwords**: Controlled via `POSTGRES_PASSWORD` and injected at container runtime.

---

## 5. Session Isolation & Access Boundaries

- **Database-Level Isolation**: Messages and session states are keyed by unique UUIDv4 `session_id` tokens with foreign-key cascading delete constraints.
- **Context Separation**: Requests for Session A only fetch conversation history explicitly belonging to Session A. Cross-session contamination is prevented at the SQL query level (`WHERE session_id = :id`).

---

## 6. Known Security Limitations & Operational Notes

1. **Local Ollama Trust**: When using the local provider, Ollama operates on `host.docker.internal:11434`. It is assumed that the local Ollama instance is under the operator's control.
2. **Download Responsibility**: Exported `.html` files contain static HTML. Opening exported HTML files locally in a standard browser outside the application sandbox is safe because all executable scripts were stripped during generation.
