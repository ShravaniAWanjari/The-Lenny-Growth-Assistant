import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session
import httpx

from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, SessionLocal, settings, get_db
from app.models import Base, Session as DBSession, Message as DBMessage, Episode, TranscriptChunk
from app.retrieval import search
from app.security import sanitize_and_validate_html
from app.ingestion.db_loader import load_processed_data_to_db

# Locate directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

app = FastAPI(
    title="The Lenny Growth Assistant",
    description="Backend API & Cinematic Interface for Lenny Growth Assistant with Skills, Artifacts, RAG, and Sessions",
    version="0.6.0",
)

# -----------------------------------------------------------------------------
# CORS Middleware (Checkpoint 3)
# -----------------------------------------------------------------------------
origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Startup Lifecycle & Multi-Service System Readiness (Checkpoints 4 & 5)
# -----------------------------------------------------------------------------
_app_state: Dict[str, Any] = {
    "status": "setting_up",
    "db_ready": False,
    "pi_agent_ready": False,
    "ollama_ready": False,
    "episodes_count": 0,
    "chunks_count": 0,
}


def _check_system_readiness():
    """Background monitor that verifies DB, Pi Agent, and Ollama before declaring app Ready."""
    import time

    # 1. Initialize DB & Populate Data if empty
    while True:
        try:
            Base.metadata.create_all(bind=engine)
            ep_count = 0
            chunk_count = 0
            with SessionLocal() as db:
                ep_count = db.query(Episode).count()
                chunk_count = db.query(TranscriptChunk).count()

            if ep_count == 0 and DATA_PROCESSED_DIR.exists():
                print("Database is empty. Automatically loading initial transcript dataset in background...")
                _app_state["status"] = "setting_up"
                load_processed_data_to_db(DATA_PROCESSED_DIR)
                print("Initial transcript dataset successfully loaded.")
                with SessionLocal() as db:
                    ep_count = db.query(Episode).count()
                    chunk_count = db.query(TranscriptChunk).count()

            if ep_count > 0 and chunk_count > 0:
                _app_state["db_ready"] = True
                _app_state["episodes_count"] = ep_count
                _app_state["chunks_count"] = chunk_count
                break
        except Exception as e:
            print(f"[System Init] Waiting for database: {e}")
        time.sleep(2)

    # 2. Continuous Monitoring for Pi Agent and Ollama
    while True:
        try:
            # Check Pi-Agent
            pi_url = settings.pi_agent_url.rstrip("/")
            try:
                with httpx.Client(timeout=2.0) as client:
                    r = client.get(f"{pi_url}/health")
                    _app_state["pi_agent_ready"] = (r.status_code == 200)
            except Exception:
                _app_state["pi_agent_ready"] = False

            # Check Ollama across candidate endpoints
            ollama_candidates = [
                settings.ollama_base_url.rstrip("/"),
                "http://ollama:11434",
                "http://host.docker.internal:11434",
                "http://localhost:11434",
            ]
            ollama_online = False
            for target_url in dict.fromkeys(ollama_candidates):
                try:
                    with httpx.Client(timeout=1.5) as client:
                        r = client.get(f"{target_url}/api/tags")
                        if r.status_code == 200:
                            ollama_online = True
                            break
                except Exception:
                    continue
            _app_state["ollama_ready"] = ollama_online

            # All services must be online
            if _app_state["db_ready"] and _app_state["pi_agent_ready"] and _app_state["ollama_ready"]:
                _app_state["status"] = "ready"
                print("[System Init] Full stack online (Postgres, Pi-Agent, Ollama). System: READY.")
                break
            else:
                _app_state["status"] = "setting_up"
        except Exception as e:
            print(f"[System Init] Readiness loop error: {e}")

        time.sleep(2)


@app.on_event("startup")
def startup_db_init():
    import threading
    t = threading.Thread(target=_check_system_readiness, daemon=True)
    t.start()


# -----------------------------------------------------------------------------
# Health & Status Check Endpoints (Checkpoint 4)
# -----------------------------------------------------------------------------
@app.get("/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "service": "lenny-growth-assistant",
        "app_status": _app_state.get("status", "setting_up"),
        "db_ready": _app_state.get("db_ready", False),
        "pi_agent_ready": _app_state.get("pi_agent_ready", False),
        "ollama_ready": _app_state.get("ollama_ready", False),
        "episodes_count": _app_state.get("episodes_count", 0),
        "chunks_count": _app_state.get("chunks_count", 0),
    }


@app.get("/status", tags=["System"])
def status_endpoint():
    return {
        "status": _app_state.get("status", "setting_up"),
        "app_status": _app_state.get("status", "setting_up"),
        "db_ready": _app_state.get("db_ready", False),
        "pi_agent_ready": _app_state.get("pi_agent_ready", False),
        "ollama_ready": _app_state.get("ollama_ready", False),
        "episodes_count": _app_state.get("episodes_count", 0),
        "chunks_count": _app_state.get("chunks_count", 0),
    }


