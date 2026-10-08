#!/usr/bin/env python3
"""Pull a reference post's media and measure it, before deciding what to borrow from it.

    python3 scripts/analyze_reference.py https://lnkd.in/p/XXXXXXXX --out research/ref1
    python3 scripts/analyze_reference.py some.gif --out research/ref2

For a LinkedIn URL (short lnkd.in links resolve) it reads the public post page: likes,
comments, the author's followers, the caption, and the media (an MP4 from data-sources or
the feedshare image, which LinkedIn serves as image/gif for animated posts). No login.

Writes into --out:
  summary.json   post stats, comments per 1k followers, caption, and media metrics:
                 size, frames, fps, duration, loop seam, how much of the canvas moves,
                 live cells (the gate's ambient metric) and a 0.5 s motion timeline
  sheet.jpg      20 evenly spaced frames with timestamps
  heat.png       the first frame with every area that moves in red
  media/         the downloaded file (someone else's work: study it, do not republish it)
Then look at the sheet and the heat map, and crop the moving areas to see what each does.
"""
import argparse
import html as htmlmod
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60)


def post_page(url, media_dir):
    page = fetch(url).read().decode("utf-8", "replace")
    info = {"url": url}
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        try:
            d = json.loads(m.group(1))
        except ValueError:
            continue
        if d.get("@type") not in ("SocialMediaPosting", "VideoObject"):
            continue
        st = {s.get("interactionType", "").split("/")[-1]: s.get("userInteractionCount") for s in d.get("interactionStatistic", [])}
        author = d.get("author") or {}
        fol = author.get("interactionStatistic") or {}
        if isinstance(fol, list):
            fol = next((s for s in fol if "Follow" in s.get("interactionType", "")), {})
        info.update(date=d.get("datePublished"), likes=st.get("LikeAction"), comments=st.get("CommentAction"),
                    author=author.get("name"), followers=fol.get("userInteractionCount"),
                    caption=d.get("articleBody") or d.get("text") or d.get("description") or "")
        break
    if info.get("comments") is not None and info.get("followers"):
        info["comments_per_1k_followers"] = round(info["comments"] / info["followers"] * 1000, 2)
    if info.get("caption"):
        info["caption_words"] = len(info["caption"].split())
    src = None
    for ds in re.findall(r'data-sources="([^"]+)"', page):
        try:
            src = json.loads(htmlmod.unescape(ds))[0]["src"]
            break
        except (ValueError, KeyError, IndexError):
            continue
    if not src:
        imgs = sorted(set(htmlmod.unescape(x) for x in re.findall(r'https://media\.licdn\.com/dms/image/[^"\s]+feedshare[^"\s]*', page)),
                      key=lambda u: "high-res" not in u)
        src = imgs[0] if imgs else None
    if not src:
        sys.exit("no media found on the public post page (text-only post, or the page needs a login)")
    data = fetch(src).read()
    ext = "gif" if data[:3] == b"GIF" else "mp4" if data[4:8] == b"ftyp" else "jpg" if data[:2] == b"\xff\xd8" else "png"
    media_dir.mkdir(parents=True, exist_ok=True)
    path = media_dir / f"reference.{ext}"
    path.write_bytes(data)
    return info, path


