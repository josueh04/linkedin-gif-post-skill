---
name: linkedin-gif-post
description: Make a LinkedIn post that promotes a resource (a research piece, a guide, a checklist, a playbook) as an animated GIF plus a rewritten caption. It reads the resource and the brand's website, designs an original composition for that resource (its own concept, layout and motion, not a template with the words swapped) in the brand's colors and fonts, animates it with GSAP, renders it locally with HeyGen HyperFrames into a seamless loop (1080x1350, 15 fps, 10 s), and gates it against LinkedIn's 250-frame GIF limit and a 4 MiB file budget. Use this skill whenever someone wants a LinkedIn post graphic, a GIF or animation for a post, a "more premium" or "more dynamic" image, more engagement on a post that shares a document or lead magnet, or a rewrite of a LinkedIn caption that links to a resource, even if they only say "make my post better" or "make the graphic".
---

# linkedin-gif-post

One looping GIF and one caption for a LinkedIn post that shares a resource. The GIF shows what the resource contains, as a living system in the brand's look; the caption gives the value in the preview and points at the resource.

The GIF is composed for the resource. A resource's shape (a process, a checklist, a transformation, a comparison...) decides the picture, so each post gets its own concept, layout and motion. Templates are optional: worked examples to learn technique from, and a shortcut when a new resource has exactly the shape of an old one.

Why it works: high-performing lead-magnet posts in a 2026 study were all animated, previewed the resource as a dense working system, and mirrored that system in a numbered list in the caption. `references/evidence.md` has the numbers.

## What you produce

All files go in one post folder, for example `posts/<slug>/`:

| File | What it is |
|---|---|
| `brand.json`, `brand-fonts/` | The brand's colors, fonts and logo, read from its website |
| `animation/` | The HyperFrames project: `index.html` and `fonts/` |
| `graphic.mp4` | 1080x1350 render |
| `graphic.gif` | 1080x1350, 15 fps, 10 s, 250 frames max, 4 MiB max, infinite loop. This is what ships |
| `graphic-frame.png` | Frame 1. It is the poster LinkedIn shows before autoplay, so it is the finished composition |
| `animation-sheet.jpg` | Ten moments of the loop, for review (the stills go in `.snapshots/`) |
| `graphic-weight.png` | Only when you run `weight_map.py`: the areas that cost the most bytes |
| `caption.md` | The post text |

## Requirements

Node 22+ (for `npx hyperframes@latest`), ffmpeg, Google Chrome, Python 3.9+ with Pillow and numpy (`pip install pillow numpy`). Everything renders locally. Scripts live in `scripts/`; run them from the skill folder or with their full path.

## Workflow

1. **Read the resource.** Open the document or page the post shares. Write down:
   - the promise, in one line, for the reader ("know whether a pipeline verifies as much as it produces");
   - the count that sums it up (14 checks, 7 prompts, 5 steps);
   - the method as 4 to 6 named steps or groups;
   - the 3 or 4 strongest numbers, each with its source and date. If the resource has few numbers, take its strongest concrete facts instead: counts, named steps, short quotes, definitions.

   Anything not in the resource does not go on the canvas or in the caption.

2. **Read the brand.**
   ```bash
   python3 scripts/brand_extract.py https://brand-site.com --out posts/<slug>
   ```
   Open `brand.json` and compare it with the site. Fix any wrong guess by hand (the accent is the most common miss). The site's own brand guide, if it has one, wins.

3. **Design the composition** with `references/compose.md`. Do this before touching code:
   - name the resource's shape and write the concept sentence: "[something concrete] travels or transforms [through what] and becomes [the outcome]";
   - choose the loop family: ambient (never clears, 10 s) or build (clears and rebuilds with one big move, 8 s);
   - sketch the zones with coordinates, holding the resource's real words and numbers;
   - write the beat sheet: one narrative thread, and a different motion type per supporting zone.

   Only use an existing template when the resource has the same shape it was made for. Each template's `README.md` says which shape that is.

4. **Build it.**
   ```bash
   python3 scripts/new_animation.py --out posts/<slug> --template blank --profile ambient --brand posts/<slug>/brand.json
   ```
   `blank` gives the frame only: the brand tokens, the header slots, the CTA band and an empty `#body`. Add `--logo path/to/logo.svg` to use the brand's logo file in place of the text wordmark. Write the zones and the timeline from your beat sheet, using the motion library in `compose.md`. The header can move; the CTA band stays at the bottom. Pick the CTA mode in `references/copy.md`. Run `npx hyperframes lint posts/<slug>/animation` until it shows 0 errors. `references/hyperframes.md` lists the gotchas.

