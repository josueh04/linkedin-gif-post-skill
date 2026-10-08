# Composing an original graphic

The default path is an original composition built for this resource, not a template with the words swapped. A template fits only when the resource has the same shape it was made for. This file is the method: from the resource to a concept, a layout, a motion plan and working code. Templates in `assets/templates/` are worked examples of that method, worth reading for technique, not for copying.

## 1. Find the resource's shape

Read the resource and decide what kind of thing it is. The shape decides the picture.

| Shape | The resource... | Visual metaphors that fit |
|---|---|---|
| Process | ...is steps in order (a routine, a pipeline, a method) | A line of stations a token travels; a conveyor; a circuit board with a signal; a subway map; a timeline with a playhead |
| Checklist or criteria | ...is a set of tests or rules | A scan down rows; a scorecard filling; a radar locking onto items; gates opening one by one |
| Transformation | ...turns one input into many outputs | A core that fans out; a prism splitting light; a constellation from one star; layers exploding up from one card |
| Accumulation | ...builds a stock over time (a bank, a calendar, a library) | A calendar floor filling; a shelf stacking; a heatmap or streak grid lighting up |
| Comparison | ...shows a gap (before and after, human and agent, us and them) | Grouped bars with a callout on the gap; a split screen; two curves diverging; a scale tipping |
| Discovery | ...finds signal in noise (research, listening, sourcing) | A radar sweep; a search beam over a field of quotes; a magnifier passing over a wall of text; a filter funnel |
| Network | ...connects parties or sources | Nodes and edges with pulses; a hub and its spokes; a map with routes |
| Cycle | ...repeats every week or month | An orbit; a clock face; a loop track. Cycles make natural seamless loops |
| Ladder or catalog | ...is a set of patterns or levels, ordered by complexity, maturity or cost | A ladder a token climbs; a staircase; a stack of tiers; a periodic table with one cell lit at a time |

Write one sentence before any code: "**[Something concrete]** travels or transforms **[through what]** and becomes **[the outcome the reader wants]**." Example: "One real ticket travels the factory line, gets checked at 14 gates, and ships, or gets blocked at check 9." If you cannot write the sentence, you do not have a concept yet.

## 2. Choose the loop family

| | Ambient | Build |
|---|---|---|
| What happens | Everything is on screen in every frame; motion highlights, travels and breathes inside the cards | The body clears, rebuilds with one big move (a sweep, a camera push, an explosion), then holds the finished frame |
| Fits | Dense resources with several parts (a checklist plus data plus method); research | One strong transformation or discovery; a launch; a single system |
| Spec | 10 s, 15 fps, 1080x1350 | 8 s, 30 fps, 720x900 |
| Risk | Reads as static if few parts move (the gate needs 40% of the body alive) | Heavy if large areas move long; a half-built frame if the clear runs late |

Set it with `new_animation.py --profile ambient|build`.

## 3. Lay out the canvas

- **Fixed:** the CTA band, 124 px at the bottom. Nothing else is fixed.
- **The header can move.** Top-left with logo top-right, logo and title on the left with the eyebrow on the right, or the title at the bottom above the CTA with the scene on top. Change it between a brand's posts so they don't look alike.
- **The body gets 60% or more of the canvas.** Pick one hero zone (about half the body) for the concept sentence, and 2 to 4 supporting zones for the list, the data and the proof. A layout with no hero reads as a dashboard.
- **Sketch zones as rectangles with coordinates** before writing HTML. For example: header 0 to 390; hero 404 to 666 full width; left column 60 to 580 from 682 to 1210; right column 596 to 1020, split at 982. Margins are 60 px, and gutters 16 px.
- **Every zone holds real content** from the resource: its step names, its counts, its numbers with their source. Write the words first, then size the zones to fit them at legible sizes (`design.md`, Cards).

## 4. Plan the motion

Write a beat sheet before the code: one row per motion, with zone, what moves, start, duration and period.

- **One narrative thread** carries the concept sentence: the token that travels, the sweep that finds, the core that fans out. It runs once (build) or 2 to 5 times (ambient).
- **Each supporting zone gets its own motion type,** never the same one twice: scan, callout, pulse, ride a curve, fill, blink, count by swaps.
- **Tie motions together where it means something:** the station the token reaches lights the matching checklist group.
- **Periods divide the loop:** 1, 2, 2.5 or 5 s for 10 s; 2, 4 or 8 s for 8 s. Or the motion ends before the loop does.
- **Everything is back in its frame-0 state by `END - 0.07`.** Frame 0 is the poster. The templates draw a red banner if any tween ends after `END`. Short flares can still slip between the sheet's tiles, so check the beat sheet's math.
- **Budget:** large areas move briefly; gradients and glows stay still; small solid shapes move. Use bursts rather than continuous motion (`design.md`, Weight budget).

## 5. Motion library

Seek-safe patterns for the paused GSAP timeline `tl`. Each one returns to its start state. Tween only `x`, `y`, `scale`, `rotation`, `opacity`, colors and SVG attributes; never `left`, `top`, `width` or `height`.

