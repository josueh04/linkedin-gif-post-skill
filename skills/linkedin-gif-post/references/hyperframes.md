# HyperFrames notes

HyperFrames is HeyGen's open-source (Apache-2.0) HTML-to-video renderer, tested here with v0.8.139. It runs locally through `npx hyperframes@latest` and needs Node 22+, ffmpeg, and an installed Chrome. Docs ship inside the tool: `npx hyperframes docs compositions|gsap|data-attributes|rendering`.

## Composition contract

- **The root** is `<div id="root" data-composition-id="main" data-start="0" data-duration="8" data-width="1080" data-height="1350">`.
- **Timed content** sits inside one clip, `<div id="scene-clip" class="clip" data-start="0" data-duration="8" style="position:absolute;inset:0">`. The linter warns that a clip with nested divs should be a sub-composition. The warning concerns the Studio timeline view; renders are unaffected.
- **One paused GSAP timeline** is registered as `window.__timelines["main"]` and ends with `tl.seek(0)`. GSAP loads from `https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js`.
- **Determinism:**
  - No `Math.random()` and no `Date.now()`.
  - No runtime fetches. Fonts are local: `fonts/fonts.css` with `url()` paths relative to the CSS file, not to `index.html`. The first render here fell back to a serif because of that.
- **Timeline length:** `tl.set({}, {}, END)` pins the duration (10 s for ambient loops, 8 s for build loops), matching `data-duration` on the root and on the clip.
- **GIF profile:** `data-gif-profile="ambient"` on `#root` makes `render_gif.py` and `snapshot_sheet.py` use the ambient spec. When absent, the profile is `build`.

## Commands

- `npx hyperframes lint <dir>`. Expected output: 0 errors. Warnings about the nested clip are known and harmless. `overlapping_gsap_tweens` fires on sequential tweens built in a loop, with wrong times; check the beat sheet rather than the warning. The linter does not catch tweens that end after `END`; the templates' red banner does.
- `npx hyperframes snapshot <dir> --at 0,1.4,2.2 --no-end -o <dir>/snapshots` writes PNG stills. `scripts/snapshot_sheet.py` wraps it.
- `npx hyperframes render <dir> -o out.mp4 --fps 30 --quiet` takes about 10 to 20 s for 150 frames on a laptop. `scripts/render_gif.py` wraps it.
- Render has its own `--format gif`. The scripts encode with ffmpeg instead (`palettegen=stats_mode=diff`, `paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle`) to control colors, size and fps.

## Privacy

- HyperFrames sends anonymous render telemetry. The scripts run with `DO_NOT_TRACK=1` and `HYPERFRAMES_SKIP_SKILLS=1`.
- `snapshot --describe` sends frames to Gemini when `GEMINI_API_KEY` is set. The scripts unset it.

## Gotchas that broke renders the first time

| Symptom | Cause | Fix |
|---|---|---|
| Titles render in a serif fallback | `url(fonts/...)` inside `fonts/fonts.css` resolves to `fonts/fonts/...` | Paths in a CSS file are relative to that file |
| Script error, nothing animates | Two classic scripts declared the same top-level `const` (`layers`) | Prefix timeline names (`LAYERS`) or wrap them in a block |
| A 3D stack goes flat for a moment | Opacity under 1 on a `transform-style: preserve-3d` container flattens it | Fade the children, never the 3D wrapper |
| An element flashes before its entrance | A `from()` tween renders its start state immediately | Use `fromTo(..., {immediateRender: false})` and `tl.set()` hidden states at the clear time |
| A counter never ticks | Seeking can suppress `onUpdate` callbacks | Avoid callback-driven counters; swap discrete text with `tl.set` or skip counters |
| An arc stays invisible after drawing | The element was hidden with opacity and also undrawn; the draw restored only the dash offset | Undraw only, or restore opacity in the same beat |
| ffmpeg says `Option not found` in zsh | `$h:flags` is a zsh modifier | Use `${h}`, or call ffmpeg from Python (the scripts do) |
| Rotating a single element with `rotateX(..) rotateZ(..)` gives a different look in GSAP | GSAP composes rotations in its own order | Nest wrappers: the outer one gets `rotateX`, the inner one `rotateZ` |
| `lint` fails with `gsap_non_transform_motion` on `left`/`top`/`width` | Layout properties snap to whole pixels and stutter under seek-by-frame capture | Position the element once with CSS `left`/`top`, then tween `x`/`y` (or `scaleX` with a left origin instead of `width`) |
| `lint` fails with `gsap_css_transform_conflict` | The element has a CSS `transform` and a GSAP tween on the same property | Drop the CSS transform and `gsap.set()` the start value in the script |
| A dot must follow a curve | Hand-computing points needs `onUpdate`, which seeking can skip | Load `MotionPathPlugin` from the same GSAP version (`gsap@3.14.2/dist/MotionPathPlugin.min.js`), register it, and tween `motionPath: {path, align, alignOrigin: [.5, .5], start, end}`; ride out and back so the loop closes |
| A starfield or particle field must look random but render the same every time | `Math.random()` breaks determinism | Use a seeded LCG at load: `seed = (seed * 1103515245 + 12345) % 2147483648` |

| A GSAP tween on a color token does nothing | GSAP cannot interpolate `var(--x)` | Read the token once with `getComputedStyle(document.documentElement).getPropertyValue('--x-rgb')` and tween `rgba(${v},a)` |
| An arrow or symbol renders in a fallback font | Latin font subsets often lack `→` and other symbols | Check the glyph exists, or set it in the mono, or write the word |
