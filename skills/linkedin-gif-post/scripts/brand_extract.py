#!/usr/bin/env python3
"""Read a brand's colors, fonts and logo from its website, as a starting point for the graphic.

    python3 scripts/brand_extract.py https://example.com --out posts/my-post

Fetches the page and up to five of its stylesheets, then writes <out>/brand.json:
  colors   the template tokens (bg, ink, ink-2, muted, accent, accent-2, accent-3, info, ok,
           warn, card-1, card-2, cta, cta-ink), from CSS variables when the site names them
           (--bg, --ink, --accent, --primary...) and from color frequency otherwise
  palette  every hex color found, most used first, so you can fix a wrong guess by hand
  fonts    display, body and mono families; Google Fonts families are downloaded into
           <out>/brand-fonts/ from the Fontsource CDN (they are OFL, so you may bundle them)
  logo     the favicon and og:image URLs, and the wordmark (text, or an inline SVG's label)
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
           "arial", "segoe ui", "roboto", "ui-sans-serif", "ui-monospace", "menlo", "consolas", "courier new", "initial",
           "helvetica neue", "monaco", "sf mono", "sfmono-regular", "liberation mono", "courier", "apple color emoji",
           "segoe ui emoji", "segoe ui symbol", "noto color emoji", "noto sans", "ubuntu", "cantarell", "oxygen",
           "open sans", "times new roman", "georgia", "unset", "revert", "lucida console", "lucida sans typewriter",
           "dejavu sans mono", "bitstream vera sans mono", "andale mono"}


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def norm(h):
    h = h.lower().lstrip("#")
    if len(h) in (3, 4):          # #rgb or #rgba
        h = "".join(c * 2 for c in h[:3])
    elif len(h) == 5:             # a truncated match; pad rather than fail
        h = h + h[-1]
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
    links = [t for t in re.findall(r"<link[^>]+>", html, re.I) if re.search(r'rel="stylesheet"', t, re.I)]
    hrefs = [m.group(1) for t in links for m in [re.search(r'href="([^"]+)"', t)] if m]
    # the site's own CSS, wherever it is hosted (many sites serve it from a CDN); font services are read from the link itself
    for href in [h for h in hrefs if "fonts.googleapis" not in h][:5]:
        u = urllib.parse.urljoin(a.url, href)
        if u.startswith("http"):
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

    body_bg = re.search(r"(?:^|[}\s])(?:html|body)[^{]*\{[^}]*background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,6})\b", css)
    site_bg = norm(body_bg.group(1)) if body_bg else None
    named = list(dict.fromkeys(vars_.values()))
    freq = Counter(norm(h) for h in re.findall(r"#[0-9a-fA-F]{6}\b", text))
    darks = sorted([h for h in named if hls(h)[1] < 0.2], key=lambda h: -freq[h]) or [by_light[0]]
    lights = sorted([h for h in named if hls(h)[1] > 0.85], key=lambda h: -freq[h]) or [by_light[-1]]
    # the graphic is always a dark canvas (references/design.md, Canvas): the brand's darkest named color
    # becomes the canvas, its lightest the text, whatever the site's own theme is
    bg = pick_var(vars_, "bg", "background", "bg-color") if (pick_var(vars_, "bg", "background", "bg-color") or "#FFFFFF") and hls(pick_var(vars_, "bg", "background", "bg-color") or "#FFFFFF")[1] < 0.2 else darks[0]
    ink = pick_var(vars_, "ink", "fg", "foreground") if hls(pick_var(vars_, "ink", "fg", "foreground") or "#000000")[1] > 0.8 else lights[0]
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
        "ok": pick_var(vars_, "ok", "success", "green", "agents") or hue_near(0.43) or mix(accent, ink, .55),
        "warn": pick_var(vars_, "warn", "warning", "amber", "yellow") or hue_near(0.11) or accent,
        "card-1": mix(bg, accent, .12), "card-2": mix(bg, ink, .03),
        "cta": accent, "cta-ink": bg,
    }

    ICON = re.compile(r"icon|awesome|material|glyph|symbol", re.I)

    def families(stack):
        out = []
        for f in stack.split(","):
            f = re.sub(r"!important", "", f).strip().strip("'\"").strip()
            if f and f.lower() not in GENERIC and not f.startswith("var(") and not ICON.search(f):
                out.append(f)
        return out

    use = Counter()
    font_vars = {}   # custom properties that hold a font stack, by name
    for k, v in re.findall(r"--([a-zA-Z0-9_-]*font[a-zA-Z0-9_-]*)\s*:\s*([^;}]+)", text):
        if re.search(r"size|weight|height|spacing|leading|tracking|style|feature|variation", k, re.I) or re.match(r"\s*(clamp|calc|min|max|[0-9.])", v):
            continue
        fs = families(v)
        if fs:
            font_vars[k.lower()] = fs[0]
    for decl in re.findall(r"font-family\s*:\s*([^;}{]+)", text):
        m = re.match(r"\s*var\(--([a-zA-Z0-9_-]+)", decl)
        if m and m.group(1).lower() in font_vars:
            use[font_vars[m.group(1).lower()]] += 1
        for f in families(decl):
            use[f] += 1
    for f in re.findall(r"family=([A-Za-z0-9+]+)", html):
        use[f.replace("+", " ")] += 5
    fams = [f for f, _ in use.most_common()]
    def by_var(*keys):
        for x in keys:              # keys in priority order
            for k, f in font_vars.items():
                if x in k:
                    return f
        return None
    fams = list(dict.fromkeys(fams))
    hashed = [f for f in fams if re.match(r"^__|_[0-9a-f]{6,}$|Fallback", f)]
    if hashed:
        print(f"note: the site loads fonts through a framework ({', '.join(hashed[:3])}...); the real family names "
              "are hidden, so the font guess below is likely wrong. Check the site's brand page.", file=sys.stderr)
    fams = [f for f in fams if f not in hashed]
    mono = by_var("mono", "code") or next((f for f in fams if "mono" in f.lower() or "code" in f.lower()), "JetBrains Mono")
    sans = [f for f in fams if f != mono]
    h1 = re.search(r"h1[^{]*\{[^}]*font-family\s*:\s*'?([^',;}]+)", text)
    var_display, var_body = by_var("display-sans", "heading", "display"), by_var("paragraph", "body", "text")
    if not sans:
        print("note: no font family found in the site's CSS; using Inter as a placeholder. Set fonts by hand.", file=sys.stderr)
    display = var_display or (h1.group(1).strip() if h1 and h1.group(1).strip() in sans else (sans[0] if sans else "Inter"))
    body = var_body or next((f for f in sans if f != display and "mono" not in f.lower()), display)
    fonts = {}
    fdir = out / "brand-fonts"
    for role, fam in (("display", display), ("body", body), ("mono", mono)):
        base = re.sub(r"[^a-z0-9]+", "-", fam.lower()).strip("-")
        # GeistSans -> geist-sans -> geist; "Inter Variable" -> inter
        slugs = list(dict.fromkeys([base, re.sub(r"-?(variable|vf|web|display)$", "", base),
                                    re.sub(r"-?sans$", "", re.sub(r"([a-z])sans$", r"\1-sans", base))]
                                   + (["jetbrains-mono"] if role == "mono" else [])))
        files = {}
        for slug in slugs:
            for w in ((500, 600, 700) if role == "display" else (400, 500, 600, 700) if role == "body" else (500, 700)):
                url = f"https://cdn.jsdelivr.net/npm/@fontsource/{slug}@5/files/{slug}-latin-{w}-normal.woff2"
                try:
                    data = get(url, binary=True)
                    fdir.mkdir(exist_ok=True)
                    (fdir / f"{slug}-{w}.woff2").write_bytes(data)
                    files[str(w)] = f"brand-fonts/{slug}-{w}.woff2"
                except Exception:
                    pass
            if files:
                break
        if files and slug == "jetbrains-mono" and base != "jetbrains-mono":
            print(f"note: mono font {fam} could not be bundled; using JetBrains Mono", file=sys.stderr)
            fam = "JetBrains Mono"
        if files:
            try:   # the OFL text travels with the files
                (fdir / f"LICENSE-{slug}.txt").write_bytes(get(f"https://cdn.jsdelivr.net/npm/@fontsource/{slug}@5/LICENSE", binary=True))
            except Exception:
                pass
        fonts[role] = {"family": fam, "files": files}
        if not files:
            fonts[role]["missing"] = True
            print(f"note: {fam} ({role}) is not on Fontsource. If you hold a license for its files, copy the woff2 "
                  f"into {fdir} and list them under fonts.{role}.files; otherwise pick the closest open font "
                  "(references/design.md, Typography)", file=sys.stderr)

    def tag_attr(tag_re, want_re, attr):
        for t in re.findall(tag_re, html, re.I):
            if re.search(want_re, t, re.I):
                m = re.search(attr + r'="([^"]+)"', t)
                if m:
                    return m.group(1)
        return None

    if not fonts["body"]["files"] and fonts["display"]["files"]:
        print(f"note: body font {fonts['body']['family']} could not be bundled; using the display family for body text", file=sys.stderr)
        fonts["body"] = dict(fonts["display"], replaces=fonts["body"]["family"])

    fav = tag_attr(r"<link[^>]+>", r'rel="(?:shortcut )?icon"|rel="apple-touch-icon"', "href")
    og = tag_attr(r"<meta[^>]+>", r'property="og:image"', "content")
    # the site's own mark lives in its header or nav; logos further down are usually customers'
    top = re.search(r"<(header|nav)\b.*?</\1>", html, re.S | re.I)
    top = top.group(0) if top else html[: len(html) // 5]
    word = re.search(r'class="[^"]*logo[^"]*"[^>]*>\s*([^<]{1,30})<', top)
    svg_logo = re.search(r'<svg[^>]*aria-label="([^"]{1,40})"', top) or re.search(r'<a[^>]*aria-label="([^"]{1,40})"[^>]*href="/"', top)
    brand = {
        "source": a.url,
        "colors": colors,
        "palette": palette[:24],
        "css_variables": vars_,
        "fonts": fonts,
        "logo": {"favicon": (fav if fav.startswith("data:") else urllib.parse.urljoin(a.url, fav)) if fav else None,
                 "og_image": og,
                 "wordmark": word.group(1).strip() if word else (svg_logo.group(1) if svg_logo else None),
                 "inline_svg": bool(svg_logo),
                 "note": "Save the logo as an SVG or PNG file and pass it to new_animation.py --logo"},
        "site_theme": "light" if site_bg and hls(site_bg)[1] > 0.6 else "dark",
    }
    (out / "brand.json").write_text(json.dumps(brand, indent=2) + "\n")
    print(json.dumps({k: brand[k] for k in ("colors", "site_theme", "logo")}, indent=2))
    for r, v in fonts.items():
        print(f"font {r}: {v['family']} ({len(v['files'])} weights downloaded)")
    if brand["site_theme"] == "light":
        print("note: the site is light. The graphic keeps a dark canvas in the brand's darkest color, with its "
              "light color for text (references/design.md, Canvas). Check that bg and ink are brand colors.")
    print(f"wrote {out / 'brand.json'}; check it against the site before using it")


if __name__ == "__main__":
    main()
