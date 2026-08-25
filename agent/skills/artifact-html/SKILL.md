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
- Clean, premium visual design (glassmorphism/card layouts, modern typography `font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`, harmonious gradients and shadows).
- Completely self-contained CSS embedded within `<style>` tags or inline styles.
- Responsive layout (works well on desktop and mobile viewports).

## STRICT SECURITY INVARIANTS
1. **NO JAVASCRIPT**: Absolutely no `<script>` tags, inline event attributes (`onclick`, `onload`, `onerror`, `onmouseover`, etc.), or `javascript:` URLs.
2. **NO IFRAMES / EMBEDS**: No `<iframe>`, `<object>`, `<embed>`, or `<applet>`.
3. **NO EXTERNAL SCRIPTS / UNTRUSTED SOURCES**: Do not load external JavaScript libraries or unverified remote executable resources.
4. **NO UNSAFE SCHEMES**: Links must use standard `https://` or `http://` schemes only.
