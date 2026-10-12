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
| `graphic.gif` | Ambient loop: 1080x1350, 15 fps, 10 s. Build loop: 720x900, 30 fps, 8 s. Both: 250 frames max, 4 MiB max, infinite loop. This is what ships |
| `graphic-frame.png` | Frame 1. It is the poster LinkedIn shows before autoplay, so it is the finished composition |
| `animation-sheet.jpg` | Ten moments of the loop, for review (the stills go in `.snapshots/`, which you can delete after) |
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

   Then write the **outcome story** in one line: how the reader gets the result they care about, with the tool or method doing its one job inside it. For a post about getting clients on LinkedIn that is a chain like "a post gets comments, the tool sorts them, the best one gets a DM, the call gets booked". The GIF tells this story; the resource's own parts (its prompts, templates, scripts) appear only in the header's INSIDE line. A GIF that illustrates the resource's internals (a scoring floor, an orbit of steps) reads as abstract, and people scroll past it. A GIF that shows their own world (their post, their inbox, their calendar) with the tool in it makes them want the resource.

2. **Look at the subject as it really is.** When the post is about a product (a model, an agent, an app), open its launch page and docs and look at its real interface, mascot and mark before you draw anything. Draw your own version in that style: if the product's agents are fuzzy characters in a light chat UI, a glowing orb on black is wrong, however good it looks. Never paste the vendor's screenshots into the graphic.

   Collect the official marks as vectors: the vendor's favicon SVG or its brand page, never a traced PNG. For LinkedIn, use the bundled `assets/marks/linkedin-in.svg`, the classic square "in". Never type "in" in a font or redraw it by eye.

3. **Read the brand.** Whose brand? The person posting, if they have one. When a personal account posts about someone else's product and has no brand of its own, the subject leads: its official marks and its colors, so the topic reads in under a second. Never use the subject's wordmark or layout in a way that makes the post look like it came from that company.
   ```bash
   python3 scripts/brand_extract.py https://brand-site.com --out posts/<slug>
   ```
   If the site blocks the script (some return 403), read it in a browser, or the product's launch page, and write `brand.json` by hand. Open `brand.json` and compare it with the site. Fix any wrong guess by hand (the accent is the most common miss). The site's own brand guide, if it has one, wins.

4. **Design the composition** with `references/compose.md`. Do this before touching code:
   - write the concept sentence from the outcome story: "[something from the reader's world] travels or transforms [through the tool] and becomes [the outcome they want]". Use the resource's shape (process, checklist, comparison...) to choose the motion, not to replace the story;
   - choose the loop family: ambient (never clears, 10 s) or build (clears and rebuilds with one big move, 8 s);
   - sketch the zones with coordinates, holding the resource's real words and numbers;
   - write the beat sheet: one narrative thread, and a different motion type per supporting zone.

   Only use an existing template when the resource has the same shape it was made for. Each template's `README.md` says which shape that is.

5. **Build it.**
   ```bash
   python3 scripts/new_animation.py --out posts/<slug> --template blank --profile ambient --brand posts/<slug>/brand.json
   ```
   `blank` gives the frame only: the brand tokens, the header slots, the CTA band and an empty `#body`. Add `--logo path/to/logo.svg` to use the brand's logo file in place of the text wordmark. Write the zones and the timeline from your beat sheet, using the motion library in `compose.md`. The header never animates, but you choose where it sits; the CTA band stays at the bottom. Pick the CTA mode in `references/copy.md`. Run `npx hyperframes lint posts/<slug>/animation` until it shows 0 errors. `references/hyperframes.md` lists the gotchas.

6. **Review the motion before rendering.**
   ```bash
   python3 scripts/snapshot_sheet.py posts/<slug>/animation
   ```
   Open `animation-sheet.jpg` and look at it as a stranger scrolling by. Check:
   - the concept sentence is visible in a still;
   - the title, the value line and the CTA read at phone size;
   - nothing collides or overflows;
   - every zone shows something specific from the resource;
   - the first and last tiles match;
   - the finish holds at full size: aligned edges on a 64 px margin, no label touching another, real words where a reader would expect words (not grey placeholder bars), official marks standing alone (never a logo tile inside another tile).

   Fix and repeat until all of these hold. After any fix made after rendering, run `snapshot_sheet.py` again so the sheet matches the GIF. A composition rarely works on the first pass. Plan two or three rounds.

