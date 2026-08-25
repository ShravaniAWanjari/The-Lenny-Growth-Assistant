import json
import sys
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.orm import Session

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import engine, SessionLocal
from app.models import Base, Episode, TranscriptChunk, TopicIndex, TopicEpisodeLink


def load_processed_data_to_db(processed_dir: Path):
    processed_dir = Path(processed_dir)
    episodes_file = processed_dir / "episodes.json"
    chunks_file = processed_dir / "chunks.json"
    topics_file = processed_dir / "topics.json"

    if not episodes_file.exists() or not chunks_file.exists():
        raise FileNotFoundError(f"Processed data files missing in {processed_dir}")

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        # Clear existing records
        print("Resetting database records...")
        db.execute(text("TRUNCATE TABLE topic_episode_links, topic_indexes, transcript_chunks, episodes CASCADE;"))
        db.commit()

        # 1. Load Episodes
        print(f"Loading episodes from {episodes_file.name}...")
        episodes_data = json.loads(episodes_file.read_text(encoding="utf-8"))
        episodes = [
            Episode(
                id=d["episode_id"],
                slug=d["slug"],
                guest=d["guest"],
                title=d["title"],
                publish_date=d["publish_date"],
                youtube_url=d["youtube_url"],
                video_id=d["video_id"],
                duration=d["duration"],
                duration_seconds=d["duration_seconds"],
                view_count=d["view_count"],
                channel=d["channel"],
                description=d["description"],
                keywords=d["keywords"],
                turns_count=d["turns_count"],
                chunks_count=d["chunks_count"],
            )
            for d in episodes_data
        ]
        db.bulk_save_objects(episodes)
        db.commit()
        print(f"Successfully loaded {len(episodes)} episodes.")

        # 2. Load Topics & Links
        if topics_file.exists():
            print(f"Loading topics from {topics_file.name}...")
            topics_data = json.loads(topics_file.read_text(encoding="utf-8"))
            topic_objs = []
            link_objs = []
            for slug, t in topics_data.items():
                topic_objs.append(
                    TopicIndex(
                        topic=t["topic"],
                        title=t["title"],
                        file_name=t["file_name"],
                        count=t["count"],
                    )
                )
                for ep_slug in t["linked_episodes"]:
                    link_objs.append(
                        TopicEpisodeLink(
                            topic=t["topic"],
                            episode_slug=ep_slug,
                        )
                    )
            db.bulk_save_objects(topic_objs)
            db.bulk_save_objects(link_objs)
            db.commit()
            print(f"Loaded {len(topic_objs)} topics and {len(link_objs)} episode-topic links.")

        # 3. Load Chunks in batches
        print(f"Loading transcript chunks from {chunks_file.name}...")
        chunks_data = json.loads(chunks_file.read_text(encoding="utf-8"))
        batch_size = 1000
        total_chunks = len(chunks_data)

        for i in range(0, total_chunks, batch_size):
            batch = chunks_data[i : i + batch_size]
            chunk_objs = [
                TranscriptChunk(
                    id=c["chunk_id"],
                    episode_id=c["episode_id"],
                    episode_slug=c["episode_slug"],
                    guest=c["guest"],
                    episode_title=c["episode_title"],
                    publish_date=c["publish_date"],
                    speakers=c["speakers"],
                    timestamp_start=c["timestamp_start"],
                    timestamp_end=c["timestamp_end"],
                    start_seconds=c["start_seconds"],
                    end_seconds=c["end_seconds"],
                    text=c["text"],
                    youtube_url=c["youtube_url"],
                    video_id=c["video_id"],
                    keywords=c["keywords"],
                    word_count=c["word_count"],
                )
                for c in batch
            ]
            db.bulk_save_objects(chunk_objs)
            db.commit()
            print(f"  Inserted {min(i + batch_size, total_chunks)} / {total_chunks} chunks...")

        # 4. Generate TSVECTOR search vectors
        print("Building PostgreSQL full-text search tsvectors and GIN index...")
        db.execute(
            text(
                """
                UPDATE transcript_chunks
                SET search_vector = (
                    setweight(to_tsvector('english', coalesce(guest, '')), 'A') ||
                    setweight(to_tsvector('english', coalesce(episode_title, '')), 'B') ||
                    setweight(to_tsvector('english', coalesce(text, '')), 'C')
                );
                """
            )
        )
        db.commit()
        print("Full-text search index successfully updated!")


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    proc_dir = base_dir / "data" / "processed"
    load_processed_data_to_db(proc_dir)
