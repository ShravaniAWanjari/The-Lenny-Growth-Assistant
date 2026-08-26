---
name: artifact-html
description: Generate modern, responsive, styled HTML/CSS visual artifacts (infographics, cards, dashboards, timelines) strictly without JavaScript.
triggers:
  - "visual html"
  - "create an html"
  - "create html"
  - "generate an html"
  - "generate html"
  - "html interface"
  - "html cards"
  - "html card"
  - "turn this into a visual"
  - "html infographic"
  - "visual card"
  - "html visual"
  - "create a visual"
  - "cards showcasing"
output_type: html
---

# HTML/CSS Visual Artifact Skill

## Purpose
Transform podcast knowledge into visually appealing, modern, self-contained HTML/CSS visual components (infographic cards, comparative grids, process timelines, metric dashboards).

## Design & Styling Requirements
- Match **The Lenny Growth Assistant** website. The artifact must feel like it belongs inside the existing dark, cinematic, editorial interface—not like a generic colorful AI dashboard.
- Use this exact design-token direction in the embedded CSS:
  - page background: `#09090b`; surface: `#141416`; cards: `rgba(255,255,255,0.04)`;
  - primary text: `#f8fafc`; secondary text: `#94a3b8`; muted text: `#71717a`;
  - subtle borders: `rgba(255,255,255,0.08)` and stronger borders: `rgba(255,255,255,0.14)`;
  - restrained accents only: emerald `#10b981`, cyan `#38bdf8`, amber `#f59e0b`, and rose `#f43f5e`;
  - sans typography: `Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`;
  - editorial headings: `Newsreader, Georgia, Cambria, serif`;
  - corner radii between `10px` and `16px`, subtle glass blur, fine borders, and soft dark shadows.
- Start with a compact editorial header, then use a clear card/grid/timeline hierarchy. Prefer generous whitespace, short labels, restrained uppercase eyebrow text, readable 1.5–1.7 line height, and quiet source/footer metadata.
- Avoid bright full-page gradients, neon glows, white backgrounds, oversized dashboard chrome, cartoon styling, generic purple SaaS palettes, and excessive decoration.
- Give the root wrapper a class named `lenny-artifact` and define the design tokens as CSS custom properties on that wrapper.
- Include `box-sizing: border-box` for the artifact subtree and ensure the body/root has no default margin.
- Completely self-contained CSS embedded within `<style>` tags or inline styles.
- Responsive layout (works well on desktop and mobile viewports).
- Return one complete HTML document or one self-contained `<style>` + `<main class="lenny-artifact">...</main>` block. Do not add explanatory prose inside the HTML artifact.

## STRICT SECURITY INVARIANTS
1. **NO JAVASCRIPT**: Absolutely no `<script>` tags, inline event attributes (`onclick`, `onload`, `onerror`, `onmouseover`, etc.), or `javascript:` URLs.
2. **NO IFRAMES / EMBEDS**: No `<iframe>`, `<object>`, `<embed>`, or `<applet>`.
3. **NO EXTERNAL SCRIPTS / UNTRUSTED SOURCES**: Do not load external JavaScript libraries or unverified remote executable resources.
4. **NO UNSAFE SCHEMES**: Links must use standard `https://` or `http://` schemes only.
