# Source Repository Inspection Report

**Repository**: `https://github.com/ChatPRD/lennys-podcast-transcripts.git`  
**Cloned Location**: `data/source/lennys-podcast-transcripts`  
**Source Commit SHA**: `be8ab89a890a833cbba2c892178f823fff178c65`  
**Date Inspected**: 2026-08-25  

---

## 1. Repository Structure Overview

```text
data/source/lennys-podcast-transcripts/
├── episodes/                  # 303 episode directories
│   └── {guest-slug}/
│       └── transcript.md     # YAML frontmatter + timestamped transcript
├── index/                     # 89 files (88 topic-based index files + README.md)
│   ├── product-market-fit.md
│   ├── growth-strategy.md
│   ├── ai.md
│   └── ...
├── scripts/                   # 1 shell script
│   └── build-index.sh        # [UNEXECUTED - Security invariant]
├── CLAUDE.md
└── README.md
```

---

## 2. Quantitative Summary

| Metric | Value |
| :--- | :--- |
| **Total Episode Folders** | 303 |
| **Episodes with `transcript.md`** | 303 (100%) |
| **Missing Transcripts** | 0 |
| **Unexpected / Extra Files in Episode Folders** | 0 |
| **Topic Index Files** | 88 topics (+ 1 README.md) |
| **Total Transcript Content Size** | ~26.1 MB |
| **Min Transcript Size** | 9,260 bytes |
| **Max Transcript Size** | 159,707 bytes |
| **Average Transcript Size** | 86,330 bytes |

---

## 3. Metadata & Frontmatter Format

Every `transcript.md` begins with valid YAML frontmatter bounded by `---` delimiters.

### Discovered Frontmatter Keys:
- `guest`: Full name of the featured guest (e.g., `"Ada Chen Rekhi"`, `"Adam Fishman"`).
- `title`: Complete episode title.
- `youtube_url`: Link to the YouTube video (e.g., `https://www.youtube.com/watch?v=...`).
- `video_id`: YouTube video identifier string.
- `publish_date`: Date in `YYYY-MM-DD` format.
- `description`: Text summary and episode notes.
- `duration`: Human-readable duration (e.g., `"1:05:46"`).
- `duration_seconds`: Numeric float representing total length in seconds.
- `view_count`: Integer view count at ingestion time.
- `channel`: Channel name (`"Lenny's Podcast"`).
- `keywords`: Array of string topic tags (e.g., `["product-market fit", "growth", "retention"]`).
- Optional fields in select files: `spotify_id`, `spotify_url`.

All 303 files parsed cleanly with zero YAML syntax errors.

---

## 4. Transcript Content & Timestamp Format

The transcript body follows a standardized markdown speaker-turn pattern:

```markdown
# [Episode Title]

## Transcript

[Speaker Name] (HH:MM:SS):
[Spoken text paragraph]

Lenny (HH:MM:SS):
[Spoken text paragraph]
```

- **Timestamp syntax**: Consistent `(HH:MM:SS)` or `(MM:SS)` format immediately following speaker names.
- **Granularity**: Natural conversational turns and paragraphs.
- **Traceability**: Each paragraph can be mapped directly to a guest, timestamp, and YouTube URL with `&t=...` offset.

---

## 5. Topic Index Format

Files in `index/*.md` categorize episodes by topic and contain markdown links to the episode transcript files:

```markdown
# product market fit

Episodes discussing **product market fit**:

- [Casey Winters](../episodes/casey-winters/transcript.md)
- [Christopher Lochhead](../episodes/christopher-lochhead/transcript.md)
- [Dalton Caldwell](../episodes/dalton-caldwell/transcript.md)
```

- Topic index files allow direct metadata-based filtering and topic-assisted retrieval before/alongside full-text search.
- **Note on character encoding**: A small number of guest names in the index files contain byte-order/replacement characters (e.g., `Gustav Sderstrm` in `index/ai.md`), but the episode slugs and frontmatter in `episodes/` remain intact and cleanly parseable.

---

## 6. Security & Safety Audit

1. **Scripts in source**: The source repository contains `scripts/build-index.sh`. Under our security invariants, this script was **NOT** executed and will not be executed.
2. **Untrusted Data Isolation**: All transcript text will be treated as untrusted data and strictly sanitized/parameterized when passed into LLM prompt contexts.
3. **No Executable Code**: All 303 episode directories contain purely Markdown text files.

---

## 7. Findings & Implications for Retrieval Strategy

1. **Dataset Size**: The corpus contains 303 episodes (~26 MB total, ~3-4 million words). This is compact enough for ultra-fast in-memory indexing, BM25 / PostgreSQL full-text search with `tsvector`, or hybrid vector embeddings (e.g., sentence-transformers or Gemini embeddings).
2. **Timestamp Preservation**: Because turns are formatted with `Speaker (HH:MM:SS):`, we can chunk by conversational turn or sliding timestamp windows (e.g. 30-90 second intervals) without losing exact playback positions.
3. **Topic Index Leverage**: The 88 curated topic indexes provide an immediate metadata boost for broad topic queries (e.g., "What does Lenny say about PMF?").
