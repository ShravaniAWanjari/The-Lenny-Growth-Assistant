# Source Validation Report

- **Validation Timestamp**: `2026-08-25T13:12:00Z`
- **Source Commit SHA**: `be8ab89a890a833cbba2c892178f823fff178c65`
- **Total Files Scanned**: `393`
- **Accepted Transcripts**: `297`
- **Accepted Topic Indexes**: `89`
- **Rejected Files**: `6`
- **Skipped Scripts (Security Invariant)**: `1` (`scripts/build-index.sh`)
- **Warnings**: `0`

---

## Documented Exclusions (6 Episodes)

The following 6 files were excluded by the strict deterministic validation pipeline:

| Episode Slug | Reason for Exclusion |
| :--- | :--- |
| `adriel-frederick` | Transcript body contains speaker names without standard `(HH:MM:SS)` timestamp format. |
| `daniel-lereya` | Frontmatter missing required `publish_date` field. |
| `nickey-skarstad` | Frontmatter missing required `youtube_url`, `video_id`, and `view_count` fields. |
| `peter-deng` | Frontmatter missing required `publish_date` field. |
| `ryan-hoover` | Transcript body contains speaker names without standard `(HH:MM:SS)` timestamp format. |
| `teaser_2021` | Non-episode trailer from 2021 missing all standard episode metadata fields. |

All 297 accepted episodes (~14,933 chunks) satisfy all schema, frontmatter, timestamp, and security invariants.
