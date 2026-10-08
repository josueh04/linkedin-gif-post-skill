#!/usr/bin/env python3
"""Start a new animated post from a template, optionally in another brand.

    python3 scripts/new_animation.py --out posts/my-post --template blank --profile ambient --brand posts/my-post/brand.json
    python3 scripts/new_animation.py --out posts/my-post --template research_bento --brand posts/my-post/brand.json

Writes <out>/animation/ (index.html plus fonts/) ready for HyperFrames. The default template is
`blank`: the frame only (brand tokens, header slots, CTA band), for an original composition built
with references/compose.md. --profile sets the loop family on blank: ambient (10 s) or build (8 s). With --brand (a file
written by brand_extract.py, or by hand) the brand's colors and fonts are appended as a second
:root block that overrides the template defaults, and the brand's font files and their licenses
are copied in. With --logo, the logo file replaces the text wordmark.
"""
import argparse
import json
import re
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
    ap.add_argument("--template", default="blank", help="folder name under assets/templates/ (default: blank)")
    ap.add_argument("--profile", choices=["ambient", "build"], help="loop family; sets data-gif-profile and the duration (ambient 10 s, build 8 s)")
    ap.add_argument("--brand", help="brand.json from brand_extract.py")
    ap.add_argument("--logo", help="an SVG or PNG of the brand's logo; replaces the text wordmark in #logo")
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
    if a.profile:

        cfg = __import__("_cfg").animated(a.profile)
        dur = int(cfg["loop_seconds"])
        html = (out / "index.html").read_text()
        root = re.search(r'<div[^>]*id="root"[^>]*>', html).group(0)
        tag = re.sub(r'data-gif-profile="[a-z_]+"', f'data-gif-profile="{a.profile}"', root)
        tag = re.sub(r'data-duration="[0-9.]+"', f'data-duration="{dur}"', tag)
        html = html.replace(root, tag, 1)
        html = re.sub(r'(id="scene-clip"[^>]*?)data-duration="[0-9.]+"', rf'\g<1>data-duration="{dur}"', html, count=1)
        html = re.sub(r"const END = [0-9.]+;", f"const END = {dur};", html, count=1)
        (out / "index.html").write_text(html)
    if a.brand:
        brand = json.loads(Path(a.brand).read_text())
        html = (out / "index.html").read_text()
        html = html.replace("</style>", "/* brand.json (new_animation.py --brand) */\n" + brand_root(brand) + "\n</style>", 1)
        (out / "index.html").write_text(html)
        bdir = Path(a.brand).resolve().parent
        faces, have = [], (out / "fonts" / "fonts.css").read_text()
        for role, spec in brand.get("fonts", {}).items():
            for w, fname in (spec.get("files") or {}).items():
                fsrc = bdir / fname
                face = f"@font-face{{font-family:'{spec['family']}';font-weight:{w};src:url({fsrc.name}) format('woff2')}}"
                if fsrc.exists() and fsrc.name not in have and face not in faces:
                    shutil.copy(fsrc, out / "fonts" / fsrc.name)
                    faces.append(face)
        for lic in (bdir / "brand-fonts").glob("LICENSE-*.txt") if (bdir / "brand-fonts").is_dir() else []:
            (out / "fonts" / "licenses").mkdir(exist_ok=True)
            shutil.copy(lic, out / "fonts" / "licenses" / lic.name)
        if faces:
            with open(out / "fonts" / "fonts.css", "a") as fh:
                fh.write("\n/* brand fonts (new_animation.py --brand) */\n" + "\n".join(faces) + "\n")
    if a.logo:
        src_logo = Path(a.logo)
        if not src_logo.exists() or src_logo.suffix.lower() not in (".svg", ".png", ".webp"):
            sys.exit(f"--logo must be an existing .svg, .png or .webp file: {src_logo}")
        (out / "assets").mkdir(exist_ok=True)
        shutil.copy(src_logo, out / "assets" / ("logo" + src_logo.suffix.lower()))
        html = (out / "index.html").read_text()
        html, n = re.subn(r'(<div id="logo"[^>]*>).*?(</div>)', rf'\g<1><img src="assets/logo{src_logo.suffix.lower()}" alt="logo">\g<2>', html, count=1, flags=re.S)
        if not n:
            sys.exit("template has no #logo element")
        (out / "index.html").write_text(html)
    profile, duration = composition(out / "index.html")
    (out / "hyperframes.json").write_text(json.dumps({"name": Path(a.out).name, "entry": "index.html"}, indent=2) + "\n")
    print(f"wrote {out} (template {a.template}, GIF profile {profile}, {duration:g} s)")
    guide = "references/compose.md" if a.template == "blank" else f"assets/templates/{a.template}/README.md"
    print(f"next: read {guide}, edit {out / 'index.html'}, then python3 {Path(__file__).with_name('snapshot_sheet.py')} {out}")


if __name__ == "__main__":
    main()
