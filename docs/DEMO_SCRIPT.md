# Demo Video Script & Walkthrough Guide — The Lenny Growth Assistant

**Target Duration**: 3–5 minutes  
**Audience**: Evaluators, hiring managers, and product engineers.  
**Objective**: Demonstrate the grounded retrieval, multi-turn reasoning, provider flexibility, Ship 30 skill, secure visual artifacts, and cinematic UX of The Lenny Growth Assistant.

---

## Timeline & Step-by-Step Script

### `0:00 – 0:20` | Introduction & Product Overview
- **Action**: Open browser at `http://localhost:8000`.
- **Narration**: *"Welcome to The Lenny Growth Assistant — a production-grade, grounded knowledge engine and content generator built on top of 297 Lenny's Podcast episodes with top founders and product leaders."*

### `0:20 – 0:40` | Cinematic Hero Experience
- **Action**: Scroll down smoothly from the fixed hero title to reveal the dark frosted glass conversational workspace floating over the background.
- **Narration**: *"The interface features a cinematic sticky hero background and a dark glass workspace with persistent multi-session drawer and instant model provider selection."*

### `0:40 – 1:15` | Grounded Knowledge Retrieval
- **Action**: Click the prompt chip: *"What do Lenny's guests say about product-market fit?"* or type it into the composer and press Enter.
- **Narration**: *"When a user asks a question, our PostgreSQL full-text search and topic indexing instantly locate the exact transcript turns across hundreds of hours of conversations. Notice how the answer synthesizes concrete frameworks from Andy Johns, Rahul Vohra, and Brian Balfour, citing exact guest names and timestamps."*

### `1:15 – 1:35` | Grounded Sources & YouTube Deep Links
- **Action**: Expand the **Sources** accordions under the response and hover/click on the timestamp link.
- **Narration**: *"Every cited insight is verifiable. Clicking the timestamp deep-links directly to the exact second in the original YouTube episode where the guest spoke."*

### `1:35 – 2:00` | Multi-Turn Reasoning & Session Isolation
- **Action**: Ask a follow-up: *"Which of these frameworks is easiest for an early-stage B2B startup to measure first?"*
- **Narration**: *"The assistant retains full conversational context across turns. In the left drawer, conversations persist across reloads with custom rename and deletion dialogs, isolated strictly per session."*

### `2:00 – 2:20` | Dual Provider Selection (Local vs. Cloud)
- **Action**: Click the provider dropdown in the top right and switch between **Local (Ollama)** and **Cloud (Gemini)**.
- **Narration**: *"Users can toggle seamlessly between local open-weight models via Ollama and Google Gemini in the cloud, with automatic metadata tags indicating which model generated each response."*

### `2:20 – 2:50` | Ship 30 Writing Skill
- **Action**: Send prompt: *"Turn what we learned about PMF into a Ship 30 atomic essay."*
- **Narration**: *"The embedded Pi Agent includes specialized writing skills, such as the Ship 30 framework, transforming transcript takeaways into compelling headlines, modular bullet points, and actionable conclusions."*

### `2:50 – 3:15` | Markdown Artifact Generation
- **Action**: Send prompt: *"Create a Markdown guide on avoiding burnout based on Andy Johns' advice."*
- **Narration**: *"When comprehensive documents are requested, the assistant outputs structured Markdown artifacts rendered cleanly with interactive preview and direct download capabilities."*

### `3:15 – 3:40` | HTML Visual Artifact & Sandboxed Modal
- **Action**: Send prompt: *"Create a visual HTML card comparing PMF signals."*
- **Narration**: *"The assistant can also generate rich HTML Visual Artifacts — visual comparison cards, matrixes, and dashboards."*

### `3:40 – 4:00` | Dual-Layer Security & Download Export
- **Action**: Click the **View HTML Visual** banner to open the modal. Show the rendered visual card, then click **Download .html**.
- **Narration**: *"For security, all HTML artifacts pass through backend nh3 sanitization and client-side iframe sandboxing with scripts strictly disabled. Users can safely inspect and export the artifact locally."*

### `4:00 – 4:30` | Architecture Summary & Wrap-Up
- **Action**: Show `docker-compose.prod.yml` or the `/health` endpoint in another tab.
- **Narration**: *"Under the hood, the entire system runs locally via a single `docker compose up` command, with PostgreSQL and the Pi Agent locked in an internal network and FastAPI serving the frontend. Thank you for watching!"*
