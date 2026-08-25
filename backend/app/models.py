import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    func,
    asc,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import TSVECTOR

Base = declarative_base()


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(128), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)

    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="asc(Message.created_at), asc(Message.id)",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(128), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # "user" | "assistant" | "system"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    metadata_json = Column(JSON, default=dict, nullable=False)

    session = relationship("Session", back_populates="messages")


class Episode(Base):
    __tablename__ = "episodes"

    id = Column(String(128), primary_key=True)  # e.g., ep_adam-fishman
    slug = Column(String(128), unique=True, nullable=False, index=True)
    guest = Column(String(256), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    publish_date = Column(String(32), nullable=True)
    youtube_url = Column(String(512), nullable=True)
    video_id = Column(String(64), nullable=True)
    duration = Column(String(32), nullable=True)
    duration_seconds = Column(Float, default=0.0)
    view_count = Column(Integer, default=0)
    channel = Column(String(128), default="Lenny's Podcast")
    description = Column(Text, nullable=True)
    keywords = Column(JSON, default=list)
    turns_count = Column(Integer, default=0)
    chunks_count = Column(Integer, default=0)

    chunks = relationship("TranscriptChunk", back_populates="episode", cascade="all, delete-orphan")


class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id = Column(String(128), primary_key=True)  # e.g., chunk_adam-fishman_0001
    episode_id = Column(String(128), ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False, index=True)
    episode_slug = Column(String(128), nullable=False, index=True)
    guest = Column(String(256), nullable=False, index=True)
    episode_title = Column(String(512), nullable=False)
    publish_date = Column(String(32), nullable=True)
    speakers = Column(JSON, default=list)
    timestamp_start = Column(String(16), nullable=False)
    timestamp_end = Column(String(16), nullable=False)
    start_seconds = Column(Integer, default=0, index=True)
    end_seconds = Column(Integer, default=0)
    text = Column(Text, nullable=False)
    youtube_url = Column(String(512), nullable=False)
    video_id = Column(String(64), nullable=True)
    keywords = Column(JSON, default=list)
    word_count = Column(Integer, default=0)
    search_vector = Column(TSVECTOR, nullable=True)

    episode = relationship("Episode", back_populates="chunks")

    __table_args__ = (
        Index("ix_chunks_search_vector", "search_vector", postgresql_using="gin"),
    )


class TopicIndex(Base):
    __tablename__ = "topic_indexes"

    topic = Column(String(128), primary_key=True)  # e.g., product-market-fit
    title = Column(String(256), nullable=False)
    file_name = Column(String(256), nullable=False)
    count = Column(Integer, default=0)


class TopicEpisodeLink(Base):
    __tablename__ = "topic_episode_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(128), ForeignKey("topic_indexes.topic", ondelete="CASCADE"), nullable=False, index=True)
    episode_slug = Column(String(128), nullable=False, index=True)

    __table_args__ = (
        Index("ix_topic_episode_unique", "topic", "episode_slug", unique=True),
    )
