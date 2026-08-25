import re
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import Episode, TranscriptChunk, TopicIndex, TopicEpisodeLink

META_STOPWORDS = {
    "what", "does", "say", "about", "how", "do", "you", "know", "when", "a", "an",
    "the", "is", "are", "of", "in", "to", "for", "and", "or", "on", "with", "from",
    "tell", "me", "lenny", "lennys", "podcast", "different", "guests", "explain",
    "write", "essay", "article", "summary", "summarize", "summarizing", "turn",
    "learned", "takeaway", "takeaways", "document", "create", "visual", "card", "cards",
    "infographic", "give", "show", "make", "piece", "ship", "30", "markdown",
    "html", "css", "points", "key", "breakdown", "perspectives", "table", "compare",
    "comparing", "interface", "modal", "code", "generating", "generate", "showcase",
    "showcasing", "discuss", "discussion", "talk", "talks", "talking", "view",
    "who", "why", "which", "where", "can", "could", "would", "should", "some",
}


GREETING_PATTERNS = [
    r"^(h+i+|h+e+y+|h+e+l+o+|h+i+e+|yo|sup|wassup|whatsup|hola|howdy|greetings|gm|ge)$",
    r"^(what'?s\s+up|what\s+is\s+up)",
    r"^how\s+(are\s+you|is\s+it\s+going|are\s+things|you\s+doing|r\s+u)",
    r"^(what|how)\s+can\s+(i|you|u)\s+(search|do|ask|help|find)",
    r"^who\s+(are\s+you|made\s+you|created\s+you|r\s+u)",
    r"^what\s+(is\s+this|stuff\s+can\s+i\s+search|topics\s+can\s+i\s+search|can\s+i\s+ask|can\s+we\s+learn)",
    r"^(good\s+morning|good\s+afternoon|good\s+evening|good\s+day)",
    r"^(thanks|thank\s+you|thx|ty|bye|goodbye|cya|see\s+ya)",
    r"^help$",
]


def is_conversational_query(query_str: str) -> bool:
    clean = query_str.strip().lower()
    clean = re.sub(r"[^\w\s]", "", clean)
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, clean):
            return True
    return False


def extract_search_terms(raw_query: str) -> Dict[str, Any]:
    """Extract domain terms, acronym expansions, and construct flexible OR tsquery."""
    tokens = re.findall(r"[a-zA-Z0-9]+", raw_query.lower())
    meaningful = [t for t in tokens if t not in META_STOPWORDS and len(t) > 1]

    expanded = list(meaningful)
    if "pmf" in tokens:
        expanded.extend(["product", "market", "fit"])
    if "mvp" in tokens or "mvps" in tokens:
        expanded.extend(["product", "prototype", "launch"])
    if "plg" in tokens:
        expanded.extend(["product", "led", "growth"])
    if "cac" in tokens or "ltv" in tokens:
        expanded.extend(["customer", "acquisition", "retention"])
    if "onboarding" in tokens:
        expanded.extend(["activation", "retention"])

    unique_terms = list(dict.fromkeys(expanded))
    clean_phrase = " ".join(meaningful) if meaningful else " ".join(tokens)
    # `to_tsquery` requires explicit operators. If a prompt consists only of
    # meta words (for example, "create a visual"), retain its tokens but still
    # form a valid OR query instead of passing a whitespace-separated phrase.
    or_tsquery = " | ".join(unique_terms) if unique_terms else " | ".join(tokens)

    return {
        "clean_phrase": clean_phrase,
        "original_terms": meaningful,
        "terms": unique_terms,
        "or_tsquery": or_tsquery,
    }


def find_matching_topics(db: Session, query_str: str) -> List[str]:
    """Finds curated topic slugs that match keywords in the query."""
    q_clean = query_str.lower()
    if "pmf" in q_clean:
        q_clean += " product market fit"
    if "mvp" in q_clean or "mvps" in q_clean:
        q_clean += " product development startup growth"
    if "burnout" in q_clean:
        q_clean += " mental health"

    topics = db.query(TopicIndex).all()
    matched_slugs = []
    for t in topics:
        topic_words = t.topic.replace("-", " ")
        if topic_words in q_clean or (len(topic_words) > 3 and all(w in q_clean for w in topic_words.split())):
            matched_slugs.append(t.topic)

    return matched_slugs