5. **Review the motion before rendering.**
   ```bash
   python3 scripts/snapshot_sheet.py posts/<slug>/animation
   ```
   Open `animation-sheet.jpg` and look at it as a stranger scrolling by. Check five things:
   - the concept sentence is visible in a still;
   - the title, the value line and the CTA read at phone size;
   - nothing collides or overflows;
   - every zone shows something specific from the resource;
   - the first and last tiles match.

   Fix and repeat until all five hold. A composition rarely works on the first pass. Plan two or three rounds.

6. **Render, then gate.**
   ```bash
   python3 scripts/render_gif.py posts/<slug>/animation
   python3 scripts/gif_gate.py posts/<slug>/graphic.gif
   ```
   The gates are FRAMES, BYTES, SIZE, LOOP, FPS, SEAM, MOTION and BAND, and all must pass. Then open `graphic-frame.png` and read the CTA letter by letter.
   - **If the GIF is too heavy,** `render_gif.py` steps down colors, dithering, fps and width on its own. If it still fails, run `scripts/weight_map.py` on the GIF to see which area costs, then shrink or shorten that motion (`references/design.md`, Weight budget).

   Show the user the sheet or the GIF and ask what feels off: the gates cover mechanics, not taste. If they like it, save it for next time with `python3 scripts/save_template.py posts/<slug>/animation --name <shape>`, and fill in the README that the script starts.

7. **Write the caption** with `references/copy.md` and save it as `caption.md`. The caption's numbered list follows the same steps, in the same order, as the cards.

8. **Publish and check.**
   - Upload `graphic.gif` as an image, natively or through a scheduler. Never convert it to JPEG or "optimize" it; that freezes it.
   - After it goes live, open the post: the media should animate.
   - If you republish an old post with the new graphic, post it as new rather than editing, because an edited post does not get a second run in the feed.

To learn from someone else's post first, run:
```bash
python3 scripts/analyze_reference.py <post-url> --out research/ref1
```
It writes stats, a frame sheet and a motion heat map. Borrow the principle, never the layout, palette or CTA shape.

## The rules, and why

- **Frame 1 and the last frame are the finished composition.** LinkedIn shows frame 1 before the GIF plays, and a loop that starts and ends on the same picture has no visible cut. Ambient loops never clear: motion highlights, travels or breathes, but never removes content.
- **The header says what the reader gets, not only the topic.** That means a title with the count, a value line with the outcome, and an INSIDE line listing what the resource contains, counted from the resource. A header that only names the audience leaves the reader guessing what is on offer.
- **An original concept per post, not a reskin.** Two posts that share a layout look like the same post in the feed. Start from the resource's shape, and borrow only technique from templates and references.
- **One chart per card, each moving its own way:** a token traveling a line, a scan down a checklist, bars called out in turn, a grid that pulses. Variety reads as premium; lists and highlights alone read as boring.
- **The text that carries meaning must read in the feed:** 22 px or more for card titles, and 16 px or more for labels, at 1080 px wide. Dense details inside cards can be texture. That density is the curiosity gap.
- **Honest content only.** Every number on the canvas comes from the resource, with its source on the card. Never invent clients, revenue, bookings or results.
- **The brand, big.** Use the logo or wordmark, the brand's own colors, and the brand's own fonts (bundled locally). The CTA band uses the brand's main accent.
- **The CTA is one line, in a full-width band at the bottom,** where it sits right above LinkedIn's Like, Comment and Share bar. Leave out "for free" and similar bait phrases, which make the image read as engagement bait.
- **1080x1350 at 15 fps, 10 s, 4 MiB or less.**
  - LinkedIn's Images API caps a GIF at 250 frames.
  - Most schedulers cap images at 5 MB.
  - 4:5 takes the most feed height LinkedIn allows for an image.
  - All the numbers live in `config.json`.

## References

- `references/compose.md`: how to design an original composition, from the resource's shape to a concept, a layout, a beat sheet and code, plus a library of seek-safe motion patterns. Read it first.
- `assets/templates/*/README.md`: each saved template, with the shape it fits, its zones and its beats. `blank` is the frame only; `research_bento` is a worked example for a checklist-plus-data research post.
- `references/design.md`: canvas, header, cards, motion grammar, CTA band, weight budget, and the never list.
- `references/copy.md`: caption structure, the two CTA modes, and a worked before and after.
- `references/hyperframes.md`: the composition contract, commands, privacy, and gotchas that broke renders.
- `references/evidence.md`: the study behind the rules.
