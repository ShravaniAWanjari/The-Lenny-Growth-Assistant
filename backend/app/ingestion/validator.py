import os
import json
import re
import shutil
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import yaml

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB limit per transcript
REQUIRED_FRONTMATTER_FIELDS = [
    "guest",
    "title",
    "youtube_url",
    "video_id",
    "publish_date",
    "description",
    "duration",
    "duration_seconds",
    "view_count",
    "channel",
    "keywords",
]

TIMESTAMP_PATTERN = re.compile(r"^\s*([^(\n]+?)\s*\((\d{1,2}:\d{2}(?::\d{2})?)\):", re.MULTILINE)
INDEX_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(\.\./episodes/([^/]+)/transcript\.md\)")


def validate_frontmatter(fm: Any, file_path: str) -> Tuple[bool, List[str]]:
    errors = []
    if not isinstance(fm, dict):
        return False, ["Frontmatter is not a valid YAML dictionary"]

    for field in REQUIRED_FRONTMATTER_FIELDS:
        if field not in fm or fm[field] is None:
            errors.append(f"Missing required field: '{field}'")

    if "publish_date" in fm and fm["publish_date"] is not None:
        val = fm["publish_date"]
        if not isinstance(val, (date, datetime, str)):
            errors.append(f"Invalid publish_date type: {type(val).__name__}")
        elif isinstance(val, str):
            try:
                datetime.fromisoformat(val.replace("Z", "+00:00"))
            except Exception:
                errors.append(f"Unparseable publish_date string: '{val}'")

    if "duration_seconds" in fm and fm["duration_seconds"] is not None:
        try:
            sec = float(fm["duration_seconds"])
            if sec < 0:
                errors.append(f"duration_seconds must be non-negative, got {sec}")
        except (ValueError, TypeError):
            errors.append(f"duration_seconds is not a valid number: {fm['duration_seconds']}")

    if "view_count" in fm and fm["view_count"] is not None:
        try:
            vc = int(fm["view_count"])
            if vc < 0:
                errors.append(f"view_count must be non-negative, got {vc}")
        except (ValueError, TypeError):
            errors.append(f"view_count is not a valid integer: {fm['view_count']}")

    if "keywords" in fm and fm["keywords"] is not None:
        if not isinstance(fm["keywords"], list):
            errors.append(f"keywords must be a list, got {type(fm['keywords']).__name__}")

    return len(errors) == 0, errors


def validate_transcript_body(body: str, file_path: str) -> Tuple[bool, List[str]]:
    errors = []
    stripped = body.strip()
    if not stripped:
        return False, ["Transcript body is empty"]

    timestamps = TIMESTAMP_PATTERN.findall(body)
    if not timestamps:
        errors.append("No timestamped speaker turns found in transcript body")

    return len(errors) == 0, errors


