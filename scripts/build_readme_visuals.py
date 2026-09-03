"""Generate repository-owned README artwork; requires Pillow, not app runtime."""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

def font(size, bold=False):
    candidates = [
        Path("C:/Windows/Fonts") / ("segoeuib.ttf" if bold else "segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu") / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)

frames = []
for step in range(36):
    im = Image.new("RGB", (1200, 380), "#0b1423")
    d = ImageDraw.Draw(im)
    for x in range(0, 1200, 40):
        d.line((x, 0, x, 380), fill="#111f30")
    for y in range(0, 380, 40):
        d.line((0, y, 1200, y), fill="#111f30")
    d.rounded_rectangle((20, 20, 1180, 360), radius=24, outline="#294158", width=2)
    d.text((60, 48), "ENGINEERED FOR YOUR NEXT MOVE", font=font(17, True), fill="#60dacd")
    d.text((56, 87), "JARVIS", font=font(72, True), fill="#f1f6fb")
    d.text((60, 174), "CAREER OS", font=font(28), fill="#a9bdd5")
    d.text((60, 233), "Career intelligence. Human-approved actions.", font=font(23), fill="#cfdeee")
    d.text((60, 308), "DISCOVER   /   PREPARE   /   APPROVE   /   TRACK", font=font(16, True), fill="#60dacd")
    cx, cy = 987, 180
    for radius in (65, 90, 115):
        d.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline="#304e69", width=2)
    points = [(cx+65*math.cos(a*math.pi/3-math.pi/2), cy+65*math.sin(a*math.pi/3-math.pi/2)) for a in range(6)]
    d.polygon(points, fill="#142f45", outline="#60dacd", width=3)
    d.text((cx-19, cy-36), "J", font=font(50, True), fill="#e4fcff")
    # One gentle circuit sweep, then a still final frame; no infinite flashing loop.
    angle = (step/35*300-150)*math.pi/180
    px, py = cx+90*math.cos(angle), cy+90*math.sin(angle)
    d.ellipse((px-5, py-5, px+5, py+5), fill="#60dacd")
    d.text((908, 316), "BY SYED SAUD", font=font(16, True), fill="#a9bdd5")
    frames.append(im)

frames[-1].save(OUT / "career-os-banner.png", optimize=True)
frames[0].save(OUT / "career-os-banner.gif", save_all=True, append_images=frames[1:], duration=100, optimize=True)

technologies = ["React", "Vite", "FastAPI", "Python", "PostgreSQL", "SQLite", "Docker", "NGINX", "Render"]
for name in technologies:
    width = max(90, len(name)*10+32)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="32" role="img" aria-label="{name}"><rect x=".5" y=".5" width="{width-1}" height="31" rx="8" fill="#14283d" stroke="#35516a"/><text x="{width/2}" y="21" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="600" fill="#c5f4ef">{name}</text></svg>'''
    (OUT / f"tech-{name.lower()}.svg").write_text(svg, encoding="utf-8")
print(f"Generated README visuals in {OUT}")
