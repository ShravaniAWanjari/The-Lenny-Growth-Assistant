import os

os.makedirs("frontend/assets", exist_ok=True)
os.makedirs("frontend/public/assets", exist_ok=True)

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="100%" height="100%">
  <defs>
    <radialGradient id="glow" cx="50%" cy="35%" r="60%">
      <stop offset="0%" stop-color="#1e293b" stop-opacity="0.8" />
      <stop offset="50%" stop-color="#0f172a" stop-opacity="0.95" />
      <stop offset="100%" stop-color="#070a13" stop-opacity="1" />
    </radialGradient>
    <linearGradient id="ambient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e1b4b" stop-opacity="0.4" />
      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.9" />
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#glow)" />
  <rect width="100%" height="100%" fill="url(#ambient)" />
  <g stroke="rgba(99, 102, 241, 0.08)" stroke-width="1.5" fill="none">
    <path d="M0,540 Q480,480 960,540 T1920,540" />
    <path d="M0,560 Q480,510 960,560 T1920,560" />
    <path d="M0,520 Q480,450 960,520 T1920,520" />
  </g>
</svg>"""

with open("frontend/assets/hero.jpg", "w", encoding="utf-8") as f:
    f.write(svg_content)
with open("frontend/public/assets/hero.jpg", "w", encoding="utf-8") as f:
    f.write(svg_content)
with open("frontend/assets/hero.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)
with open("frontend/public/assets/hero.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

print("Hero assets written successfully.")
