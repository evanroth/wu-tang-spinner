"""Render docs/36-spinners.gif: a terminal running Claude Code, with the spinner
cycling through 36 of the spinner words, a new one every 2 seconds.

Run from the project folder (macOS; needs Pillow and ffmpeg):
    python3 tools/make_gif.py
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "36-spinners.gif"

# The 36 shown in the GIF. All must be in spinner-verbs.json.
PHRASES = [
    "Bringing da ruckus", "Bombing atomically", "Protecting ya neck",
    "Thinking first before you move", "Ruling everything around me", "Chessboxing",
    "Tick-tock, keep tickin'", "Just warming up a little bit", "Entering the 36 Chambers",
    "Making way for the merge of traffic", "Philosophizing", "Feeling like a snail in the ocean",
    "Rappinin'", "Forming like Voltron", "Finding the Tootsie Roll center",
    "Swarming", "Cooking up something marvelous", "Hypothesizing",
    "Watching your step, kid", "Dropping science", "Combining and interlocking",
    "Coming to a fork in the road", "Spelling M-E-T-H-O-D", "Programming fat bass lines",
    "Dropping mockeries", "Putting the needle to the groove", "Taking your brain on spacewarp",
    "Shadowboxing", "Pitching a no-hitter", "Thinking with logic",
    "Killa Beez on attack", "Baking the cake", "Dollar dollar billing",
    "Getting technical", "Never teaching the Wu-Tang", "The saga continues",
]

FPS = 5                      # 200 ms per frame
FRAMES_PER_PHRASE = 2 * FPS  # a new phrase every 2 seconds
SCALE = 2                    # render at 2x for sharp text on retina screens
COLS, ROWS = 76, 17

BG = "#1c1c1c"
TITLEBAR = "#2c2c2c"
TEXT = "#d6d6d6"
DIM = "#8b8b8b"
GREEN = "#7fd18b"
BLUE = "#6cb6ff"
ORANGE = "#d77757"           # Claude Code's spinner color
SHIMMER = "#f4b59c"
BORDER = "#6e6e6e"
GLYPHS = "·✢✳✶✻✽✽✻✶✳✢·"     # Claude Code's spinner cycle

menlo = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 14 * SCALE, index=0)
menlo_bold = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 14 * SCALE, index=1)
symbols = ImageFont.truetype("/System/Library/Fonts/Apple Symbols.ttf", 15 * SCALE)
title_font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 12 * SCALE, index=0)

CW = menlo.getlength("M")
LH = round(14 * SCALE * 1.5)
PAD = 18 * SCALE
BAR = 30 * SCALE
W = round(PAD * 2 + CW * COLS)
H = BAR + PAD * 2 + LH * ROWS


def put(draw, col, row, text, color=TEXT, bold=False):
    """Draw text on the character grid, one cell per character."""
    y = BAR + PAD + row * LH
    for i, ch in enumerate(text):
        x = PAD + (col + i) * CW
        font = symbols if ch in "⎿" else (menlo_bold if bold else menlo)
        dy = -2 * SCALE if font is symbols else 0
        draw.text((x, y + dy), ch, font=font, fill=color)


def frame(n):
    phrase = PHRASES[n // FRAMES_PER_PHRASE]
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Title bar
    d.rectangle([0, 0, W, BAR], fill=TITLEBAR)
    for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        cx, cy, r = (14 + i * 20) * SCALE, BAR // 2, 6 * SCALE
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    title = "my-app — claude"
    d.text(((W - d.textlength(title, font=title_font)) / 2, BAR // 2), title,
           font=title_font, fill=DIM, anchor="lm")

    put(d, 0, 0, "~/code/my-app", BLUE)
    put(d, 14, 0, "$", GREEN)
    put(d, 16, 0, "claude")
    put(d, 0, 2, "> fix the failing tests", DIM)
    put(d, 0, 4, "●", TEXT)
    put(d, 2, 4, "I'll run the test suite first to see what's failing.")
    put(d, 0, 6, "●", GREEN)
    put(d, 2, 6, "Bash", bold=True)
    put(d, 6, 6, "(npm test)")
    put(d, 2, 7, "⎿  3 failed, 41 passed", DIM)
    put(d, 0, 9, "●", TEXT)
    put(d, 2, 9, "The date parser ignores time zones. Fixing it now.")

    # Spinner line: glyph, phrase with a moving shimmer, timer
    put(d, 0, 11, GLYPHS[n % len(GLYPHS)], ORANGE)
    word = phrase + "…"
    hot = (n * 3) % (len(word) + 12) - 4
    for i, ch in enumerate(word):
        put(d, 2 + i, 11, ch, SHIMMER if abs(i - hot) <= 1 else ORANGE)
    seconds = 7 + n // FPS
    put(d, 3 + len(word), 11, f"({seconds}s · esc to interrupt)", DIM)

    # Input box (drawn as a shape: box-drawing characters leave gaps at this line height)
    top, bottom = BAR + PAD + 13 * LH + LH // 2, BAR + PAD + 15 * LH + LH // 2
    d.rounded_rectangle([PAD + CW / 2, top, PAD + (COLS - 0.5) * CW, bottom],
                        radius=6 * SCALE, outline=BORDER, width=SCALE)
    put(d, 2, 14, ">", TEXT)
    if (n // 3) % 2 == 0:  # blinking cursor
        x, y = PAD + 4 * CW, BAR + PAD + 14 * LH
        d.rectangle([x, y + 3 * SCALE, x + CW, y + LH - 3 * SCALE], fill=DIM)
    put(d, 2, 16, "? for shortcuts", DIM)
    return img


def main():
    verbs = set(json.loads((ROOT / "spinner-verbs.json").read_text())["verbs"])
    missing = [p for p in PHRASES if p not in verbs]
    assert len(PHRASES) == 36 and not missing, (len(PHRASES), missing)
    longest = max(len(p) for p in PHRASES) + 1 + 3 + len("(99s · esc to interrupt)")
    assert longest <= COLS, longest

    tmp = Path(tempfile.mkdtemp())
    try:
        for n in range(len(PHRASES) * FRAMES_PER_PHRASE):
            frame(n).save(tmp / f"f{n:04d}.png")
        OUT.parent.mkdir(exist_ok=True)
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "f%04d.png"),
            "-vf", "split[a][b];[a]palettegen=max_colors=48:stats_mode=full[p];[b][p]paletteuse=dither=none",
            "-loop", "0", str(OUT),
        ], check=True)
        frame(0).save(tmp / "first.png")
        shutil.copy(tmp / "first.png", OUT.with_name("36-spinners-poster.png"))
    finally:
        shutil.rmtree(tmp)
    print(f"Wrote {OUT.relative_to(ROOT)} ({W}x{H}, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