@app.get("/health/db", tags=["System"])
def health_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "postgresql",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}",
        )


# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------

class SessionCreateRequest(BaseModel):
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional metadata for the session")


class SessionUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, description="New title for the session")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata updates")


class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    updated_at: Optional[str] = None
    message_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class MessageItem(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query to search against Lenny's transcript knowledge base")
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of chunks to return")
    topic_boost: bool = Field(default=True, description="Whether to apply curated topic index boost")


class SourceItem(BaseModel):
    guest: str
    episode: str
    speaker: str
    timestamp: str
    source_url: str
    score: float
    text: Optional[str] = None


class StructuredContent(BaseModel):
    type: str = Field(..., description="Type of content: 'article' | 'summary' | 'key_points' | 'comparison'")
    title: str
    content: str


class ArtifactItem(BaseModel):
    artifact_id: str
    session_id: str
    type: str = Field(..., description="Artifact type: 'markdown' | 'html'")
    title: str
    content: str
    validation_status: str = Field(default="valid", description="'valid' | 'sanitized' | 'rejected'")
    original_modified: bool = Field(default=False, description="True if sanitization altered the original content")
    validation_error: Optional[str] = None
    created_at: str


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000, description="User prompt to send to the assistant")
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session ID. If not provided, a new session is created automatically.",
    )
    provider: Optional[str] = Field(
        default=None,
        description="LLM provider override ('gemini' or 'ollama'). Defaults to LLM_PROVIDER in .env",
    )
    model: Optional[str] = Field(
        default=None,
        description="Optional model override",
    )


class ChatResponse(BaseModel):
    session_id: str
    response: str
    provider: str
    model: Optional[str] = None
    status: str = "ok"
    sources: List[SourceItem] = []
    skill_invoked: Optional[str] = None
    content: Optional[StructuredContent] = None
    artifact: Optional[ArtifactItem] = None


# -----------------------------------------------------------------------------
# Health & Status Endpoints
# -----------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "ok",
        "service": "lenny-growth-assistant",
    }


@app.get("/health/db", tags=["Health"])
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "postgresql",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "database": "postgresql", "message": str(e)},
        )


# -----------------------------------------------------------------------------
# Session & Conversation Endpoints
# -----------------------------------------------------------------------------

@app.get("/sessions", response_model=List[SessionResponse], tags=["Sessions"])
def list_sessions(db: Session = Depends(get_db)):
    """List all conversation sessions ordered by most recently updated."""
    sessions = db.query(DBSession).order_by(DBSession.updated_at.desc(), DBSession.id.desc()).all()
    results = []
    for s in sessions:
        count = db.query(DBMessage).filter(DBMessage.session_id == s.session_id).count()
        results.append(
            SessionResponse(
                session_id=s.session_id,
                created_at=s.created_at.isoformat() if s.created_at else "",
                updated_at=s.updated_at.isoformat() if s.updated_at else "",
                message_count=count,
                metadata=s.metadata_json or {},
            )
        )
    return results


@app.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED, tags=["Sessions"])
def create_session(request: SessionCreateRequest = None, db: Session = Depends(get_db)):
    """Create a new conversational session."""
    meta = request.metadata if (request and request.metadata) else {}
    public_id = f"session_{uuid.uuid4().hex[:16]}"
    now = datetime.now(timezone.utc)

    session_obj = DBSession(
        session_id=public_id,
        metadata_json=meta,
        created_at=now,
        updated_at=now,
    )
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)

    return SessionResponse(
        session_id=session_obj.session_id,
        created_at=session_obj.created_at.isoformat(),
        updated_at=session_obj.updated_at.isoformat(),
        message_count=0,
        metadata=session_obj.metadata_json,
    )


