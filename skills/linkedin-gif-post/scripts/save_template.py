#!/usr/bin/env python3
"""Save a finished composition as a reusable template.

    python3 scripts/save_template.py posts/my-post/animation --name factory-line

Copies the HyperFrames project (index.html and fonts/, plus assets/ if present) into
assets/templates/<name>/ and writes a README.md stub there. Fill the stub in: the shape of
resource it fits, its zones and ids, its beat sheet, and what to change for a new post.
The brand stays as tokens, so the next post can apply its own with new_animation.py --brand.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path

from _cfg import SKILL, composition


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("animation_dir")
    ap.add_argument("--name", required=True, help="lowercase, hyphens: the resource shape it fits")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    src = Path(a.animation_dir)
    if not (src / "index.html").exists():
        sys.exit(f"no index.html in {src}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", a.name):
        sys.exit("--name: lowercase letters, digits, hyphens and underscores only")
    dest = SKILL / "assets" / "templates" / a.name
    if dest.exists() and not a.force:
        sys.exit(f"{dest} exists; pass --force to overwrite")
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    shutil.copy(src / "index.html", dest / "index.html")
    for sub in ("fonts", "assets"):
        if (src / sub).is_dir():
            shutil.copytree(src / sub, dest / sub)
    profile, duration = composition(dest / "index.html")
    (dest / "README.md").write_text(f"""# {a.name}

GIF profile `{profile}`, {duration:g} s.

## Fits

<!-- The shape of resource this composition was made for (compose.md, step 1), and the concept sentence. -->

## Zones

| Zone | Ids and classes | Content | Motion |
|---|---|---|---|

## Beats

| Time | What moves |
|---|---|

## To adapt

<!-- What to change for a new post: words, counts, the arrays the script reads, positions to keep in sync. -->
""")
    print(f"wrote {dest}; fill in {dest / 'README.md'}")


if __name__ == "__main__":
    main()
