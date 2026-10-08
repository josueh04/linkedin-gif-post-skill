#!/usr/bin/env python3
"""Render a post animation to MP4 with HyperFrames, then encode the LinkedIn GIF.

    python3 scripts/render_gif.py posts/my-post/animation

Writes next to the animation folder: graphic.mp4 (1080x1350), graphic.gif (infinite loop)
and graphic-frame.png (frame 1, the poster). The spec comes from the composition's GIF
profile (`data-gif-profile` on #root, see config.json `profiles`):
  build    720x900 at 30 fps
  ambient  1080x1350 at 15 fps (research_bento)
If the GIF is over max_bytes it retries with fewer colors, then without dithering,
then at a lower fps, then narrower, and says which setting shipped. Then run gif_gate.py.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

from _cfg import animated, composition


def run(cmd, env=None):
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if p.returncode != 0:
        sys.exit(f"failed: {' '.join(cmd[:4])} ...\n{p.stdout[-1500:]}\n{p.stderr[-1500:]}")
    return p


def encode(mp4, gif, fps, width, colors, dither="bayer:bayer_scale=4"):
    height = width * 5 // 4
    vf = (f"fps={fps},scale={width}:{height}:flags=lanczos,split[a][b];"
          f"[a]palettegen=max_colors={colors}:stats_mode=diff[p];"
          f"[b][p]paletteuse=dither={dither}:diff_mode=rectangle")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-vf", vf, "-loop", "0", str(gif)])
    return gif.stat().st_size


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("animation_dir")
    ap.add_argument("--fps", type=int)
    ap.add_argument("--skip-render", action="store_true", help="Reuse an existing graphic.mp4")
    a = ap.parse_args()
    anim = Path(a.animation_dir).resolve()
    if not (anim / "index.html").exists():
        sys.exit(f"no index.html in {anim}")
    profile, duration = composition(anim / "index.html")
    cfg = animated(profile)
    if duration and duration * int(a.fps or cfg["fps"]) > int(cfg["max_frames"]):
        sys.exit(f"{duration} s at {a.fps or cfg['fps']} fps is over {cfg['max_frames']} frames (LinkedIn's GIF limit)")
    print(f"profile {profile}: {cfg['gif_size'][0]}x{cfg['gif_size'][1]}, {cfg['fps']} fps, {duration or '?'} s")
    post = anim.parent
    mp4, gif, png = post / "graphic.mp4", post / "graphic.gif", post / "graphic-frame.png"
    fps = a.fps or int(cfg["fps"])

    if not a.skip_render:
        env = dict(os.environ, DO_NOT_TRACK="1", HYPERFRAMES_SKIP_SKILLS="1")
        env.pop("GEMINI_API_KEY", None)  # snapshot/describe would send frames to Gemini; renders never need it
        run(["npx", "-y", "hyperframes@latest", "render", str(anim), "-o", str(mp4), "--fps", str(fps), "--quiet"], env=env)
    run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-frames:v", "1", str(png)])

    width = int(cfg["gif_size"][0])
    colors = [c for c in (int(cfg["colors"]), 160, 128, 96) if c <= int(cfg["colors"])]
    slower = max(10, round(fps * 5 / 6))      # 30 -> 25, 15 -> 12
    narrower = (width * 8 // 9) // 4 * 4      # 720 -> 640, 1080 -> 960
    bayer, flat = "bayer:bayer_scale=4", "none"
    # undithered 128 colors is often smaller than dithered 96 on flat UI, and looks cleaner
    attempts = ([(fps, width, c, bayer) for c in colors] + [(fps, width, 128, flat)]
                + [(slower, width, 128, bayer), (slower, narrower, 128, bayer)])
    for f, w, c, d in attempts:
        size = encode(mp4, gif, f, w, c, d)
        print(f"gif {f} fps, {w}x{w * 5 // 4}, {c} colors, dither {d.split(':')[0]}: {size / 1048576:.2f} MiB")
        if size <= int(cfg["max_bytes"]):
            break
    else:
        sys.exit(f"still over {int(cfg['max_bytes']) / 1048576:.2f} MiB: run weight_map.py on the GIF to see which area costs, "
                 "then shrink or shorten that motion (references/design.md, Weight budget)")
    print(f"wrote {mp4}, {gif}, {png}")
    print(f"next: python3 {Path(__file__).with_name('gif_gate.py')} {gif}")


if __name__ == "__main__":
    main()
