# Demo Script — The Lenny Growth Assistant

Target: 2–3 minutes. Keep your camera on and the app at `http://localhost:8000` open.

> Hi, I’m Shravani. This is The Lenny Growth Assistant: a grounded product-and-growth research assistant built from 297 episodes of Lenny’s Podcast.
>
> The key product decision was to prioritize trust over generic chatbot behavior. FastAPI coordinates the application, PostgreSQL stores sessions and transcript search data, and a Pi agent uses retrieved evidence before generating an answer. Users can choose a cloud model or a local Ollama model, which gives a privacy and cost trade-off.

1. **First question — grounded answer**

   Ask: `What do Lenny's guests say about product-market fit?`

   > The backend retrieves relevant transcript passages first. These source cards show the guest, timestamp, and original link, so the answer is inspectable rather than an unsupported claim.

2. **Second question — context and sessions**

   Ask: `Which of those signals should an early-stage B2B startup measure first?`

   > This follow-up uses the first turn as context. The sidebar shows that the conversation is persisted as its own PostgreSQL session, so it remains available after a refresh and stays separate from other chats.

3. **Artifacts**

   Ask: `Create a Markdown checklist for testing PMF.` Then ask: `Create a visual HTML card comparing PMF signals.`

   > The agent can turn grounded material into a Markdown artifact or a small HTML visual. HTML is sanitized on the backend and rendered in a sandboxed iframe before it can be previewed or downloaded.

4. **Hallucination guard and provider choice**

   Ask: `What do the transcripts say about quantum mechanics?`

   > With no supporting transcript evidence, the assistant refuses instead of inventing an answer. Finally, the provider selector supports Gemini for cloud quality and Ollama for a local workflow; I’m using **[say the provider currently selected]** for this response.

> That is the Lenny Growth Assistant: source-grounded answers, persistent context, useful artifacts, and safe fallback behavior.

Before recording, ensure an Ollama model is installed if you plan to show the local option: `docker compose -f docker-compose.prod.yml exec ollama ollama pull llama3.2`.
