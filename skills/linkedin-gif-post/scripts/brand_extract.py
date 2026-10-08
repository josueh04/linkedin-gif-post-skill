#!/usr/bin/env python3
"""Read a brand's colors, fonts and logo from its website, as a starting point for the graphic.

    python3 scripts/brand_extract.py https://example.com --out posts/my-post

Fetches the page and up to five of its same-site stylesheets, then writes <out>/brand.json:
  colors   the template tokens (bg, ink, ink-2, muted, accent, accent-2, accent-3, info, ok,
           warn, card-1, card-2, cta, cta-ink), from CSS variables when the site names them
           (--bg, --ink, --accent, --primary...) and from color frequency otherwise
  palette  every hex color found, most used first, so you can fix a wrong guess by hand
  fonts    display, body and mono families; Google Fonts families are downloaded into
           <out>/brand-fonts/ from the Fontsource CDN (they are OFL, so you may bundle them)
  logo     the favicon and og:image URLs, and the wordmark text if the site has one
Read brand.json before using it: the guess is a draft, and the brand's own guide wins.
Then: new_animation.py --out <out> --brand <out>/brand.json
"""
import argparse
import colorsys
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
GENERIC = {"inherit", "sans-serif", "serif", "monospace", "system-ui", "-apple-system", "blinkmacsystemfont", "helvetica",
           "arial", "segoe ui", "roboto", "ui-sans-serif", "ui-monospace", "menlo", "consolas", "courier new", "initial"}


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def norm(h):
    h = h.lower().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h[:6].upper()


def hls(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hls(r, g, b)


def mix(a, b, t):
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


def pick_var(vars_, *names):
    for n in names:
        for k, v in vars_.items():
            if k == n or k.endswith("-" + n):
                return v
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    html = get(a.url)
    css = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
    host = urllib.parse.urlparse(a.url).netloc
    for href in re.findall(r'<link[^>]+rel="stylesheet"[^>]+href="([^"]+)"', html)[:5]:
        u = urllib.parse.urljoin(a.url, href)
        if urllib.parse.urlparse(u).netloc == host:
            try:
                css += "\n" + get(u)
            except Exception as e:  # a missing stylesheet should not stop the read
                print(f"skip {u}: {e}", file=sys.stderr)
    text = css + "\n" + html

    vars_ = {k.lower(): norm(v) for k, v in re.findall(r"--([a-zA-Z0-9-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\b", text)}
    palette = [c for c, _ in Counter(norm(h) for h in re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b(?![0-9a-fA-F])", text)).most_common()]
    if not palette:
        sys.exit("no hex colors found; fill brand.json by hand")
    by_light = sorted(palette, key=lambda h: hls(h)[1])
    vivid = [h for h in palette if hls(h)[2] > 0.45 and 0.25 < hls(h)[1] < 0.8]

    bg = pick_var(vars_, "bg", "background", "bg-color", "surface") or by_light[0]
    ink = pick_var(vars_, "ink", "fg", "text", "foreground") or by_light[-1]
    accent = pick_var(vars_, "accent", "primary", "brand", "acc", "brain2") or (vivid[0] if vivid else mix(ink, bg, .3))
    rest = [h for h in vivid if h not in (accent,)]

    def hue_near(target):
        cands = [h for h in rest if abs(hls(h)[0] - target) < 0.08 or abs(hls(h)[0] - target) > 0.92]
        return cands[0] if cands else None

    colors = {
        "bg": bg, "ink": ink,
        "ink-2": mix(ink, bg, .18), "muted": mix(ink, bg, .48),
        "accent": accent,
        "accent-2": pick_var(vars_, "accent-2", "secondary", "brain") or mix(accent, ink, .25),
        "accent-3": mix(accent, ink, .5),
        "info": pick_var(vars_, "info", "software", "blue") or hue_near(0.6) or mix(accent, "#5B9BFF", .6),
        "ok": pick_var(vars_, "ok", "success", "green", "agents") or hue_near(0.43) or "#3EE9A6",
        "warn": pick_var(vars_, "warn", "warning", "amber", "yellow") or hue_near(0.11) or "#F0B23E",
        "card-1": mix(bg, accent, .12), "card-2": mix(bg, ink, .03),
        "cta": accent, "cta-ink": bg,
    }

    fams = []
    for f in re.findall(r"family=([A-Za-z0-9+]+)", html):
        fams.append(f.replace("+", " "))
    for decl in re.findall(r"font-family\s*:\s*([^;}{]+)", text):
        for f in decl.split(","):
            f = f.strip().strip("'\"")
            if f and f.lower() not in GENERIC and not f.startswith("var("):
                fams.append(f)
    fams = list(dict.fromkeys(fams))
    mono = next((f for f in fams if "mono" in f.lower() or "code" in f.lower()), "JetBrains Mono")
    sans = [f for f in fams if f != mono]
    h1 = re.search(r"h1[^{]*\{[^}]*font-family\s*:\s*'?([^',;}]+)", text)
    display = h1.group(1).strip() if h1 and h1.group(1).strip() in sans else (sans[0] if sans else "Inter")
    body = next((f for f in sans if f != display), display)
    fonts = {}
    fdir = out / "brand-fonts"
    for role, fam in (("display", display), ("body", body), ("mono", mono)):
        slug = re.sub(r"[^a-z0-9]+", "-", fam.lower()).strip("-")
        files = {}
        for w in ((500, 600, 700) if role == "display" else (400, 500, 600, 700) if role == "body" else (500, 700)):
            url = f"https://cdn.jsdelivr.net/npm/@fontsource/{slug}@5/files/{slug}-latin-{w}-normal.woff2"
            try:
                data = get(url, binary=True)
                fdir.mkdir(exist_ok=True)
                (fdir / f"{slug}-{w}.woff2").write_bytes(data)
                files[str(w)] = f"brand-fonts/{slug}-{w}.woff2"
            except Exception:
                pass
        fonts[role] = {"family": fam, "files": files}
        if not files:
            print(f"note: {fam} is not on Fontsource; add its woff2 files by hand or pick another family", file=sys.stderr)

    fav = re.search(r'<link[^>]+rel="(?:shortcut )?icon"[^>]+href="([^"]+)"', html)
    og = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html)
    word = re.search(r'class="[^"]*logo[^"]*"[^>]*>\s*([^<]{1,30})<', html)
    brand = {
        "source": a.url,
        "colors": colors,
        "palette": palette[:24],
        "css_variables": vars_,
        "fonts": fonts,
        "logo": {"favicon": urllib.parse.urljoin(a.url, fav.group(1)) if fav else None,
                 "og_image": og.group(1) if og else None,
                 "wordmark": word.group(1).strip() if word else None},
        "theme": "dark" if hls(bg)[1] < 0.35 else "light",
    }
    (out / "brand.json").write_text(json.dumps(brand, indent=2) + "\n")
    print(json.dumps({k: brand[k] for k in ("colors", "theme", "logo")}, indent=2))
    print({r: (v["family"], len(v["files"])) for r, v in fonts.items()})
    if brand["theme"] == "light":
        print("note: the site is light; research_bento is a dark template. Keep a dark canvas in the brand's ink "
              "or a deep tint of its accent, and use the light color for text (references/design.md, Canvas).")
    print(f"wrote {out / 'brand.json'}; check it against the site before using it")


if __name__ == "__main__":
    main()
