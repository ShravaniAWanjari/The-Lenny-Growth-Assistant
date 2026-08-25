# Submission Demo Script — The Lenny Growth Assistant

Target: 2–3 minutes. Record with your camera on, the app open at `http://localhost:8000`, and the browser zoom at 100%.

## 0:00–0:20 — Introduction

> Hi, I’m Shravani, and this is The Lenny Growth Assistant. It turns 297 Lenny’s Podcast episodes into a source-grounded product and growth research assistant.

## 0:20–0:45 — Product and decisions

> The central decision was to optimize for trust rather than a generic chatbot. Every domain question retrieves transcript passages first, then the model receives that evidence and the recent conversation context. If the corpus does not support a question, the assistant refuses instead of inventing an answer.
>
> I used FastAPI for the API and static frontend, PostgreSQL for transcript search plus persistent sessions, and a Pi agent for skill routing and model calls. Docker Compose starts PostgreSQL, Ollama, the Pi agent, and the backend together. It also automatically downloads the local `llama3.2` model on the first run.

## 0:45–1:20 — Local grounded answer

**Action:** Select **Local** and ask: `What do Lenny's guests say about product-market fit?`

> I’m using the local Ollama provider here. PostgreSQL full-text retrieval finds relevant timestamped transcript chunks before the response is generated. These source cards expose the guest, episode, timestamp, and original link, so the answer is easy to verify.

**Action:** Open one source/timestamp.

> The timestamp links back to the original episode, which is the grounding mechanism behind the UI.

## 1:20–1:45 — Context and persistence

**Action:** Ask: `Which of those signals should an early-stage B2B startup measure first?` Then open the Sessions drawer.

> This follow-up uses the first turn as context. Sessions and messages are persisted in PostgreSQL, so I can refresh, return to this conversation, or create another isolated session without mixing contexts.

## 1:45–2:15 — Cloud choice and artifacts

**Action:** Switch to **Cloud**, then ask: `Create a Markdown checklist for testing PMF.`

> The model selector makes the trade-off explicit: Ollama is local and privacy-friendly; Gemini is cloud-hosted and can offer stronger hosted-model capability. There is no silent fallback between them.

**Action:** Ask: `Create a visual HTML card comparing PMF signals.` Open the artifact.

> The Pi agent recognizes artifact requests. Markdown is downloadable, and HTML is sanitized in FastAPI then rendered inside a sandboxed iframe, so generated visuals remain useful without trusting generated code.

## 2:15–2:40 — Hallucination guard and close

**Action:** Ask: `What do the transcripts say about quantum mechanics?`

> This is outside the supplied corpus. With no supporting sources, the assistant states that it cannot answer reliably instead of hallucinating. That source-grounded behavior, persistent context, provider choice, and safe artifacts are the core decisions behind the project. Thank you.

## Recording checklist

- Keep your camera visible throughout.
- Wait for the Local response to finish before switching providers.
- Ensure one source link, the session drawer, Markdown artifact, and HTML artifact are visibly shown.
- If time is tight, prioritize Local Ollama, sources, the follow-up, one HTML artifact, and the unsupported-question refusal.