```js
// Travel: a token moves along stations at xs[], arriving at each every `step` s.
function travel(tok, xs, t0, step) {
  tl.set(tok, {x: xs[0], opacity: 0}, t0).to(tok, {opacity: 1, duration: .2}, t0);
  xs.forEach((x, i) => i && tl.to(tok, {x, duration: step * .8, ease: "power2.inOut"}, t0 + (i - 1) * step));
  tl.to(tok, {opacity: 0, duration: .25}, t0 + (xs.length - 1) * step);
}

// Flare: a station or card lights, then releases.
const flare = (glow, s) => tl.to(glow, {opacity: 1, duration: .15}, s).to(glow, {opacity: 0, duration: .45}, s + .5);

// Scan: a bar walks rows (y positions) and each row's mark pops as it passes.
function scan(bar, ys, marks, t0, step) {
  tl.set(bar, {y: ys[0], opacity: 0}, t0).to(bar, {opacity: 1, duration: .3}, t0);
  ys.forEach((y, i) => {
    const s = t0 + i * step;
    if (i) tl.to(bar, {y, duration: .3, ease: "power2.inOut"}, s - .3);
    tl.to(marks[i], {scale: 1.3, duration: .15}, s).to(marks[i], {scale: 1, duration: .35}, s + .2);
  });
  tl.to(bar, {opacity: 0, duration: .4}, t0 + ys.length * step);
}

// Callout: a highlight box moves between items and a label shows while it rests.
function callout(box, ys, labels, times, hold) {
  times.forEach((s, i) => tl.to(box, {y: ys[i], opacity: 1, duration: .4, ease: "power2.inOut"}, s)
    .to(labels[i], {opacity: 1, duration: .25}, s + .3).to(labels[i], {opacity: 0, duration: .3}, s + hold));
}

// Pulse in sequence: cells pop one after another.
const pulses = (cells, t0, every) => cells.forEach((c, k) =>
  tl.to(c, {scale: 1.6, duration: .2, ease: "back.out(3)"}, t0 + k * every).to(c, {scale: 1, duration: .4}, t0 + k * every + .3));

// Ride: a dot follows an SVG path out and back, so the loop closes.
function ride(dot, path, t0, half) {
  const mp = (a, b) => ({motionPath: {path, align: path, alignOrigin: [.5, .5], start: a, end: b}});
  gsap.set(dot, mp(0, 0));
  tl.fromTo(dot, mp(0, 0), {...mp(0, 1), duration: half, ease: "sine.inOut", immediateRender: false}, t0)
    .to(dot, {...mp(1, 0), duration: half, ease: "sine.inOut"}, t0 + half);
}

// Draw: an SVG line draws in (build loops), then stays.
function draw(path, s, d) {
  const L = path.getTotalLength();
  gsap.set(path, {strokeDasharray: L, strokeDashoffset: 0});
  tl.set(path, {strokeDashoffset: L}, s).to(path, {strokeDashoffset: 0, duration: d, ease: "power2.inOut"}, s);
}

// Swap text: a counter or label changes in discrete steps (seeking can skip onUpdate, so never count with it).
const swap = (node, values, times) => values.forEach((v, i) => tl.set(node, {textContent: v}, times[i]));

// Sweep: a wedge or beam rotates once, then rests (keep it short: it rewrites a large area every frame).
const sweep = (wedge, s, d) => tl.fromTo(wedge, {rotation: 0}, {rotation: 360, duration: d, ease: "none", immediateRender: false}, s);

// Fly out: cards leave a center point with overshoot (build loops). Set their final layout in CSS first.
function flyOut(cards, cx, cy, s) {
  cards.forEach((c, i) => {
    const r = c.getBoundingClientRect(), dx = cx - (r.left + r.width / 2), dy = cy - (r.top + r.height / 2);
    tl.fromTo(c, {x: dx, y: dy, scale: .2, opacity: 0}, {x: 0, y: 0, scale: 1, opacity: 1, duration: .6, ease: "back.out(1.6)", immediateRender: false}, s + i * .08);
  });
}
```

Build-loop clears: `tl.to(bodyParts, {opacity: 0, y: 12, duration: .35, stagger: .02}, .45)`, then rebuild from about 0.9 s and hold from about 5 s. Never fade the header or the CTA.

## 6. Build, look, fix

1. `new_animation.py --out posts/<slug> --template blank --profile ambient|build --brand ...`
2. Write the zones' HTML with real content, then the timeline from the beat sheet.
3. Run `npx hyperframes lint posts/<slug>/animation`. Zero errors are required; warnings about the nested clip and overlapping tweens are fine.
4. Run `snapshot_sheet.py`. A red banner on the canvas means a tween runs past `END`; fix it first. Then look at the sheet as a stranger scrolling by:
   - Is the concept sentence visible in a still?
   - Can you read the title, the value line and the CTA at phone size?
   - Does anything collide, overflow or look unfinished?
   - Does every zone show something specific from the resource?
   - Do frame 0 and the last tile match?
5. Fix and repeat until all five answers are yes. Then run `render_gif.py`, `gif_gate.py`, and `weight_map.py` if the GIF is heavy.
6. Show the user the sheet or the GIF before they post, and ask what feels off. Taste is theirs; the gates only cover the mechanics.

## 7. Keep what works

When a composition passes the gates and the user likes it, save it as a template, so the next post of the same shape can start from it:

```bash
python3 scripts/save_template.py posts/<slug>/animation --name <shape-name>
```

The script copies the project into `assets/templates/<shape-name>/` and starts a `README.md` there. Fill it in: the shape it fits, the zones and their ids, the beat sheet, and what to change for a new post.