def search(
    query: str,
    top_k: int = 5,
    topic_boost: bool = True,
    db: Optional[Session] = None,
) -> List[Dict[str, Any]]:
    """
    Search Lenny's podcast transcript knowledge base using PostgreSQL full-text search,
    hybrid exact + disjunctive matching, topic index boosting, and guest entity recognition.
    """
    if not query or not query.strip() or is_conversational_query(query):
        return []

    should_close = False
    if db is None:
        db = SessionLocal()
        should_close = True

    try:
        raw_query = query.strip()
        matched_topics = find_matching_topics(db, raw_query) if topic_boost else []

        # Find guest names that match query
        guest_boost_slugs = []
        all_guests = db.query(Episode.slug, Episode.guest).all()
        q_lower = raw_query.lower()
        for slug, guest_name in all_guests:
            g_parts = guest_name.lower().split()
            if guest_name.lower() in q_lower or (len(g_parts) >= 2 and all(p in q_lower for p in g_parts)):
                guest_boost_slugs.append(slug)

        # Get episode slugs associated with matched topics
        topic_boost_episodes = set()
        if matched_topics:
            links = db.query(TopicEpisodeLink.episode_slug).filter(TopicEpisodeLink.topic.in_(matched_topics)).all()
            topic_boost_episodes = {l[0] for l in links}

        # Extract search parameters
        search_meta = extract_search_terms(raw_query)
        clean_phrase = search_meta["clean_phrase"]
        or_tsquery = search_meta["or_tsquery"]
        original_terms = search_meta["original_terms"]

        if not clean_phrase and not or_tsquery and not guest_boost_slugs:
            return []

        sql_query = text(
            """
            WITH ranked AS (
                SELECT
                    c.id AS chunk_id,
                    c.episode_id,
                    c.episode_slug,
                    c.guest,
                    c.episode_title,
                    c.speakers,
                    c.timestamp_start,
                    c.timestamp_end,
                    c.start_seconds,
                    c.text,
                    c.youtube_url,
                    c.keywords,
                    ts_rank_cd(c.search_vector, plainto_tsquery('english', :clean_phrase)) AS plain_rank,
                    ts_rank_cd(c.search_vector, to_tsquery('english', :or_tsquery)) AS or_rank
                FROM transcript_chunks c
                WHERE
                    (:clean_phrase != '' AND c.search_vector @@ plainto_tsquery('english', :clean_phrase))
                    OR (:or_tsquery != '' AND c.search_vector @@ to_tsquery('english', :or_tsquery))
                    OR (c.guest ILIKE ANY(:guest_patterns))
            )
            SELECT
                chunk_id,
                guest,
                episode_title,
                episode_slug,
                speakers,
                timestamp_start,
                timestamp_end,
                start_seconds,
                text,
                youtube_url,
                keywords,
                plain_rank,
                or_rank
            FROM ranked
            """
        )

        guest_patterns = [f"%{g}%" for g in guest_boost_slugs] if guest_boost_slugs else ["%NOT_A_GUEST%"]

        results = db.execute(
            sql_query,
            {
                "clean_phrase": clean_phrase,
                "or_tsquery": or_tsquery,
                "guest_patterns": guest_patterns,
            },
        ).fetchall()

        # Score and rank candidates
        scored_candidates = []
        for r in results:
            # A disjunctive FTS query is useful for recall, but a long query
            # should not be accepted merely because one generic term appears in
            # a transcript. Require evidence for at least two original
            # meaningful terms, unless a named guest creates an explicit match.
            searchable_text = f"{r.text or ''} {r.episode_title or ''}".lower()
            term_matches = sum(
                1 for term in original_terms
                if re.search(rf"\b{re.escape(term)}\b", searchable_text)
            )
            # Require every original content term for a non-entity query. The
            # OR query remains useful to build a candidate set, but accepting a
            # partial lexical match makes unrelated prompts appear grounded.
            # Guest-specific prompts remain eligible via their explicit boost.
            required_matches = max(1, len(original_terms))
            if r.episode_slug not in guest_boost_slugs and term_matches < required_matches:
                continue

            plain_r = float(r.plain_rank or 0.0)
            or_r = float(r.or_rank or 0.0)

            base_score = plain_r * 2.5 + or_r * 1.2

            # Topic boost
            topic_bonus = 0.40 if r.episode_slug in topic_boost_episodes else 0.0

            # Guest boost
            guest_bonus = 0.75 if r.episode_slug in guest_boost_slugs else 0.0

            total_score = base_score + topic_bonus + guest_bonus

            primary_speaker = r.speakers[0] if (r.speakers and len(r.speakers) > 0) else r.guest

            scored_candidates.append({
                "chunk_id": r.chunk_id,
                "text": r.text,
                "guest": r.guest,
                "episode": r.episode_title,
                "episode_slug": r.episode_slug,
                "speaker": primary_speaker,
                "timestamp": r.timestamp_start,
                "source_url": r.youtube_url,
                "relevance_score": round(total_score, 4),
            })

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Minimum relevance threshold: if top match is weak/unrelated, return no sources
        MIN_TOP_SCORE = 0.08
        if not scored_candidates or scored_candidates[0]["relevance_score"] < MIN_TOP_SCORE:
            return []

        return scored_candidates[:top_k]

    finally:
        if should_close and db is not None:
            db.close()
