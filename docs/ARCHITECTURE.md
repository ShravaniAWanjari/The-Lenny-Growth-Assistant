# System Architecture — The Lenny Growth Assistant

The Lenny Growth Assistant is a grounded AI platform built on top of 297 transcripts from **Lenny's Podcast**. It combines PostgreSQL Full-Text Search (FTS), a dedicated Node/TypeScript **Pi Agent**, dual LLM providers (**Google Gemini** & **Local Ollama**), and an HTML/Markdown Artifact generation engine.

---

## 1. High-Level System Architecture

```mermaid
graph TD
    User([Evaluator / User Browser])
    
    subgraph Host_Environment [Docker Host Environment / Local Machine]
        subgraph Public_Boundary [Publicly Accessible Boundary :8000]
            FastAPI["FastAPI Application Server<br/>(Python 3.12 / Uvicorn)<br/>• Session & Chat APIs<br/>• Static Frontend Delivery<br/>• HTML Sanitizer (nh3)"]
            Frontend["Frontend Interface<br/>(HTML5 / Vanilla CSS / JS)<br/>• Cinematic Fixed Hero<br/>• Frosted Glass Workspace<br/>• Sandboxed Artifact Modal"]
        end
        
        subgraph Private_Network [Internal Docker Network: lenny-network]
            Postgres[("PostgreSQL 16 Database<br/>• 297 Episodes<br/>• 14,933 Chunks<br/>• GIN Full-Text Index<br/>• Sessions & Messages")]
            PiAgent["Pi Agent Microservice<br/>(Node.js 20 / TypeScript)<br/>• Skills Engine<br/>• Prompt Orchestration<br/>• Port :3001 (Private)"]
        end
    end
    
    subgraph External_Providers [LLM Providers]
        Gemini["Google Gemini Cloud API<br/>(gemini-2.5-flash / gemini-1.5-pro)"]
        Ollama["Local Ollama Instance<br/>(llama3.2 / host-gateway)"]
    end
    
    User <-->|HTTP / Static Assets| Frontend
    Frontend <-->|REST API JSON| FastAPI
    FastAPI <-->|SQLAlchemy / FTS Queries| Postgres
    FastAPI <-->|HTTP POST /chat| PiAgent
    PiAgent <-->|HTTPS API Key| Gemini
    PiAgent <-->|HTTP host.docker.internal| Ollama
```

---

## 2. Retrieval-Augmented Generation (RAG) Architecture

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Browser
    participant API as FastAPI Backend
    participant DB as PostgreSQL (FTS & Topics)
    participant Pi as Pi Agent Service
    participant LLM as LLM (Gemini / Ollama)

    User->>API: POST /chat { prompt, session_id, provider }
    API->>API: Extract domain keywords & sanitize search tokens
    API->>DB: PostgreSQL FTS Query + GIN index match
    API->>DB: Query curated Topic Index (PMF, Growth, Hiring, etc.)
    DB-->>API: Top-K Grounded Transcript Chunks + YouTube Timestamps
    API->>Pi: POST /chat { prompt, retrievedSources, history }
    Pi->>Pi: Match Skill Triggers (Ship 30, Markdown, HTML Visual)
    Pi->>LLM: Generate Grounded Answer + Citations + Artifacts
    LLM-->>Pi: Raw Structured Response & Artifact Code
    Pi-->>API: Return text response, sources, and artifact
    API->>API: Sanitize HTML Artifact via nh3 allowlist
    API->>DB: Persist User & Assistant messages to Session
    API-->>User: JSON { response, sources, artifact, session_id }
```

---

## 3. Artifact Generation & Security Architecture

```mermaid
graph LR
    UserReq[User Content Request] --> Trigger[Pi Skill Classifier]
    Trigger --> Gen[Raw HTML / Markdown Generation]
    
    subgraph Backend_Security_Boundary [FastAPI Security Pipeline]
        Gen --> Sanitize[nh3 Ammonia Sanitizer]
        Sanitize --> TagFilter[Allowlist Tag & Attribute Filter]
        TagFilter --> SchemeCheck[Safe URL Scheme Validator]
        SchemeCheck --> CleanHTML[Verified Safe HTML]
    end
    
    subgraph Browser_Sandbox [Client Isolation Sandbox]
        CleanHTML --> Iframe["&lt;iframe sandbox='allow-same-origin'&gt;<br/>(Scripts Strictly Prohibited)"]
        Iframe --> Visual[Rendered Visual Card]
        CleanHTML --> Download[Download .html / .md]
    end
```

---

## 4. Key Component Responsibilities

| Component | Technology | Primary Responsibilities |
|---|---|---|
| **Frontend** | Vanilla JS / CSS3 / HTML5 | Cinematic responsive UI, session drawer, custom dialogs, sandboxed artifact viewer, model provider switcher. |
| **FastAPI Backend** | Python 3.12 / FastAPI / SQLAlchemy | REST endpoints, database connection pooling, search query extraction, RAG orchestration, HTML sanitization, session persistence. |
| **Database** | PostgreSQL 16 (Alpine) | Full-text search over transcript chunks (`to_tsvector` GIN indexes), episode metadata, topic link mappings, session and message stores. |
| **Pi Agent** | Node.js 20 / TypeScript / Express | Agentic execution, system prompt assembly, conversational memory trimming, Ship 30 writing skill, markdown & HTML artifact generation. |