@app.get("/sessions/{session_id}", response_model=SessionResponse, tags=["Sessions"])
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get metadata for a specific session."""
    session_obj = db.query(DBSession).filter(DBSession.session_id == session_id).first()
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    msg_count = db.query(DBMessage).filter(DBMessage.session_id == session_id).count()

    return SessionResponse(
        session_id=session_obj.session_id,
        created_at=session_obj.created_at.isoformat(),
        updated_at=session_obj.updated_at.isoformat() if session_obj.updated_at else None,
        message_count=msg_count,
        metadata=session_obj.metadata_json,
    )


@app.patch("/sessions/{session_id}", response_model=SessionResponse, tags=["Sessions"])
def update_session(session_id: str, request: SessionUpdateRequest, db: Session = Depends(get_db)):
    """Update title or metadata for a specific session."""
    session_obj = db.query(DBSession).filter(DBSession.session_id == session_id).first()
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    meta = dict(session_obj.metadata_json or {})
    if request.title is not None:
        meta["title"] = request.title.strip()
    if request.metadata is not None:
        meta.update(request.metadata)

    session_obj.metadata_json = meta
    session_obj.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session_obj)

    msg_count = db.query(DBMessage).filter(DBMessage.session_id == session_id).count()

    return SessionResponse(
        session_id=session_obj.session_id,
        created_at=session_obj.created_at.isoformat() if session_obj.created_at else "",
        updated_at=session_obj.updated_at.isoformat() if session_obj.updated_at else "",
        message_count=msg_count,
        metadata=session_obj.metadata_json,
    )


@app.delete("/sessions/{session_id}", tags=["Sessions"])
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a session and all its associated messages."""
    session_obj = db.query(DBSession).filter(DBSession.session_id == session_id).first()
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    db.delete(session_obj)
    db.commit()

    return {"status": "ok", "deleted_session_id": session_id}


@app.delete("/sessions", tags=["Sessions"])
def delete_all_sessions(db: Session = Depends(get_db)):
    """Delete all sessions and their messages."""
    count = db.query(DBSession).delete()
    db.query(DBMessage).delete()
    db.commit()
    return {"status": "ok", "deleted_count": count}


@app.get("/sessions/{session_id}/messages", response_model=List[MessageItem], tags=["Sessions"])
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """Get all messages in chronological order for a specific session."""
    session_obj = db.query(DBSession).filter(DBSession.session_id == session_id).first()
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    messages = (
        db.query(DBMessage)
        .filter(DBMessage.session_id == session_id)
        .order_by(DBMessage.created_at.asc(), DBMessage.id.asc())
        .all()
    )

    return [
        MessageItem(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat(),
            metadata=m.metadata_json,
        )
        for m in messages
    ]


# -----------------------------------------------------------------------------
# Retrieval & Grounded Chat Endpoints
# -----------------------------------------------------------------------------