def run_validation(
    source_dir: Path,
    validated_dir: Path,
    reports_dir: Path,
    commit_sha: str = "be8ab89a890a833cbba2c892178f823fff178c65",
) -> Dict[str, Any]:
    source_dir = Path(source_dir)
    validated_dir = Path(validated_dir)
    reports_dir = Path(reports_dir)

    validated_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    report: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source_commit": commit_sha,
        "summary": {
            "total_scanned": 0,
            "accepted_transcripts": 0,
            "accepted_indexes": 0,
            "rejected_files": 0,
            "skipped_scripts_or_executables": 0,
            "warnings_count": 0,
        },
        "accepted_transcripts": [],
        "accepted_indexes": [],
        "rejected": [],
        "skipped": [],
        "warnings": [],
    }

    discovered_episode_slugs = set()

    # 1. Scan and validate all episode transcripts
    episodes_source = source_dir / "episodes"
    if episodes_source.exists():
        for ep_dir in sorted(episodes_source.iterdir()):
            if not ep_dir.is_dir():
                continue

            slug = ep_dir.name
            discovered_episode_slugs.add(slug)

            for file in ep_dir.iterdir():
                report["summary"]["total_scanned"] += 1
                rel_path = str(file.relative_to(source_dir))

                if file.name != "transcript.md":
                    report["rejected"].append({
                        "file": rel_path,
                        "reason": "Unexpected file in episode directory",
                    })
                    report["summary"]["rejected_files"] += 1
                    continue

                # Check file size
                file_size = file.stat().st_size
                if file_size > MAX_FILE_SIZE_BYTES:
                    report["rejected"].append({
                        "file": rel_path,
                        "reason": f"File size ({file_size} bytes) exceeds limit ({MAX_FILE_SIZE_BYTES} bytes)",
                    })
                    report["summary"]["rejected_files"] += 1
                    continue

                # Read and parse
                try:
                    content = file.read_text(encoding="utf-8")
                except Exception as ex:
                    report["rejected"].append({
                        "file": rel_path,
                        "reason": f"Encoding error reading file: {str(ex)}",
                    })
                    report["summary"]["rejected_files"] += 1
                    continue

                if not content.startswith("---"):
                    report["rejected"].append({
                        "file": rel_path,
                        "reason": "File does not start with YAML frontmatter delimiter '---'",
                    })
                    report["summary"]["rejected_files"] += 1
                    continue

                parts = content.split("---", 2)
                if len(parts) < 3:
                    report["rejected"].append({
                        "file": rel_path,
                        "reason": "Malformed frontmatter delimiters",
                    })
                    report["summary"]["rejected_files"] += 1
                    continue

                try:
                    fm = yaml.safe_load(parts[1])
                except Exception as ex:
                    report["rejected"].append({
                        "file": rel_path,
                        "reason": f"YAML parse error: {str(ex)}",
                    })
                    report["summary"]["rejected_files"] += 1
                    continue

                fm_valid, fm_errors = validate_frontmatter(fm, rel_path)
                body_valid, body_errors = validate_transcript_body(parts[2], rel_path)

                if not fm_valid or not body_valid:
                    report["rejected"].append({
                        "file": rel_path,
                        "errors": fm_errors + body_errors,
                    })
                    report["summary"]["rejected_files"] += 1
                    continue

                # Copy to validated destination
                target_ep_dir = validated_dir / "episodes" / slug
                target_ep_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, target_ep_dir / "transcript.md")

                report["accepted_transcripts"].append({
                    "slug": slug,
                    "guest": fm.get("guest"),
                    "title": fm.get("title"),
                    "video_id": fm.get("video_id"),
                    "publish_date": str(fm.get("publish_date")),
                    "size_bytes": file_size,
                })
                report["summary"]["accepted_transcripts"] += 1

    # 2. Scan and validate topic index files
    index_source = source_dir / "index"
    if index_source.exists():
        for file in sorted(index_source.iterdir()):
            if not file.is_file():
                continue

            report["summary"]["total_scanned"] += 1
            rel_path = str(file.relative_to(source_dir))

            if not file.name.endswith(".md"):
                report["rejected"].append({
                    "file": rel_path,
                    "reason": "Non-markdown file in index directory",
                })
                report["summary"]["rejected_files"] += 1
                continue

            try:
                content = file.read_text(encoding="utf-8", errors="replace")
            except Exception as ex:
                report["rejected"].append({
                    "file": rel_path,
                    "reason": f"Error reading index file: {str(ex)}",
                })
                report["summary"]["rejected_files"] += 1
                continue

            # Validate links in topic files (except README.md)
            if file.name != "README.md":
                links = INDEX_LINK_PATTERN.findall(content)
                broken_links = []
                for guest_name, ref_slug in links:
                    if ref_slug not in discovered_episode_slugs:
                        broken_links.append(ref_slug)

                if broken_links:
                    report["warnings"].append({
                        "file": rel_path,
                        "warning": f"Index links reference non-existent episode slugs: {broken_links}",
                    })
                    report["summary"]["warnings_count"] += 1

            # Copy validated index file
            target_index_dir = validated_dir / "index"
            target_index_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, target_index_dir / file.name)

            report["accepted_indexes"].append({
                "file_name": file.name,
                "topic": file.stem,
                "size_bytes": file.stat().st_size,
            })
            report["summary"]["accepted_indexes"] += 1

    # 3. Check for scripts / executables and record as skipped
    scripts_source = source_dir / "scripts"
    if scripts_source.exists():
        for file in scripts_source.iterdir():
            report["summary"]["total_scanned"] += 1
            rel_path = str(file.relative_to(source_dir))
            report["skipped"].append({
                "file": rel_path,
                "reason": "Executable / shell script skipped per security policy (NEVER executed)",
            })
            report["summary"]["skipped_scripts_or_executables"] += 1

    # Write report JSON
    report_json_path = reports_dir / "validation_report.json"
    report_json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Write report Markdown
    report_md_path = reports_dir / "validation_report.md"
    md_content = f"""# Source Validation Report

- **Validation Timestamp**: `{report['timestamp']}`
- **Source Commit SHA**: `{report['source_commit']}`
- **Total Files Scanned**: `{report['summary']['total_scanned']}`
- **Accepted Transcripts**: `{report['summary']['accepted_transcripts']}`
- **Accepted Topic Indexes**: `{report['summary']['accepted_indexes']}`
- **Rejected Files**: `{report['summary']['rejected_files']}`
- **Skipped Scripts**: `{report['summary']['skipped_scripts_or_executables']}`
- **Warnings**: `{report['summary']['warnings_count']}`

## Result
Validation Status: **{"PASSED" if report['summary']['rejected_files'] == 0 and report['summary']['accepted_transcripts'] > 0 else "FAILED"}**
"""
    report_md_path.write_text(md_content, encoding="utf-8")

    return report


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    src = base_dir / "data" / "source" / "lennys-podcast-transcripts"
    val = base_dir / "data" / "validated"
    rep = base_dir / "data" / "reports"

    print("Running validation pipeline...")
    res = run_validation(src, val, rep)
    print("Validation finished. Summary:")
    print(json.dumps(res["summary"], indent=2))
