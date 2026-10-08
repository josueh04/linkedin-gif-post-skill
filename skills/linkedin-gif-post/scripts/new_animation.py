#!/usr/bin/env python3
"""Start a new animated post from a template, optionally in another brand.

    python3 scripts/new_animation.py --out posts/my-post
    python3 scripts/new_animation.py --out posts/my-post --brand posts/my-post/brand.json

Writes <out>/animation/ (index.html plus fonts/) ready for HyperFrames. With --brand (a file
written by brand_extract.py, or by hand) the template's :root tokens are replaced by the
brand's colors and fonts, and the brand's font files are copied in. Then edit index.html:
change words, numbers and the logo; keep the ids and classes the timeline uses.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from _cfg import SKILL, composition

TOKENS = ["bg", "ink", "ink-2", "muted", "accent", "accent-2", "accent-3", "info", "ok", "warn", "card-1", "card-2", "cta", "cta-ink"]


def hex_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def brand_root(brand):
    c, f = brand.get("colors", {}), brand.get("fonts", {})
    lines = []
    for t in TOKENS:
        if t in c:
            lines.append(f"  --{t}:{c[t]};")
            if c[t].startswith("#"):
                lines.append(f"  --{t}-rgb:{hex_rgb(c[t])};")
    for role in ("display", "body", "mono"):
        if role in f:
            lines.append(f"  --font-{role}:'{f[role]['family']}',sans-serif;" if role != "mono" else f"  --font-mono:'{f[role]['family']}',monospace;")
    return ":root{\n" + "\n".join(lines) + "\n}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="post folder; the animation goes in <out>/animation")
    ap.add_argument("--template", default="research_bento", help="folder name under assets/templates/")
    ap.add_argument("--brand", help="brand.json from brand_extract.py")
    ap.add_argument("--force", action="store_true", help="overwrite an existing animation folder")
    a = ap.parse_args()
    src = SKILL / "assets" / "templates" / a.template
    if not (src / "index.html").exists():
        known = ", ".join(p.name for p in (SKILL / "assets" / "templates").iterdir() if p.is_dir())
        sys.exit(f"no template {a.template!r}; known: {known}")
    out = Path(a.out) / "animation"
    if out.exists() and not a.force:
        sys.exit(f"{out} exists; pass --force to overwrite")
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src, out)
    if a.brand:
        brand = json.loads(Path(a.brand).read_text())
        html = (out / "index.html").read_text()
        marker = "/* BRAND TOKENS (new_animation.py --brand replaces this block) */"
        if marker not in html:
            sys.exit("template has no BRAND TOKENS block")
        html = html.replace("</style>", "/* brand.json (new_animation.py --brand) */\n" + brand_root(brand) + "\n</style>", 1)
        (out / "index.html").write_text(html)
        bdir = Path(a.brand).resolve().parent
        faces = []
        for role, spec in brand.get("fonts", {}).items():
            for w, fname in (spec.get("files") or {}).items():
                fsrc = bdir / fname
                if fsrc.exists():
                    shutil.copy(fsrc, out / "fonts" / fsrc.name)
                    faces.append(f"@font-face{{font-family:'{spec['family']}';font-weight:{w};src:url({fsrc.name}) format('woff2')}}")
        if faces:
            with open(out / "fonts" / "fonts.css", "a") as fh:
                fh.write("\n/* brand fonts */\n" + "\n".join(faces) + "\n")
    profile, duration = composition(out / "index.html")
    (out / "hyperframes.json").write_text(json.dumps({"name": Path(a.out).name, "entry": "index.html"}, indent=2) + "\n")
    print(f"wrote {out} (template {a.template}, GIF profile {profile}, {duration:g} s)")
    print(f"next: edit {out / 'index.html'}, then python3 {Path(__file__).with_name('snapshot_sheet.py')} {out}")


if __name__ == "__main__":
    main()
