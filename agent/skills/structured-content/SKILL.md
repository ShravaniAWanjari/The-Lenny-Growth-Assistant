---
name: structured-content
description: Generate structured summaries, bulleted key takeaways, and multi-perspective comparison tables.
triggers:
  - "key takeaways"
  - "key points"
  - "summarize"
  - "summary"
  - "comparison table"
  - "compare guests"
  - "compare perspectives"
  - "structured breakdown"
output_type: structured_content
---

# Structured Content Generation Skill

## Purpose
Extract and synthesize knowledge from Lenny's Podcast into clear, structured takeaways, executive summaries, or multi-guest comparison tables.

## Output Formats
1. **Summary (`type: "summary"`)**:
   - Executive overview of the central topic.
   - Core thesis and background.
2. **Key Points (`type: "key_points"`)**:
   - Numbered or bulleted actionable takeaways.
   - Attributed to the specific guest/expert.
3. **Comparison (`type: "comparison"`)**:
   - Markdown table comparing guest perspectives, methodologies, or approaches side-by-side.
   - Columns: `Guest / Company`, `Core Philosophy / Approach`, `Key Metric or Signal`, `Example / Quote`.

## Invariants
- Ground strictly in retrieved podcast transcripts.
- Explicitly credit speaker perspectives.
