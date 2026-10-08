#!/usr/bin/env python3
"""Capture key moments of an animation and tile them into one contact sheet for review.

    python3 scripts/snapshot_sheet.py posts/my-post/animation
    python3 snapshot_sheet.py <dir> --at 0,0.6,1.4,2.2,3.0,3.8,4.6,5.4,7.9

Without --at it takes ten evenly spaced moments across the composition's data-duration,
ending just before the loop closes (that last tile must match the first).

Writes <post>/animation-sheet.jpg. Look at it before rendering: a beat that reads badly
in a still almost always reads badly in motion.
"""
import argparse
import glob
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from _cfg import composition


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("animation_dir")
    ap.add_argument("--at")
    a = ap.parse_args()
    anim = Path(a.animation_dir).resolve()
    if not a.at:
        dur = composition(anim / "index.html")[1] or 8.0
        a.at = ",".join(f"{t:g}" for t in [round(i * (dur - 0.1) / 9, 2) for i in range(10)])
    snaps = anim / "snapshots"
    env = dict(os.environ, DO_NOT_TRACK="1", HYPERFRAMES_SKIP_SKILLS="1")
    env.pop("GEMINI_API_KEY", None)  # keeps frames on this machine
    p = subprocess.run(["npx", "-y", "hyperframes@latest", "snapshot", str(anim), "--at", a.at, "--no-end",
                        "-o", str(snaps), "--timeout", "15000"], capture_output=True, text=True, env=env)
    if p.returncode != 0:
        sys.exit(p.stdout[-1500:] + p.stderr[-1500:])
    files = sorted(glob.glob(str(snaps / "frame-*.png")))
    if not files:
        sys.exit("no snapshots written")
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    tiles = [Image.open(f).convert("RGB").resize((300, 375), Image.LANCZOS) for f in files]
    cols = 5
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 306, rows * 405), (25, 25, 25))
    d = ImageDraw.Draw(sheet)
    for i, (f, t) in enumerate(zip(files, tiles)):
        x, y = (i % cols) * 306, (i // cols) * 405
        sheet.paste(t, (x, y + 28))
        d.text((x + 6, y + 4), f.split("-at-")[1].replace(".png", ""), fill=(255, 220, 120), font=font)
    out = anim.parent / "animation-sheet.jpg"
    sheet.save(out, quality=85)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
