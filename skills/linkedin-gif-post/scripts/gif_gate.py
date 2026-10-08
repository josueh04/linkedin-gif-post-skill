#!/usr/bin/env python3
"""Release gates for an animated post graphic.

    python3 scripts/gif_gate.py posts/my-post/graphic.gif
    python3 scripts/gif_gate.py posts/my-post/graphic.gif --profile ambient

The profile (build or ambient, config.json `profiles`) is detected from the GIF's
size unless --profile says otherwise. MOTION differs by profile: a build loop must change a
lot from frame 1; an ambient loop never clears, so it must instead keep many parts of the
canvas alive (the share of a 6x8 grid over the body that moves at some point).

Prints one PASS/FAIL line per gate and exits 1 on any FAIL. After the gates pass, open
graphic-frame.png and read the keyword character by character, exactly as for a static
graphic: no script can tell FACTORY from FACOTRY at feed size.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageStat

from _cfg import animated


def frames(im):
    out, delays = [], []
    i = 0
    while True:
        try:
            im.seek(i)
        except EOFError:
            break
        out.append(im.convert("RGB"))
        delays.append(im.info.get("duration", 0) or 0)
        i += 1
    return out, delays


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gif")
    ap.add_argument("--profile", help="build or ambient; detected from the GIF size when omitted")
    a = ap.parse_args()
    path = Path(a.gif)
    im = Image.open(path)
    fr, delays = frames(im)
    n = len(fr)
    size = path.stat().st_size
    w, h = fr[0].size
    profile = a.profile or next((k for k, v in animated()["sizes"].items() if v == [w, h]), "build")
    cfg = animated(profile)
    print(f"profile {profile}")
    loop = im.info.get("loop")
    avg_ms = sum(delays) / max(1, n)
    fps = 1000 / avg_ms if avg_ms else 0
    gray = lambda f: f.convert("L").resize((180, 225))
    seam = ImageStat.Stat(ImageChops.difference(gray(fr[0]), gray(fr[-1]))).mean[0]
    motion = max(ImageStat.Stat(ImageChops.difference(gray(fr[0]), gray(f))).mean[0] for f in fr[:: max(1, n // 24)])
    # ambient: how much of the body (above the CTA band) moves at some point in the loop
    small = [np.asarray(f.convert("L").resize((108, 135)), dtype=np.int16) for f in fr[:: max(1, n // 40)]]
    peak = np.zeros((135, 108))
    for f in small:
        peak = np.maximum(peak, np.abs(f - small[0]))
    body = peak[: int(135 * (1 - cfg["cta_band_px"] / cfg["canvas"][1]))]
    gh, gw = body.shape[0] // 8, 108 // 6
    live = sum((body[r * gh:(r + 1) * gh, c * gw:(c + 1) * gw] > 24).mean() > 0.02 for r in range(8) for c in range(6)) / 48
    # CTA band: the strips above and below the keyword (the bottom cta_band_px of the canvas) are
    # one flat color, the same at the top and bottom of the band, and clearly different from the
    # body just above it.
    L = fr[0].convert("L")
    top = int(h * (1 - cfg["cta_band_px"] / cfg["canvas"][1]))
    s_top = ImageStat.Stat(L.crop((0, top + 4, w, top + 10)))
    s_bot = ImageStat.Stat(L.crop((0, h - 8, w, h - 2)))
    s_body = ImageStat.Stat(L.crop((0, top - int(h * 0.07), w, top - int(h * 0.01))))
    flat = max(s_top.stddev[0], s_bot.stddev[0])
    same = abs(s_top.mean[0] - s_bot.mean[0])
    contrast = abs((s_top.mean[0] + s_bot.mean[0]) / 2 - s_body.mean[0])
    band_ok = flat <= 6 and same <= 8 and contrast >= 30

    gates = [
        ("FRAMES", n <= int(cfg["max_frames"]), f"{n} frames (max {cfg['max_frames']}, LinkedIn Images API)"),
        ("BYTES", size <= int(cfg["max_bytes"]), f"{size / 1048576:.2f} MiB (max {int(cfg['max_bytes']) / 1048576:.2f} MiB, config max_bytes)"),
        ("SIZE", [w, h] == list(cfg["gif_size"]), f"{w}x{h} (want {cfg['gif_size'][0]}x{cfg['gif_size'][1]})"),
        ("LOOP", loop == 0, f"loop flag {loop} (0 = forever)"),
        ("FPS", abs(fps - float(cfg["fps"])) <= 0.2 * float(cfg["fps"]) + 0.5, f"{fps:.1f} fps average (target {cfg['fps']})"),
        ("SEAM", seam <= float(cfg["max_seam_diff"]), f"first vs last frame diff {seam:.2f} (max {cfg['max_seam_diff']})"),
        ("MOTION", motion >= float(cfg["min_motion"]), f"largest change from frame 1 is {motion:.1f}, min {cfg['min_motion']} (a GIF that barely moves is a static post)")
        if not cfg.get("min_live_cells") else
        ("MOTION", live >= float(cfg["min_live_cells"]), f"{live:.0%} of the body moves at some point, min {float(cfg['min_live_cells']):.0%} (an ambient loop with few live parts reads as static)"),
        ("BAND", band_ok, f"CTA band flat (std {flat:.1f}, max 6), even (top vs bottom {same:.1f}, max 8), stands out (vs body {contrast:.0f}, min 30)"),
    ]
    failed = False
    for name, ok, msg in gates:
        print(f"{'PASS' if ok else 'FAIL'}  {name:6s} {msg}")
        failed |= not ok
    print("then: open graphic-frame.png and read the CTA letter by letter")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
