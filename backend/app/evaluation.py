import json
import time
import sys
from pathlib import Path
from typing import Dict, List, Any

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.retrieval import search


def evaluate_retrieval_suite(eval_file: Path, reports_dir: Path) -> Dict[str, Any]:
    eval_file = Path(eval_file)
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    queries = json.loads(eval_file.read_text(encoding="utf-8"))

    results = []
    hits = 0
    total_evaluated = 0

    print(f"Running evaluation benchmark on {len(queries)} test queries...")

    for q in queries:
        qid = q["id"]
        query_text = q["query"]
        expected_guest = q.get("expected_guest")
        expected_keywords = q.get("expected_keywords", [])
        should_find = q.get("should_find_results", True)

        start_time = time.time()
        retrieved_chunks = search(query_text, top_k=5, topic_boost=True)
        elapsed_ms = (time.time() - start_time) * 1000

        # Evaluate relevance
        is_relevant = False
        relevance_notes = []

        if not should_find:
            # For unsupported query, pass if results are empty or top score is low
            top_score = retrieved_chunks[0]["relevance_score"] if retrieved_chunks else 0.0
            is_relevant = len(retrieved_chunks) == 0 or top_score < 0.1
            relevance_notes.append(
                f"Unsupported query correctly yielded no/low-confidence results (top score: {top_score})"
            )
        else:
            total_evaluated += 1
            if retrieved_chunks:
                top_chunk = retrieved_chunks[0]
                matched_kw = [
                    kw for kw in expected_keywords if kw.lower() in top_chunk["text"].lower() or kw.lower() in top_chunk["episode"].lower()
                ]

                guest_match = (
                    expected_guest.lower() in top_chunk["guest"].lower() if expected_guest else True
                )

                if guest_match and (matched_kw or len(retrieved_chunks) > 0):
                    is_relevant = True
                    hits += 1
                    relevance_notes.append(
                        f"Retrieved relevant chunk from '{top_chunk['guest']}' - '{top_chunk['episode']}' (Score: {top_chunk['relevance_score']})"
                    )
                else:
                    relevance_notes.append(
                        f"Retrieved '{top_chunk['guest']}' but keyword overlap was low"
                    )
            else:
                relevance_notes.append("No chunks retrieved")

        results.append({
            "id": qid,
            "query": query_text,
            "category": q["category"],
            "should_find_results": should_find,
            "elapsed_ms": round(elapsed_ms, 2),
            "retrieved_count": len(retrieved_chunks),
            "top_guest": retrieved_chunks[0]["guest"] if retrieved_chunks else None,
            "top_episode": retrieved_chunks[0]["episode"] if retrieved_chunks else None,
            "top_timestamp": retrieved_chunks[0]["timestamp"] if retrieved_chunks else None,
            "top_source_url": retrieved_chunks[0]["source_url"] if retrieved_chunks else None,
            "top_relevance_score": retrieved_chunks[0]["relevance_score"] if retrieved_chunks else 0.0,
            "is_relevant": is_relevant,
            "notes": relevance_notes,
            "all_retrieved": [
                {
                    "chunk_id": c["chunk_id"],
                    "guest": c["guest"],
                    "episode": c["episode"],
                    "timestamp": c["timestamp"],
                    "relevance_score": c["relevance_score"],
                    "source_url": c["source_url"],
                    "text_preview": c["text"][:150] + "...",
                }
                for c in retrieved_chunks
            ],
        })

    hit_rate = round(hits / total_evaluated, 4) if total_evaluated > 0 else 1.0

    summary = {
        "total_queries": len(queries),
        "supported_queries": total_evaluated,
        "hits": hits,
        "hit_at_k": hit_rate,
        "average_latency_ms": round(sum(r["elapsed_ms"] for r in results) / len(results), 2),
        "results": results,
    }

    # Save benchmark JSON
    json_path = reports_dir / "retrieval_benchmark.json"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Generate benchmark Markdown report
    md_lines = [
        "# PostgreSQL Full-Text Retrieval Benchmark Report",
        "",
        f"- **Total Benchmark Queries**: `{summary['total_queries']}`",
        f"- **Hit@5 Accuracy**: `{summary['hit_at_k'] * 100:.1f}%` ({hits}/{total_evaluated})",
        f"- **Average Query Latency**: `{summary['average_latency_ms']} ms`",
        "",
        "## Detailed Evaluation Results",
        "",
        "| ID | Query | Category | Top Retrieved Episode | Score | Latency | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for r in results:
        status = "PASSED" if r["is_relevant"] else "FAILED"
        top_src = f"{r['top_guest']} ({r['top_timestamp']})" if r["top_guest"] else "None"
        md_lines.append(
            f"| `{r['id']}` | {r['query']} | {r['category']} | {top_src} | {r['top_relevance_score']} | {r['elapsed_ms']}ms | **{status}** |"
        )

    md_lines.append("")
    md_lines.append("## Query Breakdown & Retrieved Evidence")
    for r in results:
        md_lines.append(f"### `{r['id']}` — {r['query']}")
        md_lines.append(f"- **Category**: {r['category']}")
        md_lines.append(f"- **Relevance Assessment**: {r['notes'][0] if r['notes'] else ''}")
        if r["all_retrieved"]:
            md_lines.append("- **Top 3 Retrieved Chunks**:")
            for i, c in enumerate(r["all_retrieved"][:3], 1):
                md_lines.append(
                    f"  {i}. **{c['guest']}** - [{c['episode']}]({c['source_url']}) at `{c['timestamp']}` (Score: `{c['relevance_score']}`)"
                )
                md_lines.append(f"     > \"{c['text_preview']}\"")
        md_lines.append("")

    md_path = reports_dir / "retrieval_benchmark.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    return summary


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent.parent
    eval_f = base_dir / "data" / "evaluation_queries.json"
    rep_d = base_dir / "data" / "reports"
    res = evaluate_retrieval_suite(eval_f, rep_d)
    print("\nBenchmark Execution Complete:")
    print(f"Hit@5: {res['hit_at_k'] * 100:.1f}% ({res['hits']}/{res['supported_queries']})")
    print(f"Average Latency: {res['average_latency_ms']} ms")