def load_frames(path):
    """RGB frames as int16 arrays plus their timestamps in seconds."""
    if path.suffix.lower() == ".gif":
        im = Image.open(path)
        out, ts, t = [], [], 0
        for i in range(getattr(im, "n_frames", 1)):
            im.seek(i)
            out.append(np.asarray(im.convert("RGB"), dtype=np.int16))
            ts.append(t / 1000)
            t += im.info.get("duration", 0) or 0
        return out, ts, t / 1000, im.info.get("loop")
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=avg_frame_rate",
                            "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout.strip()
    num, _, den = probe.partition("/")
    fps = float(num) / float(den or 1) if num else 30.0
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), f"{tmp}/f%04d.png"], check=True)
        files = sorted(Path(tmp).glob("f*.png"))
        out = [np.asarray(Image.open(f).convert("RGB"), dtype=np.int16) for f in files]
    ts = [i / fps for i in range(len(out))]
    return out, ts, len(out) / fps, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="a LinkedIn post URL or a local GIF/MP4")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if re.match(r"https?://", a.source):
        info, media = post_page(a.source, out / "media")
    else:
        info, media = {"source": a.source}, Path(a.source)

    fr, ts, dur, loop = load_frames(media)
    n = len(fr)
    h, w = fr[0].shape[:2]
    step = [0.0] + [float(np.abs(fr[i] - fr[i - 1]).mean()) for i in range(1, n)]
    from0 = [float(np.abs(f - fr[0]).mean()) for f in fr]
    heat = np.zeros((h, w))
    for i in range(1, n):
        heat += np.abs(fr[i] - fr[i - 1]).mean(axis=2)
    heat = (heat / max(heat.max(), 1e-9)) ** 0.5
    small = [np.asarray(Image.fromarray(f.astype(np.uint8)).convert("L").resize((108, 135)), dtype=np.int16) for f in fr[:: max(1, n // 40)]]
    peak = np.zeros((135, 108))
    for f in small:
        peak = np.maximum(peak, np.abs(f - small[0]))
    body = peak[:121]
    gh, gw = body.shape[0] // 8, 108 // 6
    live = sum((body[r * gh:(r + 1) * gh, c * gw:(c + 1) * gw] > 24).mean() > 0.02 for r in range(8) for c in range(6)) / 48
    timeline = []
    for s in np.arange(0, dur, 0.5):
        idx = [i for i in range(n) if s <= ts[i] < s + 0.5]
        if idx:
            timeline.append({"t": round(float(s), 1), "step_max": round(max(step[i] for i in idx), 2),
                             "from_frame1_max": round(max(from0[i] for i in idx), 2)})
    info["media"] = {
        "file": str(media), "bytes": media.stat().st_size, "mib": round(media.stat().st_size / 1048576, 2),
        "size": [w, h], "frames": n, "duration_s": round(dur, 2), "fps": round(n / dur, 1) if dur else None, "loop": loop,
        "seam_first_vs_last": round(float(np.abs(fr[-1] - fr[0]).mean()), 2),
        "canvas_moving_pct": round(float((heat > 0.25).mean() * 100), 1),
        "live_cells_pct": round(live * 100, 1),
        "never_clears": max(from0) < 6,
        "timeline": timeline,
    }
    (out / "summary.json").write_text(json.dumps(info, indent=1, ensure_ascii=False))

    base = Image.fromarray(fr[0].astype(np.uint8)).convert("L").point(lambda v: v * 0.35)
    red = Image.fromarray((heat * 255).astype(np.uint8))
    Image.merge("RGB", (Image.fromarray(np.maximum(np.asarray(base), np.asarray(red))), base, base)).save(out / "heat.png")
    idxs = [round(i * (n - 1) / 19) for i in range(20)] if n >= 20 else list(range(n))
    tw = 270
    th = int(tw * h / w)
    sheet = Image.new("RGB", (5 * tw, ((len(idxs) + 4) // 5) * (th + 22)), "white")
    d = ImageDraw.Draw(sheet)
    for k, i in enumerate(idxs):
        x, y = (k % 5) * tw, (k // 5) * (th + 22)
        sheet.paste(Image.fromarray(fr[i].astype(np.uint8)).resize((tw, th), Image.LANCZOS), (x, y + 22))
        d.text((x + 4, y + 5), f"#{i}  {ts[i]:.2f}s", fill="black")
    sheet.save(out / "sheet.jpg", quality=88)
    m = info["media"]
    print(f"{m['size'][0]}x{m['size'][1]}, {m['frames']} frames, {m['fps']} fps, {m['duration_s']} s, {m['mib']} MiB, "
          f"seam {m['seam_first_vs_last']}, moving {m['canvas_moving_pct']}%, live cells {m['live_cells_pct']}%, "
          f"{'never clears' if m['never_clears'] else 'clears and rebuilds'}")
    if info.get("comments") is not None:
        print(f"{info.get('author')}: {info['comments']} comments, {info.get('likes')} likes, "
              f"{info.get('followers')} followers ({info.get('comments_per_1k_followers')} per 1k), posted {info.get('date')}")
    print(f"wrote {out}/summary.json, sheet.jpg, heat.png")


if __name__ == "__main__":
    main()