7. **Render, then gate.**
   ```bash
   python3 scripts/render_gif.py posts/<slug>/animation
   python3 scripts/gif_gate.py posts/<slug>/graphic.gif
   ```
   The gates are FRAMES, BYTES, SIZE, LOOP, FPS, SEAM, MOTION and BAND, and all must pass. Then open `graphic-frame.png` and read the CTA letter by letter.
   - **If the GIF is too heavy,** `render_gif.py` steps down colors, dithering, fps and width on its own. If it still fails, run `scripts/weight_map.py` on the GIF to see which area costs, then shrink or shorten that motion (`references/design.md`, Weight budget).

   Show the user the sheet or the GIF and ask what feels off: the gates cover mechanics, not taste. If the user is not around, deliver it with a short list of the choices you made (brand source, font substitutions, invented example people) so they can veto any of them. If they like it, save it for next time with `python3 scripts/save_template.py posts/<slug>/animation --name <shape>`, and fill in the README that the script starts.

8. **Write the caption** with `references/copy.md` and save it as `caption.md`. Write three variations with different hook shapes and mark the one you recommend. The caption's list follows the same steps, in the same order, as the GIF.

9. **Publish and check.**
   - Upload `graphic.gif` as an image, natively or through a scheduler. Never convert it to JPEG or "optimize" it; that freezes it.
   - After it goes live, open the post: the media should animate.
   - If you republish an old post with the new graphic, post it as new rather than editing, because an edited post does not get a second run in the feed.

To learn from someone else's post first, run:
```bash
python3 scripts/analyze_reference.py <post-url> --out research/ref1
```
It writes stats, a frame sheet and a motion heat map. Borrow the principle, never the layout, palette or CTA shape.

## The rules, and why

- **The GIF tells the reader's outcome, not the resource's internals.** People stop for their own world (their post, their comments, their inbox, their booked call) with the tool doing its job inside it. Diagrams of how the resource works inside read as abstract. The resource's parts belong in the INSIDE line.
- **Products look like themselves, marks are official.** Draw a product's UI and characters in the style its makers show, and use official vector marks. The audience knows these brands at a glance, and a wrong logo or an invented look costs trust before they read a word.
- **Frame 1 and the last frame are the finished composition.** LinkedIn shows frame 1 before the GIF plays, and a loop that starts and ends on the same picture has no visible cut. Ambient loops never clear: motion highlights, travels or breathes, but never removes content.
- **The header says what the reader gets, not only the topic.** That means a title with the count, a value line with the outcome, and an INSIDE line listing what the resource contains, counted from the resource. A header that only names the audience leaves the reader guessing what is on offer.
- **An original concept per post, not a reskin.** Two posts that share a layout look like the same post in the feed. Start from the resource's shape, and borrow only technique from templates and references.
- **One chart per card, each moving its own way:** a token traveling a line, a scan down a checklist, bars called out in turn, a grid that pulses. Variety reads as premium; lists and highlights alone read as boring.
- **The text that carries meaning must read in the feed:** 22 px or more for card titles, and 16 px or more for labels, at 1080 px wide. Dense details inside cards can be texture. That density is the curiosity gap.
- **Honest content only.** Every number on the canvas comes from the resource, with its source on the card. Never invent clients, revenue or results presented as real. Showing the workflow's own example states (a sample commenter, a draft DM, "Call booked" on a calendar) is fine: it illustrates what the reader's flow looks like, uses roles or first names rather than real people, and claims no count of outcomes.
- **The brand, big.** Use the logo or wordmark, the brand's own colors, and the brand's own fonts (bundled locally). The CTA band uses the brand's main accent.
- **The CTA is one line, in a 104 px full-width band at the bottom,** where it sits right above LinkedIn's Like, Comment and Share bar. It must be legible, not the loudest thing on the canvas: a band that eats the canvas leaves less room for the story. Leave out "for free" and similar bait phrases, which make the image read as engagement bait.
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
