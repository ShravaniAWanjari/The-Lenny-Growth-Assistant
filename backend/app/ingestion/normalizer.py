import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import yaml


def parse_timestamp_to_seconds(ts_str: str) -> int:
    """Converts (HH:MM:SS) or (MM:SS) to total seconds."""
    parts = [int(p) for p in ts_str.strip().split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return 0


def seconds_to_timestamp_str(seconds: int) -> str:
    """Converts total seconds to HH:MM:SS string."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


TS_LINE_PATTERN = re.compile(r"^(?:([^(\n]{1,60}?)\s*)?\((\d{1,2}:\d{2}(?::\d{2})?)\):\s*(.*)$")


def parse_speaker_turns(transcript_body: str, default_guest: str = "Guest") -> List[Dict[str, Any]]:
    """Extracts speaker turns with name, timestamp, seconds, and text cleanly."""
    lines = transcript_body.split("\n")
    turns = []
    current_speaker = default_guest.strip() or "Guest"
    current_ts = "00:00:00"
    current_text_lines: List[str] = []

    for line in lines:
        match = TS_LINE_PATTERN.match(line)
        if match:
            # Save previous turn if it had content
            if current_text_lines and any(l.strip() for l in current_text_lines):
                turn_text = "\n".join(current_text_lines).strip()
                turns.append({
                    "speaker": current_speaker,
                    "timestamp_str": current_ts,
                    "seconds": parse_timestamp_to_seconds(current_ts),
                    "text": turn_text,
                })

            speaker_match = match.group(1)
            if speaker_match and speaker_match.strip() and not speaker_match.strip().startswith("#"):
                current_speaker = speaker_match.strip().lstrip("#").strip()

            current_ts = match.group(2)
            current_text_lines = []
            remaining = match.group(3)
            if remaining and remaining.strip():
                current_text_lines.append(remaining.strip())
        else:
            if not line.startswith("#"):
                current_text_lines.append(line)

    if current_text_lines and any(l.strip() for l in current_text_lines):
        turns.append({
            "speaker": current_speaker,
            "timestamp_str": current_ts,
            "seconds": parse_timestamp_to_seconds(current_ts),
            "text": "\n".join(current_text_lines).strip(),
        })

    return turns


def chunk_speaker_turns(
    turns: List[Dict[str, Any]],
    episode_id: str,
    episode_slug: str,
    meta: Dict[str, Any],
    max_words_per_chunk: int = 350,
    min_words_per_chunk: int = 150,
) -> List[Dict[str, Any]]:
    """
    Groups speaker turns into semantic chunks while strictly preserving timestamps,
    speakers, and exact YouTube video deep links.
    """
    chunks = []
    if not turns:
        return chunks

    current_turns: List[Dict[str, Any]] = []
    current_word_count = 0
    chunk_index = 0

    def finalize_chunk(turns_subset: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        nonlocal chunk_index
        if not turns_subset:
            return None

        t_start = turns_subset[0]["timestamp_str"]
        sec_start = turns_subset[0]["seconds"]
        t_end = turns_subset[-1]["timestamp_str"]
        sec_end = turns_subset[-1]["seconds"]

        lines = []
        speakers = set()
        for t in turns_subset:
            speakers.add(t["speaker"])
            lines.append(f"{t['speaker']} ({t['timestamp_str']}): {t['text']}")
        chunk_text = "\n\n".join(lines)

        chunk_id = f"chunk_{episode_slug}_{chunk_index:04d}"
        chunk_index += 1

        video_id = meta.get("video_id", "")
        youtube_url = meta.get("youtube_url", "")
        timestamped_url = f"https://www.youtube.com/watch?v={video_id}&t={sec_start}" if video_id else youtube_url

        return {
            "chunk_id": chunk_id,
            "episode_id": episode_id,
            "episode_slug": episode_slug,
            "guest": meta.get("guest", ""),
            "episode_title": meta.get("title", ""),
            "publish_date": str(meta.get("publish_date", "")),
            "speakers": sorted(list(speakers)),
            "timestamp_start": t_start,
            "timestamp_end": t_end,
            "start_seconds": sec_start,
            "end_seconds": sec_end,
            "text": chunk_text,
            "youtube_url": timestamped_url,
            "video_id": video_id,
            "keywords": meta.get("keywords", []) or [],
            "word_count": len(chunk_text.split()),
        }

    for turn in turns:
        turn_words = len(turn["text"].split())
        if current_word_count + turn_words > max_words_per_chunk and current_word_count >= min_words_per_chunk:
            c = finalize_chunk(current_turns)
            if c:
                chunks.append(c)
            current_turns = [turn]
            current_word_count = turn_words
        else:
            current_turns.append(turn)
            current_word_count += turn_words

    if current_turns:
        c = finalize_chunk(current_turns)
        if c:
            chunks.append(c)

    return chunks


def process_validated_corpus(
    validated_dir: Path,
    processed_dir: Path,
    reports_dir: Path,
) -> Dict[str, Any]:
    validated_dir = Path(validated_dir)
    processed_dir = Path(processed_dir)
    reports_dir = Path(reports_dir)

    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    episodes_data = []
    all_chunks = []
    topic_data = {}

    episodes_dir = validated_dir / "episodes"
    if episodes_dir.exists():
        for ep_dir in sorted(episodes_dir.iterdir()):
            if not ep_dir.is_dir():
                continue
            transcript_file = ep_dir / "transcript.md"
            if not transcript_file.exists():
                continue

            content = transcript_file.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            if len(parts) < 3:
                continue

            fm = yaml.safe_load(parts[1])
            body = parts[2]

            slug = ep_dir.name
            episode_id = f"ep_{slug}"
            guest_name = fm.get("guest", slug.replace("-", " ").title())

            pub_date = fm.get("publish_date")
            pub_date_str = pub_date.isoformat() if isinstance(pub_date, (date, datetime)) else str(pub_date or "")

            turns = parse_speaker_turns(body, default_guest=guest_name)
            chunks = chunk_speaker_turns(turns, episode_id, slug, fm)

            episode_record = {
                "episode_id": episode_id,
                "slug": slug,
                "guest": guest_name,
                "title": fm.get("title", ""),
                "publish_date": pub_date_str,
                "youtube_url": fm.get("youtube_url", ""),
                "video_id": fm.get("video_id", ""),
                "duration": fm.get("duration", ""),
                "duration_seconds": float(fm.get("duration_seconds", 0.0) or 0.0),
                "view_count": int(fm.get("view_count", 0) or 0),
                "channel": fm.get("channel", "Lenny's Podcast"),
                "description": fm.get("description", ""),
                "keywords": fm.get("keywords", []) or [],
                "turns_count": len(turns),
                "chunks_count": len(chunks),
            }

            episodes_data.append(episode_record)
            all_chunks.extend(chunks)

    # Process topic index files
    index_dir = validated_dir / "index"
    index_link_pattern = re.compile(r"\[([^\]]+)\]\(\.\./episodes/([^/]+)/transcript\.md\)")
    if index_dir.exists():
        for f in sorted(index_dir.iterdir()):
            if f.is_file() and f.name.endswith(".md") and f.name != "README.md":
                topic_slug = f.stem
                topic_text = f.read_text(encoding="utf-8", errors="replace")
                matches = index_link_pattern.findall(topic_text)
                linked_slugs = [slug for name, slug in matches]
                topic_data[topic_slug] = {
                    "topic": topic_slug,
                    "title": topic_slug.replace("-", " ").title(),
                    "file_name": f.name,
                    "linked_episodes": linked_slugs,
                    "count": len(linked_slugs),
                }

    # Save processed JSON datasets
    (processed_dir / "episodes.json").write_text(json.dumps(episodes_data, indent=2), encoding="utf-8")
    (processed_dir / "chunks.json").write_text(json.dumps(all_chunks, indent=2), encoding="utf-8")
    (processed_dir / "topics.json").write_text(json.dumps(topic_data, indent=2), encoding="utf-8")

    # Ingestion summary report
    summary = {
        "timestamp": datetime.now().isoformat() + "Z",
        "episodes_processed": len(episodes_data),
        "total_chunks_generated": len(all_chunks),
        "average_chunks_per_episode": round(len(all_chunks) / len(episodes_data), 1) if episodes_data else 0,
        "topics_indexed": len(topic_data),
        "total_topic_episode_links": sum(t["count"] for t in topic_data.values()),
    }

    (reports_dir / "ingestion_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    md_summary = f"""# Ingestion & Normalization Summary

- **Episodes Processed**: `{summary['episodes_processed']}`
- **Total Chunks Generated**: `{summary['total_chunks_generated']}`
- **Average Chunks per Episode**: `{summary['average_chunks_per_episode']}`
- **Topics Indexed**: `{summary['topics_indexed']}`
- **Topic-Episode Links**: `{summary['total_topic_episode_links']}`
"""
    (reports_dir / "ingestion_summary.md").write_text(md_summary, encoding="utf-8")

    return summary


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    val = base_dir / "data" / "validated"
    proc = base_dir / "data" / "processed"
    rep = base_dir / "data" / "reports"

    print("Running normalization & chunking pipeline...")
    res = process_validated_corpus(val, proc, rep)
    print("Ingestion finished:")
    print(json.dumps(res, indent=2))
