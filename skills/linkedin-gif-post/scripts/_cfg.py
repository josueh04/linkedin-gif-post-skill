"""Config for linkedin-gif-post: config.json in the skill folder, with safe defaults.

A composition chooses its GIF profile with `data-gif-profile` on #root ("build" when absent):
  build    a loop that clears and rebuilds with one big move; ships 720x900 at 30 fps
  ambient  a loop that never clears, motion lives inside the cards; ships 1080x1350 at 15 fps
`animated(profile)` returns the base settings with that profile's overrides applied.
"""
import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent

DEFAULTS = {
    "canvas": [1080, 1350],
    "gif_size": [720, 900],
    "fps": 30,
    "loop_seconds": 8,
    "max_frames": 250,       # LinkedIn Images API limit for GIFs
    "max_bytes": 4194304,    # 4 MiB: stays under the 5 MB image limit most schedulers enforce
    "max_seam_diff": 1.0,
    "colors": 192,
    "cta_band_px": 124,
    "min_motion": 2.0,
    "min_live_cells": None,
    "profiles": {
        "ambient": {"gif_size": [1080, 1350], "fps": 15, "loop_seconds": 10, "colors": 128, "min_live_cells": 0.40},
    },
}


def animated(profile=None):
    cfg = {}
    path = SKILL / "config.json"
    if path.exists():
        try:
            cfg = json.loads(path.read_text())
        except ValueError as e:
            sys.exit(f"config.json is not valid JSON: {e}")
    out = dict(DEFAULTS)
    out.update({k: v for k, v in cfg.items() if v is not None or k == "min_live_cells"})
    profiles = out.pop("profiles", {}) or {}
    # every profile's GIF size, so the gate can tell which spec a finished GIF was made for
    out["sizes"] = {"build": list(out["gif_size"])} | {k: list(v.get("gif_size", out["gif_size"])) for k, v in profiles.items()}
    out["profile"] = profile or "build"
    if profile and profile != "build":
        if profile not in profiles:
            sys.exit(f"unknown GIF profile {profile!r}; known: build, {', '.join(profiles)}")
        out.update(profiles[profile])
    return out


def composition(index_html):
    """Profile and duration a composition declares on its #root element."""
    html = Path(index_html).read_text()
    root = re.search(r'<div[^>]*id="root"[^>]*>', html)
    tag = root.group(0) if root else ""
    prof = re.search(r'data-gif-profile="([a-z_]+)"', tag)
    dur = re.search(r'data-duration="([0-9.]+)"', tag)
    return (prof.group(1) if prof else "build"), (float(dur.group(1)) if dur else None)