@app.post("/retrieval/search", response_model=List[SourceItem], tags=["Retrieval"])
def search_knowledge(request: RetrievalRequest, db: Session = Depends(get_db)):
    """Search knowledge base using PostgreSQL FTS + topic indexes."""
    raw_results = search(
        query=request.query,
        top_k=request.top_k,
        topic_boost=request.topic_boost,
        db=db,
    )
    return [
        SourceItem(
            guest=r["guest"],
            episode=r["episode"],
            speaker=r["speaker"],
            timestamp=r["timestamp"],
            source_url=r["source_url"],
            score=r["relevance_score"],
            text=r["text"],
        )
        for r in raw_results
    ]


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    clean_prompt = request.prompt.strip()
    if not clean_prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be empty.",
        )

    selected_provider = (request.provider or settings.llm_provider).lower()
    if selected_provider not in ["gemini", "ollama"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider '{selected_provider}'. Supported providers: 'gemini', 'ollama'.",
        )

    now = datetime.now(timezone.utc)

    # 1. Resolve Session
    if request.session_id:
        session_obj = db.query(DBSession).filter(DBSession.session_id == request.session_id).first()
        if not session_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{request.session_id}' not found.",
            )
    else:
        # Create a new session automatically
        public_id = f"session_{uuid.uuid4().hex[:16]}"
        initial_title = clean_prompt[:60] + ("..." if len(clean_prompt) > 60 else "")
        session_obj = DBSession(
            session_id=public_id,
            metadata_json={"title": initial_title},
            created_at=now,
            updated_at=now,
        )
        db.add(session_obj)
        db.commit()
        db.refresh(session_obj)

    # If session has no title yet, set title to first prompt
    if not session_obj.metadata_json or not session_obj.metadata_json.get("title"):
        meta = dict(session_obj.metadata_json or {})
        meta["title"] = clean_prompt[:60] + ("..." if len(clean_prompt) > 60 else "")
        session_obj.metadata_json = meta

    # 2. Fetch Conversation History (last 8 messages)
    history_records = (
        db.query(DBMessage)
        .filter(DBMessage.session_id == session_obj.session_id)
        .order_by(DBMessage.created_at.asc(), DBMessage.id.asc())
        .all()
    )

    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in history_records[-8:]
    ]

    # 3. Knowledge Retrieval with Context Enrichment for follow-ups
    raw_results = search(
        query=clean_prompt,
        top_k=5,
        topic_boost=True,
        db=db,
    )

    # If direct query yielded few/no results and we have prior history, try searching with prior user message context
    if (len(raw_results) == 0 or raw_results[0]["relevance_score"] < 0.25) and conversation_history:
        prior_user_msgs = [m["content"] for m in conversation_history if m["role"] == "user"]
        if prior_user_msgs:
            enriched_query = f"{prior_user_msgs[-1]} {clean_prompt}"
            enriched_results = search(
                query=enriched_query,
                top_k=5,
                topic_boost=True,
                db=db,
            )
            if enriched_results:
                raw_results = enriched_results

    retrieved_sources = [
        {
            "guest": r["guest"],
            "episode": r["episode"],
            "speaker": r["speaker"],
            "timestamp": r["timestamp"],
            "source_url": r["source_url"],
            "score": float(r["relevance_score"]),
            "text": r["text"],
        }
        for r in raw_results
    ]

    # 4. Dispatch to Pi Agent Service
    pi_chat_url = f"{settings.pi_agent_url.rstrip('/')}/chat"
    payload = {
        "prompt": clean_prompt,
        "provider": selected_provider,
        "model": request.model or (settings.ollama_model if selected_provider == "ollama" else None),
        "retrievedSources": retrieved_sources,
        "conversationHistory": conversation_history,
    }

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(pi_chat_url, json=payload)
            if resp.status_code != 200:
                detail_msg = resp.text
                try:
                    detail_json = resp.json()
                    detail_msg = detail_json.get("error", detail_json.get("detail", resp.text))
                except Exception:
                    pass
                print(f"[Backend Error] Pi Agent returned {resp.status_code}: {detail_msg}", flush=True)
                raise HTTPException(status_code=resp.status_code, detail=detail_msg)

            data = resp.json()
            response_text = data.get("response", "")
            model_id = data.get("model")
            sources_data = data.get("sources", [])
            skill_invoked = data.get("skill_invoked")
            raw_content = data.get("content")
            raw_artifact = data.get("artifact")

            sources = [
                SourceItem(
                    guest=s.get("guest", ""),
                    episode=s.get("episode", ""),
                    speaker=s.get("speaker", ""),
                    timestamp=s.get("timestamp", ""),
                    source_url=s.get("source_url", ""),
                    score=float(s.get("score", s.get("relevance_score", 0.0))),
                )
                for s in sources_data
            ]

            # Structured Content Object
            structured_content_obj = None
            if raw_content:
                structured_content_obj = StructuredContent(
                    type=raw_content.get("type", "summary"),
                    title=raw_content.get("title", "Summary"),
                    content=raw_content.get("content", ""),
                )

            # Artifact Sanitization & Validation Pipeline
            artifact_obj = None
            if raw_artifact:
                art_type = raw_artifact.get("type", "markdown")
                art_title = raw_artifact.get("title", "Artifact")
                art_content = raw_artifact.get("content", "")
                art_id = f"art_{uuid.uuid4().hex[:12]}"

                val_status = "valid"
                orig_mod = False
                val_error = None

                if art_type == "html":
                    cleaned_html, val_status, orig_mod, val_error = sanitize_and_validate_html(art_content)
                    if val_status == "rejected":
                        art_content = ""
                    else:
                        art_content = cleaned_html

                artifact_obj = ArtifactItem(
                    artifact_id=art_id,
                    session_id=session_obj.session_id,
                    type=art_type,
                    title=art_title,
                    content=art_content,
                    validation_status=val_status,
                    original_modified=orig_mod,
                    validation_error=val_error,
                    created_at=datetime.now(timezone.utc).isoformat(),
                )

            # 5. Persist Conversation in Database (User + Assistant)
            user_msg = DBMessage(
                session_id=session_obj.session_id,
                role="user",
                content=clean_prompt,
                created_at=datetime.now(timezone.utc),
                metadata_json={},
            )
            db.add(user_msg)
            db.flush()

            assistant_meta = {
                "provider": selected_provider,
                "model": model_id,
                "sources": [s.model_dump() for s in sources],
                "skill_invoked": skill_invoked,
            }
            if structured_content_obj:
                assistant_meta["content"] = structured_content_obj.model_dump()
            if artifact_obj:
                assistant_meta["artifact"] = artifact_obj.model_dump()

            assistant_msg = DBMessage(
                session_id=session_obj.session_id,
                role="assistant",
                content=response_text,
                created_at=datetime.now(timezone.utc),
                metadata_json=assistant_meta,
            )
            db.add(assistant_msg)

            session_obj.updated_at = datetime.now(timezone.utc)
            db.commit()

            return ChatResponse(
                session_id=session_obj.session_id,
                response=response_text,
                provider=data.get("provider", selected_provider),
                model=model_id,
                status=data.get("status", "ok"),
                sources=sources,
                skill_invoked=skill_invoked,
                content=structured_content_obj,
                artifact=artifact_obj,
            )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to connect to Pi Agent service at {pi_chat_url}: {str(exc)}",
        )


# -----------------------------------------------------------------------------
# Frontend Static Files & App Routing (Phase 5)
# -----------------------------------------------------------------------------

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Frontend index.html not found"}
