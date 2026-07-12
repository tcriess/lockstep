# Rebuilding Aurora with Lockstep

This is the toolkit's capstone tutorial. We take a real, finished 4kb Atari ST intro — **Aurora**
(tecer & ZoltarX): all four borders open, full-sync, VBL-only, a 64-line scroller in a TOS font blown
up to 64×64, two mask-and-or sprites on a Lissajous path, a two-colour logo and a dosound tune — and
we rebuild it **through Lockstep**.

The rule is:

> **The content is Aurora's. The counting is Lockstep's.**

Every instruction, every table, every effect is the original's, taken verbatim. Every *number* the
original's author worked out with a pencil — the `dcb.w 90 / 13 / 12` on a border line, the
`dcb.w 58` and `dcb.w 22` balancing each conditional in the preamble, the `dcb.w 798` that pads the
whole thing back out — is **deleted**, and derived by the tool instead.

That claim is falsifiable, which is the point of doing it: if the tool's cost model is wrong
anywhere, the numbers come out different and the picture falls apart.

The code is [`examples/aurora/aurora.py`](https://github.com/tcriess/lockstep/blob/main/examples/aurora/aurora.py); the untouched original is
[`examples/aurora/orig/aurora.s`](https://github.com/tcriess/lockstep/blob/main/examples/aurora/orig/aurora.s).

---

## 1. A frame has four places to put work

This is the mental model the whole toolkit hangs off. A full-sync frame is not "some code"; it is
four regions with four different rules, and Lockstep budgets all four:

```
     VBL entry
        |
        |  pre     17,052c   the VBL-entry pause. Dead time in a plain frame — the beam is
        |                    walking down toward the display. Aurora runs its ENTIRE per-frame
        |                    logic here: five sequence steppers and both sprite draws.
        v
     [beam sync]            the $ff8209 poll + the variable-cost `lsl.w` fine-sync
        |
        |  post       340c   the window between the lock and the first band line. Load the
        |                    registers the bands are going to walk.
        v
     [band 0] ... [band 259]
        |
        |  bands   133,120c  260 scanlines, each EXACTLY 512c, with the border switches pegged
        |                    to their cycles and your effect poured into the gaps between them.
        v
        |  tail     8,582c   after the last visible line: the music replay, the screen flip.
        |                    Not a scanline, so the per-line check can't see it.
        v
     next VBL
```

The sizes are not suggestions. `pre` is padded back to *exactly* 17,052 cycles, because the 60 Hz
pulse immediately after it is the top-border bust and its scanline is fixed purely by how many cycles
come before it. Four cycles out and the top border stays shut.

---

## 2. The frame: borders for free

Start with the thing you no longer have to write:

```python
from lockstep.skeleton import OverscanFrame

frame = OverscanFrame()      # 227 main + bust + restore + 31 bottom = 260 lines
```

That object owns the once-per-frame beam lock, the left stabiliser, and the cross-boundary bottom
bust — all four borders, on all four wakestates, on a plain STF. You supply content; it guarantees
the borders. (See [`HOWTO_OVERSCAN.md`](HOWTO_OVERSCAN.md) for how it works.)

Aurora predates it, so it hand-rolls the same thing. We just use the object.

---

## 3. `pre` — your logic, in the pause

Aurora's preamble (its sections A–J) steps five sequences — sprite, animation, palette, sound,
scroller-palette — and draws both sprites. Nine conditionals, each **hand-balanced** so that both
arms cost the same, because a branch in this region means two different distances to the top-border
pulse:

```asm
    bge.s   .current_pal_seq_cnt_ok
    <inner code>                       ; arm 1
    bra.s   .current_pal_seq_cont
.current_pal_seq_cnt_ok:
    dcb.w   22,$4e71                   ; arm 2: 22 nops to make the arms equal. Why 22? Because
    nop                                ;        the author added up arm 1 and divided by four.
    nop                                ;        Change one instruction in arm 1 and this is wrong.
.current_pal_seq_cont:
```

In Lockstep you declare the *intent* — "these two arms must cost the same" — and the filler is the
tool's problem:

```asm
;@balance
    bge.s   .current_pal_seq_cnt_ok
    <inner code>
    bra.s   .current_pal_seq_cont
;@balance alt
.current_pal_seq_cnt_ok:
;@fill                                 ; <- the dcb.w 22 is GONE
    nop                                ; (Aurora's own evening-out pair, kept: they are part of
    nop                                ;  arm 2, and the tool sizes the filler around them)
;@balance end
.current_pal_seq_cont:
```

`aurora.py` does that transformation mechanically on the original's own text (`balanced()`), so you
can see it is the same code with the numbers removed. Then hand the whole region to the frame:

```python
frame = OverscanFrame(pre=aurora_pre())
```

Lockstep costs each *path*, equalises the arms, and pads the region to exactly the pause budget. What
comes out:

```
dcb.w 22,$4e71   ; @balance fill (arm2): +88c
dcb.w 58,$4e71   ; @balance fill (arm2): +232c
dcb.w 22,$4e71   ; @balance fill (arm2): +88c
...
dcb.w 796,$4e71  ; @fill -> budget 17052: +3184c
```

Those are **exactly** the author's numbers. All nine of his balance pads — `22, 58, 22, 22, 58, 22,
22, 34, 26` — come back out of the tool, re-derived from the instruction stream alone. That is the
falsifiable claim, and it is the load-bearing test in `tests/test_aurora.py`: the cycle model is the
one thing in the toolkit that the toolkit cannot check, so it is pinned against numbers a human got
right and shipped on hardware.

The final pad is the one place they differ: **Aurora's hand-counted pad is `dcb.w 798`**, and the
tool derives **796** — two nops, on a 17,052-cycle region, and they are not a disagreement about
cycles but about the *VBL prologue*, which is `emit_program`'s rather than his. (The author's own
comment at that spot reads *"those 2 cycles are totally ok to go up or down"*. He knew.)

`pre` refuses work it cannot size:

- **variable cost** — an unbalanced branch → two distances to the pulse → rejected;
- **over budget** — *"it would push the 60 Hz top-border pulse past its scanline and the TOP BORDER
  WILL CLOSE. Cut 2948c."*

---

## 4. `post` — the registers the bands will walk

340 cycles between the lock and band 0. Load the pointers your bands need. It may **not** touch
`a0`/`a1`/`d3`/`d4` — those *are* the border switches.

```python
POST = """\
    movea.l scrollscraddr,a6        ; a6 walks the scroller buffer through band A
    move.l  font_addr1,a3           ; a3/a4: the two preshifted font copies (the 8-px step)
    add.w   fontoffset1,a3
    move.l  font_addr2,a4
    add.w   fontoffset2,a4
    movea.l scrollscraddr,a5
    lea     216(a5),a5              ; a5: the rightmost group, where new data is fed in
"""
```

Lockstep pads it back to 340c: `dcb.w 53,$4e71  ; @fill -> budget 340: +212c`.

---

## 5. The bands: pegs, work, and gaps

A scanline is a **template** — the immovable hardware events, nailed to their cycles — plus **work**
poured into the gaps between them.

```python
ALLBORDERS = _allborders(left_nops=1)   # left @0, right @376, extra @444
```

Gaps: **356c**, **52c**, **48c**.

> Note that the first gap is 356c, not the original's 360c. The wakestate-robust left blip carries
> one extra `nop` (the stabiliser that keeps ws2's left border open), which costs 4 cycles out of the
> line. In the original, that one change would mean re-deriving every filler count on every line by
> hand. Here the packer just re-sizes the gaps, and `verify` confirms all 260 lines are still 512c.

Aurora's scroller shifts one 16-px column left per frame, and it needs **two raster lines of
byte-shifting per scroller line**, so 64 scroller lines cost 128 raster lines. The work is Aurora's
exact instruction stream:

```python
COL = "move.l 8(a6),(a6)+\naddq #4,a6"          # one column: 24 + 8 = 32c

def band_shift_line1() -> WorkStream:
    return WorkStream([
        WorkBlock("nop"),                                   # 4c
        *[WorkBlock(COL) for _ in range(11)],               # -> gap1 = 356c
        WorkBlock(COL),                                     # \
        WorkBlock("move.w 8(a6),(a6)+"),                    #  > gap2 = 52c
        WorkBlock("nop"),                                   # /
        WorkBlock("move.w 8(a6),(a6)+\naddq #4,a6"),        # \  gap3 = 48c
        WorkBlock("move.l 8(a6),(a6)+"),                    # /
    ])
```

Look at gap 2 and gap 3: a 32-bit copy is emitted as **`move.w` … border switch … `move.w`**. The
raster cuts a longword in half. That is not a quirk to be tidied away — it is what "the switch is
immovable and the work goes around it" actually means in practice.

### Beam windows are constraints, not decoration

The per-line palette has to be **loaded before the right-border switch and written after it**, so the
colours take effect on the *next* scanline. Say so:

```python
def band_palette_line() -> WorkStream:
    return WorkStream([
        WorkBlock(PAL_LOAD, beam=(0, 376)),     # 16 colours -> registers, before the switch
        WorkBlock(PAL_HI,   beam=(392, 444)),   # ...write them after it
        WorkBlock(PAL_LO,   beam=(464, 512)),
    ])
```

Without the windows the packer does exactly what you told it — fills the line — and puts the whole
lot in the 356c gap, where the colours land a line early. **Every line still closes at 512c, so
nothing complains.** The window is the difference between a band that is on budget and a band that is
*correct*.

### A `WorkStream` is poured ACROSS a band, not repeated on each line

This one cost me hours, so it gets its own heading. `Segment(tmpl, work, n_lines)` pours `work`
across the whole band. If you want the same work on **every** line, the stream must carry it N times:

```python
def per_line(make, n):
    blocks = []
    for _ in range(n):
        blocks.extend(make().blocks)
    return WorkStream(blocks)

segs.append(Segment(allb, per_line(band_feed_line, 8), 8))
```

Get it wrong and the packer greedily fills each line to capacity:

```
placed per line: [11, 11, 11, 11, 12, 11, 5, 0]     # wrong: greedy
placed per line: [9, 9, 9, 9, 9, 9, 9, 9]           # right: beam-windowed, 9 per line
```

Every line is still 512c. Nothing fails. You just get one eighth of a scroller.

### The whole band stack

```python
segs = []
for _ in range(64):                                          # A: 64 scroller lines,
    segs.append(Segment(allb, band_shift_line1(), 1))        #    two raster lines of
    segs.append(Segment(allb, band_shift_line2(), 1))        #    byte-shifting each = 128
segs.append(Segment(allb, per_line(band_feed_line, 8), 8))   # B: feed a new 64-line column in
segs.append(Segment(allb, WorkStream([]), 59))               # C: just hold the borders open
segs.append(Segment(allb, band_palette_first(), 1))          # D: load the palette-window pointer
segs.append(Segment(allb, per_line(band_palette_line, 31), 31))   # E
segs.append(Segment(bust, band_palette_bust(), 1))           # F: the bottom-border bust line
segs.append(Segment(firstbot, band_palette_line(), 1))       #    the 50 Hz restore line
segs.append(Segment(allb, per_line(band_palette_line, 30), 30))   # G: the opened bottom border
segs.append(Segment(allb, band_palette_last(), 1))           # H: put the global palette back
```

```
bands: 260 lines, 2507/2507 work units, 0c of nop filler
```

**Zero nop filler.** Every cycle of every gap on all 260 scanlines is doing real work.

---

## 6. The tail, and the budget that can't see it

The music replay runs after the last visible line. That region is **not a scanline**, so the per-line
check is blind to it — and a fat tail makes the handler overrun the frame, which lands the *next*
frame's top-border switch late. Cost it:

```python
from lockstep.budget import frame_budget
fb = frame_budget(frame, tail_cost=hi, reserved=False)
```

```
frame budget (1040 STF / PAL, 160256c/frame):
  skeleton      151674c  = wrap 328 + prelude 18226 + bands 133120 (260x512)
  slack budget    8582c  (free for the post-display tail)
  tail             900c  -> 7682c free after tail
  !! UNRESERVED: this 900c tail is data-dependent — budget its WORST case, not a typical frame,
     or it will fit on cheap frames and close the border on the dear one (intermittent flicker).
```

---

## 7. Verify: cycles, then pixels

Two different questions, two different tools.

```python
from lockstep.verify    import verify_segments   # every line exactly 512c, on silicon
from lockstep.wakestate import verify_overscan   # ...and did the borders actually OPEN?
```

`verify_segments` is the **cycle gate**: fast, video off, wakestate-invariant. `verify_overscan` is
the **pixel proof**: it runs the real `.TOS` at all four wakestates across *consecutive* frames and
reports a matrix. You want both — a frame can be perfectly 512c per line and still show nothing.

> **A caveat this demo taught us.** `verify_overscan` decides "is this border open?" by comparing the
> overscan bands against the border colour. Aurora's per-line palette **rewrites palette 0 — which
> *is* the border colour** — and its background is the same light grey as its border. The open
> borders are invisible *by design*; that is the demo's whole charm. So the detector cannot certify
> Aurora as-is: grey content in an open border is indistinguishable from a closed grey border. For
> certification you build a **marker variant** that paints the overscan a distinct colour
> (`lockstep.wakestate.probe_fill` exists for exactly this).

---

## 8. What rebuilding a known-good demo found

This is the real reason to do a capstone. Every one of these was a *silent* bug — the build was
clean, every line measured 512c, and the picture was wrong:

| bug | why it was invisible |
|---|---|
| **`rept` bodies weren't multiplied in a sized region.** `annotate` had always expanded `rept 16` correctly; `expand()` — the engine that sizes `@pad`/`@budget`/`@balance` filler — counted the body **once**. | Aurora's sprite draw is four `rept 16` blocks. The preamble was under-costed by ~11,000 cycles, so the tool padded it with 14,344c of nops. Everything still "fit". |
| **vasm was rewriting what we had just counted.** `build_tos` called vasm with only `-Ftos`, so its optimiser was free to turn absolute addressing into PC-relative and `move.l #x,dn` into `moveq` — each of which *changes the cycle cost*. | The entire premise of the toolkit is that the emitted instructions cost what the model says. Aurora's own Makefile mandates `-no-opt`. Now so does ours. |
| **A `WorkStream` is poured across a band, not repeated per line.** | The lines still closed at 512c. You just got 1/8th of the effect. |
| **Beam windows are load-bearing.** Without them the packer fills the first gap and the palette lands a line early. | Ditto: on budget, wrong picture. |
| **A taken branch costs 12c, not the manual's 10c.** The table charged BRA/Bcc-taken their raw 68000 cost and carried the 2c remainder forward as bus phase. On an ST the taken branch refills the prefetch queue, and the refill *realigns* the CPU to the 4-cycle bus — the 2c never come back. `@balance` therefore under-filled **every** arm by exactly 4 cycles. | See below. This one is worth its own section. |

Four of those five are toolkit fixes with regression tests; the fifth is a documented idiom
(`per_line`). That is what a capstone is *for*: a demo you already trust is the only thing that can
tell you your tool is lying to you.

### The four cycles that hid the scroller

The last bug is the one worth the whole exercise, because of how far the symptom sat from the cause.

The symptom was **"the scroller does not render."** Everything it depends on was verified *in RAM*
with Hatari's `savebin`: the LINE-A font rip produced real glyphs, the feed wrote correct blown-up
character data into the off-screen column, the byte-shift propagated it across the line, and the
per-line palette loaded valid, contrasting colours. The scroller buffer was **full of text** and the
palette was **right** — and the screen showed bare colour bands.

The cause was four cycles in `st68k`'s branch table.

Aurora's preamble contains nine hand-balanced conditionals, and its author padded each one with a
`dcb.w` he derived by hand and verified on real hardware. Lockstep's `@balance` re-derives those
pads — and emitted **every single one exactly one word (4c) short**. That is not a coincidence you
can look away from; nine independent blocks do not all miss by the same amount by accident. A `bge.s`
costs 8c when it falls through and 12c when taken (measured, not assumed —
`test_branch_costs_match_hatari`), and the table said 10c.

Those pads sit in the VBL pause, and the pause is not slack — it is *the measured distance* to the
60/50 Hz pulse that removes the top border. Come out of it a few cycles early and the pulse lands on
the wrong scanline. So:

- the top border stayed **shut**, which pushed the `$8209` beam-lock 29 lines late,
- which put the bottom bust on the wrong line, so the bottom border stayed **shut** too,
- while the **left and right borders kept opening perfectly**, because those are driven by absolute
  `move.b d3/d4,(a0)` writes on every line, not by the pulse.

Aurora's scroller lives in the *opened bottom border*. With the bottom border shut, the shifter never
fetches those scanlines — the CPU dutifully wrote the text into a buffer the video hardware had
stopped reading. Hence: a screen that shows the per-line palette rolling (CPU writes, still on time)
across bands with no letters in them (bitmap never fetched).

The error was also **state-dependent**, which is why it looked like a content bug rather than a
timing one. Those nine conditionals are "sequence counter expired?" tests, and they take the
fall-through arm only when a counter runs out. The demo ran with all four borders open for the first
~1000 frames and then closed them permanently, at the frame where a sequence reached a state it
stayed in. A bug that appears 20 seconds in, in a different subsystem from its cause, is exactly the
kind a cycle-exact toolkit exists to prevent — and exactly the kind it will *cause* if its own
numbers are wrong.

The lesson, then, is not "branches are tricky". It is that **the cycle model is the one thing in the
toolkit that cannot be checked by the toolkit.** It has to be pinned against something outside
itself: the Hatari oracle (`measure`), and a demo whose numbers a human already got right and shipped.

---

## 9. Status

Working, and verified:

- **all four borders open, on all four wakestates** — 260 lines at exactly 512c, **zero nop filler**;
- the preamble's **nine hand-balanced conditionals** re-derived by the tool, matching the author's
  hand-counted pads *exactly* (`[22, 58, 22, 22, 58, 22, 22, 34, 26]`), final pad `796` against his
  `798` — the difference being `emit_program`'s VBL prologue, not the model;
- both **sprites** on their Lissajous path, drawn in the pause;
- the **scroller**: TOS font rip, blow-up, feed, byte-shift, and the per-line palette;
- the **logo** and the **dosound tune** in the tail, inside budget.

Against the original binary, at the same demo frame, the rebuild is **pixel-identical to within 18
pixels on one scanline** (36 of 459,264 — 0.008%).

Those 18 pixels are the honest price of the toolkit's more robust frame, and worth naming. Lockstep
opens the bottom border with a **cross-boundary bust** (60 Hz set late on the bust line, restored
early on the next) instead of Aurora's within-line pulse. The 60 Hz set at cycle 500 shortens that
line's last gap, so only 32c of palette work fits there instead of the full write, and one palette
entry on that single line keeps the previous line's value.

What it buys is the whole point:

| | ws1 | ws2 | ws3 | ws4 |
|---|---|---|---|---|
| **original `aurora.s`** | ok | border glitch | ok | **scroller cut off** |
| **the rebuild** | ok | ok | ok | ok |

The original was tuned on a machine that powers up in ws1/ws3 and opens its bottom border only
there. The rebuild renders the same frame, pixel-for-pixel, on **all four** — which is what the
cross-boundary bust and the left stabiliser are for, and it costs one palette entry on one line.
