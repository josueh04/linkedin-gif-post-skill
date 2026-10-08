# Design system

## Canvas

- 1080x1350 (4:5), authored at 1x. Ambient loops render and ship at 15 fps. A build loop (one that clears and rebuilds with a big move) ships at 720x900 and 30 fps; set `data-gif-profile="build"` or remove the attribute.
- **Dark and dense reads as premium in the feed:**
  - **Background:** the brand's darkest color.
  - **Washes:** two or three radial washes of the accents at 7 to 22% opacity.
  - **Texture:** a faint 54 px grid masked toward the edges.
- **A light brand:** keep a dark canvas in a deep tint of the brand's ink or accent, and use the brand's light color for text and cards. Flat, light, low-contrast scenes read as static.

## Header (never animates)

The header stays still, but its position is yours: top-left, split left and right, or at the bottom above the CTA (`compose.md`, Layout).


- **The logo,** large: a wordmark at about 52 px, or a logo file at about 56 px tall (`new_animation.py --logo`). If the brand has a motif (a cursor, a dot, a slash), a small loop on it is a cheap way to look alive.
- **The eyebrow:** the content type and the resource name, in mono caps tracked .12 to .18em, in an accent.
- **The title:** the count plus the promise, in the brand's display font, at 70 to 80 px. It is the largest type on the canvas. Put the count in the accent.
- **The value line:** the thesis or the outcome, in the body font at 30 to 40 px, with the key phrase in a static gradient.
- **The INSIDE line:** what the resource contains, counted, in mono caps at 18 to 20 px, with `+` separators in an accent. Count from the resource; never estimate.

## Typography

- **The brand's fonts come first,** including a serif if the brand uses one.
- **Proprietary fonts:** if the brand's fonts are proprietary and you hold no license for the files, use the closest open font:
  - a geometric or neo-grotesk sans: Inter or Geist;
  - a grotesk with character: Space Grotesk or Hanken Grotesk;
  - a text serif: Source Serif 4 or Newsreader;
  - a mono: JetBrains Mono or Geist Mono.

  Say which substitution you made.
- **Without a brand typeface,** prefer a sans for display. Editorial italic serifs on a tech topic read as generic AI output.
- **Bundle every font locally,** in `animation/fonts/`. A missing font falls back to a system face in the render.
- `.fit` elements in the templates shrink at load until they fit their max-width. Use it on any one-line text that varies in length.

## Cards

- **Fill:** a vertical glass gradient (card-1 to card-2 at about 90%), a 1 px ink hairline at 10%, and a 22 to 26 px radius.
- **Card titles** are 22 px in the display font, with an optional pill on the right (mono, 13 px).
- **Each card holds one chart with its own motion,** and every chart shows the resource's real content. Some forms that read well:

  | Content | Chart | Motion |
  |---|---|---|
  | A method | A line of stations | A token travels it and each station flares |
  | A checklist | Rows with checks | A scan bar walks it and each check pops |
  | A comparison | Grouped bars | A callout moves from pair to pair and shows the gap |
  | A share | A 100-cell grid | The highlighted cells pulse |
  | A trend | A line chart | A dot rides the curve, out and back |
  | A cadence | A streak grid | Cells fill in |
  | Overlap | A Venn | Dots flow into the overlap |
  | Time | A bar with a playhead | The playhead walks it |

- **Sizes at 1080 px:** 22 px or more for card titles, 16 px or more for labels that carry meaning, and 13 px for mono tags. Dense rows can be 18 to 19 px; their density is the curiosity gap.
- **Semantic colors:** `--ok` for passes, `--warn` for the flagged item, `--info` for the baseline or human series, and `--accent` for the subject.

## Motion grammar (ambient)

- **Nothing hides content.** Motion highlights, travels or breathes; it never removes a card or a label. Frame 1 is the finished poster.
- **Stagger the cycles** so something always moves: here 0.6 s per checklist row, 3.2 s per data callout, 1.8 s per share pulse, and 5 s per token trip. Each cycle divides the loop or ends before it closes.
- **Eases:**
  - `power2.inOut` for travel;
  - `back.out(2 to 3)` for pops;
  - a 0.15 to 0.25 s flash, then a 0.35 to 0.6 s release.
- **Return to the frame-1 state by 9.9 s.** A reset that starts at 9.0 s and takes 0.4 s is invisible as a seam; the gate's SEAM check catches the rest.

## CTA band (never animates)

- Full width, flush to the bottom, 124 px tall (`cta_band_px` in config.json; the gate reads it).
- **The color:** the brand's main accent as a flat fill, with no gradient, because the gate checks that the band is flat. The text is in `--cta-ink`, with the key phrase in `--ink`.
- **The text:** one line at 56 to 76 px. Shorter text can go larger.
- It stays at the bottom, right above LinkedIn's action bar.

## Weight budget (4 MiB)

GIF frames store only the pixels that change, so file size follows how many pixels change and for how long. `scripts/weight_map.py` shows which area costs.

| Lever | Effect measured |
|---|---|
| A headline gradient that drifts the whole loop | 5.32 MiB, against 3.82 MiB with a static gradient |
| A pulsing blurred glow, a ring rotating nonstop and a waveform moving nonstop | 6.83 MiB, against 3.66 MiB with a thin ring ping, no rotation and bursts of motion |
| Dithering on flat UI | bayer at 192 colors 4.71 MiB; no dither at 192 colors 3.92 MiB; bayer at 128 colors 3.82 MiB |
| A large rotating wedge left on for the whole loop | 6.65 MiB, against 3.84 MiB with it limited to 2 s |

- **Keep gradients and glows still,** and move small solid shapes over them.
- **Use bursts (move, then rest)** rather than continuous motion; a burst roughly halves a region's cost.
- `render_gif.py` steps the palette down (128 to 96 colors), then drops dithering, then fps, then width. Check one decoded frame for banding.

## Never

- Invented clients, revenue, bookings or results.
- A blank or half-built first frame.
- A near-copy of someone else's post: their layout, palette or CTA shape. Borrow the principle; keep the brand.
- A header that names the topic but not what the reader gets.
- System fonts; the render falls back to something cheap. Bundle the brand's fonts locally.
- Text that runs off the canvas or out of its card. No gate catches it: check the sheet, or mark the element `.fit`.
- A square text card that repeats the caption.
