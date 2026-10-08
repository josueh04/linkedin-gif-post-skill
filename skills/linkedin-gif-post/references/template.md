# research_bento

An ambient loop for a post that shares research, a checklist or a method. The template is a complete worked example: "14 checks before you trust a software factory", a research note on AI coding pipelines. It is 10 s at 15 fps, with every frame finished. To make a new post, keep the frame and the four cards, then swap the words, numbers and labels.

## Frame

| Element | Id or class | Content |
|---|---|---|
| Logo | `#logo` (text) plus `#cur` (the blinking bar) | The brand's wordmark. Replace it with `<img src="assets/logo.svg" style="height:52px">` if the brand has a logo file. Drop `#cur` if the brand has no cursor motif |
| Eyebrow | `#eyebrow` | `RESEARCH / ACCEPTANCE TEST`: the content type, then the resource's name |
| Title | `h1` with `<b>` around the count | "**14 checks** before you trust / a software factory." Two lines, at most about 26 characters each at 76 px |
| Value line | `#claim`, with the outcome in `<span>` (a static gradient) | The resource's thesis or the reader's outcome |
| INSIDE line | `#inside` | What the resource contains, counted: `14-CHECK SCORECARD + SCORING RULE + LINEARB DATA` |
| CTA | `#cta .k` | `FULL DOCUMENT <span>·</span> <em>LINK IN THE POST</em>`, or `COMMENT "<em>KEYWORD</em>"` (see copy.md) |

## Cards

| Card | Id | Chart and motion | To adapt |
|---|---|---|---|
| The method | `#line` | Six stations (`.st`, each with `small`, `b` and `.cks i` dots). A `#tok` token travels them twice per loop, and each station flares as it passes. `#weak` flags a problem at one station | Rename the stations after the method's steps. The dots under each station are its share of the checklist. `XS` in the script holds the station x positions; keep it in sync with the `left:` values. Move `#weak` to the station that catches the problem |
| The checklist | `#score` | `ROWS` in the script builds every row as `[label, group]`. A `#scan` bar walks them, each check pops, and the row at index 8 is flagged `MOST MISSED` | Edit `ROWS` (up to 14 rows fit at `RH = 29.2`). Change `i === 8` to the item the resource calls out. `#rule` holds the scoring rule |
| The headline data | `#yield` | `TIERS` holds grouped bars (`[label, a, b]`). The `#hl` box calls out each pair in turn with its gap | Put the resource's comparison in `TIERS`, set the legend and the source line, and keep three rows |
| One share | `#share` | 100 cells, where the indices in `AG` are highlighted and pulse in sequence. `#big` shows the figure | Set `AG` to the share (five indices for about 5%), and set `#big` and `#sharefoot` from the resource |

## Beats (10 s)

| Time | What moves |
|---|---|
| Every 1 s | The logo cursor blinks |
| 0.2 s and 5.2 s | The token runs the line; a station flares every 0.62 s; `#weak` shows at the third station |
| 0.35 to 8.75 s | The scan walks the checklist, 0.6 s per row; the flag pulses at 5.2 s and 5.8 s |
| 0.4, 3.6 and 6.8 s | The data callout moves to each pair and shows its gap |
| 0.8 s, then every 1.8 s | The highlighted share cells pulse |
| 9.0 to 9.9 s | Everything returns to the frame-1 state |

## Brand tokens

`:root` defines the tokens: `--bg`, `--ink`, `--ink-2`, `--muted`, `--accent` (with `-2` and `-3`), `--info`, `--ok`, `--warn`, `--card-1`, `--card-2`, `--cta`, `--cta-ink`, plus `-rgb` triplets for the colors used with alpha. Fonts are `--font-display`, `--font-body` and `--font-mono`.

`new_animation.py --brand` appends the brand's tokens at the end of the stylesheet, so they win. The script reads `--ok-rgb` once with `getComputedStyle`, because GSAP cannot tween a `var()`.
