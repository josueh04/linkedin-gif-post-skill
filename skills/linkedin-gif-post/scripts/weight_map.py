#!/usr/bin/env python3
"""Show where a GIF spends its bytes: which areas change from frame to frame, and how often.

    python3 scripts/weight_map.py posts/my-post/graphic.gif
    python3 scripts/weight_map.py <gif> --box line=60,404,1020,666 --box scorecard=60,682,580,1210

GIF frames store only the pixels that changed, so file size follows the changed-pixel count.
Prints a 4x5 grid (or your named boxes, in 1080x1350 coordinates) with each area's share of
all changes, and writes <name>-weight.png next to the GIF (graphic-weight.png for graphic.gif): the first frame with changed areas in red. The
usual culprits: a gradient that drifts over a large area, a blurred glow that pulses, an
element that moves for the whole loop (a rotating ring, a nonstop waveform).
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gif")
    ap.add_argument("--box", action="append", default=[], help="name=x0,y0,x1,y1 in 1080x1350 coordinates")
    a = ap.parse_args()
    path = Path(a.gif)
    im = Image.open(path)
    n = im.n_frames
    w, h = im.size
    acc, prev = np.zeros((h, w)), None
    for i in range(n):
        im.seek(i)
        f = np.asarray(im.convert("RGB"), dtype=np.int16)
        if prev is not None:
            acc += np.abs(f - prev).sum(axis=2) > 0
        prev = f
    acc /= max(1, n - 1)
    total = acc.sum() or 1.0
    k = w / 1080
    boxes = []
    for b in a.box:
        name, xy = b.split("=")
        x0, y0, x1, y1 = (int(int(v) * k) for v in xy.split(","))
        boxes.append((name, x0, y0, x1, y1))
    if not boxes:
        for r in range(5):
            for c in range(4):
                boxes.append((f"r{r + 1}c{c + 1}", c * w // 4, r * h // 5, (c + 1) * w // 4, (r + 1) * h // 5))
    print(f"{path.name}: {n} frames, {path.stat().st_size / 1048576:.2f} MiB, "
          f"{acc.mean() * 100:.1f}% of pixels change per frame on average")
    rows = sorted(((acc[y0:y1, x0:x1].sum() / total, acc[y0:y1, x0:x1].mean(), nm) for nm, x0, y0, x1, y1 in boxes), reverse=True)
    for share, mean, nm in rows:
        bar = "#" * int(share * 50)
        print(f"  {nm:12s} {share * 100:5.1f}% of all changes   ({mean * 100:4.1f}% of its pixels per frame)  {bar}")
    im.seek(0)
    base = np.asarray(im.convert("L"), dtype=np.float64) * 0.35
    heat = np.clip((acc / max(acc.max(), 1e-9)) ** 0.5 * 255, 0, 255)
    out = np.stack([np.maximum(base, heat), base, base], axis=2).astype(np.uint8)
    dest = path.with_name(path.stem + "-weight.png")
    Image.fromarray(out).save(dest)
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
