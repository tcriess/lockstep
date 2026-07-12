# HOWTO: a verified four-border overscan intro with Lockstep

*From an empty frame to a `.TOS` that opens all four borders on every wakestate — and stays
open when you pour effects in. Every step ends in a machine-checkable guarantee, not a vibe.*

This is the practical companion to `DESIGN.md` (the why) and `TIMING.md` (the cycle model). It
walks the toolkit an author actually touches, in the order you meet it:

1. [The empty frame](#1-the-empty-frame) — `OverscanFrame` opens the borders for you.
2. [Prove it opens](#2-prove-the-borders-open) — `wakestate.verify_overscan`, all four wakestates.
3. [Pour in effects](#3-pour-work-into-the-bands) — band work, cycle-verified 512c/line.
4. [Respect the budget](#4-respect-the-frame-budget) — `budget.frame_budget`, before a border closes.
5. [Race the beam](#5-race-the-beam) — `beamrace.BandGeometry` for a bouncing band.
6. [Don't tear](#6-dont-tear-the-active-zone) — `effects.active_zone_lint` + recipes.
7. [The whole pipeline](#7-the-whole-pipeline) on one page.

Prerequisites: Python 3.10+, `vasmm68k_mot` on `PATH`, and a cycle-exact `hatari` + a TOS/EmuTOS
ROM for the emulator-backed checks (set `STCYC_HATARI` / `STCYC_VASM` / `STCYC_TOS` to override
discovery). The static checks (cycles, budget, beam-race, lint) need none of that.

---

## 1. The empty frame

The hardest, most reused thing in a full-sync overscan demo is *opening the four borders and
keeping them open* — the once-per-frame `$8209` MMU beam-lock, the top-border eor-dance, the left
stabiliser, and the cross-boundary bottom bust. `OverscanFrame` owns all of it. You supply the
`setup` (screen fill / palette / video base); **the skeleton guarantees the borders.**

```python
from lockstep.skeleton import OverscanFrame

# a minimal green screen so an open border is visibly green in the overscan
GREEN = 0xA8000
SETUP = f"""\
    move.w  #$0000,$ffff8240          ; palette[0] = black  (the border colour)
    move.w  #$0070,$ffff825e          ; palette[15] = green (the display fill)
    move.l  #${GREEN:x},a2
    move.w  #$3fff,d0
.fill:
    move.l  #$ffffffff,(a2)+          ; fill the screen (all four planes set)
    dbra    d0,.fill
    move.b  #${(GREEN >> 16) & 0xff:02x},$ffff8201   ; video base high
    move.b  #${(GREEN >> 8) & 0xff:02x},$ffff8203   ; video base mid
    lea     $ffff8260,a1
    moveq   #2,d3
    moveq   #0,d4
"""

OverscanFrame().build("BORD.TOS", setup=SETUP)
```

That is a complete, bootable, all-four-borders-open full-sync demo. `build()` wraps the frame in
Aurora's proven `$70`-VBL-handler bootstrap (disable Timer C and all MFP interrupts, install the
frame as the handler, idle the main program) — the same `emit_program` the examples use.

The default frame is `main_lines=227` display lines + the cross-bust line + `bot_lines=32` — 260
scanlines, exactly Aurora's frame height, every line closed to 512 CPU cycles. Knobs, if you need
them: `OverscanFrame(main_lines=…, bot_lines=…, left_nops=…, cross=True/False, sync=SyncConfig(…))`.
`cross=False` gives the within-line bottom bust (opens the bottom on ws1/ws3 only); the default
`cross=True` is the all-wakestate cross-boundary bust.

> The skeleton never references a screen address — it is content-agnostic. An "empty" frame just
> shows whatever the video base in your `setup` points at. That is why the exact same object drives
> both `bordopen` (an empty green frame) and `aurora` (a whole demo).

---

## 2. Prove the borders open

"It opened on my ST" is a sample size of one. The border-open property is **wakestate-dependent**
(the cold-start GLUE phase shifts your whole frame) *and* **frame-dependent** (a bad lock flickers
period-2 — every other frame). So you check all four wakestates across *consecutive* frames.

```python
from lockstep.wakestate import verify_overscan

report = verify_overscan("BORD.TOS", wakestates=(1, 2, 3, 4), frames=range(320, 323))
print(report.matrix())
print("ship it" if report.ok else "DO NOT SHIP")
```

```
overscan matrix — wakestates × borders  (frames 320..322, 3 consecutive)
        left     right    top      bottom
  ws1   open     open     open     open
  ws2   open     open     open     open
  ws3   open     open     open     open
  ws4   open     open     open     open
  => ALL borders open on all wakestates, no flicker
```

The detector reads the four **outer overscan edge bands** of the rendered frame: a closed border
leaves its band at the border colour (fill ≈ 0.00), an open one spills display colour into it
(≈ 0.6–1.0). A border that differs between consecutive frames is reported as `FLICKER`, not `open`
— the period-2 trap a single screenshot cannot see.

In a test, make it a one-liner that fails CI the instant a border closes on any wakestate:

```python
from lockstep.wakestate import assert_overscan_open
assert_overscan_open("BORD.TOS", frames=range(320, 322))   # raises with the matrix on failure
```

**Bottom-border-open demos stall Hatari's vblank counter.** Once the bottom border is gone there is
no vblank for `nVBL > N` to count, so bump a longword frame counter yourself and trigger on it:
`verify_overscan(prog, count_addr=0x1000)` (the demo does `addq.l #1,$1000` at the end of each
frame). The examples use `$1000`.

**Churning demos** (a sparse effect on a black field) leave the overscan edges dark — a black
overscan is indistinguishable from a closed border by screenshot. Paint a bright test-only marker
strip into the overscan edges of the displayed buffer so an open border reads bright; see
`lockstep.wakestate.probe_fill`, and build a `marker=True` variant that is byte-identical to the
shipped binary when the flag is off.

---

## 3. Pour work into the bands

Effects go into the display bands as `WorkStream`s, poured into the gaps between the border pegs.
The frame exposes `upper` (the `main_lines` display band) and `lower` (the post-bust band):

```python
from lockstep.model import WorkStream

work = WorkStream.repeat("move.l 8(a6),(a6)+\naddq #4,a6", n=39)   # e.g. a scroller feed
OverscanFrame().build("BORD.TOS", setup=SETUP, upper=work)
```

The packer places the work around the pegs and closes every scanline to exactly 512c — the border
switches still land on their cycles. Prove the cycle side (wakestate-invariant, video off, fast):

```python
from lockstep.verify import verify_segments
f = OverscanFrame()
vr = verify_segments(f._segments(work, WorkStream([])))   # measure every line in cycle-exact Hatari
print(vr.report())            # every line == 512c, beam constant per line -> borders hold
```

For work that isn't a clean multiple of your unit, use `StepWork` (the `move.l`/`move.w` mix) so the
solver fills each gap exactly instead of wasting the remainder on `nop`s. See `TUTORIAL.md §5` for
the scheduler surface (templates, pegs, `StepWork`, multi-band `pack_schedule`) that `OverscanFrame`
sits on top of.

The two checks are complementary and you want both: **cycles are the gate** (`verify_segments` —
every line 512c, cheap, wakestate-invariant), **pixels are the proof** (`verify_overscan` — the
borders actually open, per wakestate).

---

## 4. Respect the frame budget

The display bands are only half the frame. After the borders are busted, the VBL handler runs a
**post-display tail** — palette pointer fills, the sound replay, per-frame churn. That tail competes
for the frame's *slack*, and if it eats the slack the handler overruns toward the next VBL, the
eor-dance top-removal lands past the wakestate margin, and **the top border silently closes.** This
is the regression that cost this project a border (≈672c of added per-frame work) and was invisible
to the toolkit — until W3.

```python
from lockstep.budget import frame_budget

fb = frame_budget(OverscanFrame(), tail=my_tail_asm)   # cost the tail against the frame
print(fb.report())
```

```
frame budget (1040 STF / PAL, 160256c/frame):
  skeleton      151674c  = wrap 328 + prelude 18226 + bands 133120 (260x512)
  slack budget    8582c  (free for the post-display tail)
  tail            6800c  -> 1782c free after tail
  => within budget (1782c to spare)
```

The standard frame leaves **~8,600c of slack**. Warnings fire *before Hatari is ever run*:

- **OVER** — the tail exceeds the slack; the handler overruns the frame and the borders *will* close.
- **RISK** — the tail is within the VBL-entry-jitter margin (~64c) of the slack; likely to close the
  top border. Verify on all wakestates or cut it back.
- **UNRESERVED** — a *data-dependent* tail (a sound replay, a conditional churn) costed at a typical
  frame instead of its worst case. Reserve the worst case, always:

```python
from lockstep.sound import profile_play
env = profile_play(play_body, ticks=…)          # measures the replay across the whole tune
fb = frame_budget(OverscanFrame(), tail_cost=env.reserve, reserved=True)   # worst-case, phase-stable
```

A tail that fits on its cheap frames but not its dear one is exactly the intermittent border flicker
the emulator only catches on the dear frame. Reserve, don't average. Guard it in CI:

```python
from lockstep.budget import assert_within_budget
assert_within_budget(OverscanFrame(), tail_cost=env.reserve)   # raises (with the report) if OVER/RISK
```

This boundary is real, not theoretical: an over-budget tail warns statically *and* closes the
borders in Hatari (see `tests/test_budget.py`).

---

## 5. Race the beam

If an effect writes a band *while the beam is displaying it* — a see-through scroller, a raster bar
that bounces — the write must lay each row down **before** the beam reaches it. Two axes:

- **Intra-line** (where in the 512c line the write happens): `WorkBlock(beam=(lo, hi))` pins a write
  to a cycle window; the packer places it only where it runs inside `[lo, hi]`.
- **Inter-line / vertical** (a band written row-by-row down the screen): a geometry race. A band
  written from the split at `work_start`, `lines_per_row` scanlines per row, that bounces up toward
  the split, can have its last row's write fall *behind* the beam and tear.

W4 makes the vertical race a computed certificate instead of a hand comment:

```python
from lockstep.beamrace import BandGeometry, certify_race

band = BandGeometry(
    work_start=104,      # display line where the band's row-writing begins (the upper/lower split)
    center=193,          # band centre display line at rest
    height=34,           # band height in rows (guards included)
    lines_per_row=2,     # work scanlines to lay down one band row
    amplitude=7,         # worst-case UP-bounce (drives the race)
    amp_down=29,         # DOWN-bounce if asymmetric (a down-bias; drives the fit)
    frame_bottom=259,    # first line the band must stay above (the bottom-border structure)
)
res = band.check()
print(res.report())      # "OK — every band row is written ahead of the beam (worst-case bounce)"
certify_race(band)       # raises ValueError naming the first violating row if it tears / collides
```

`check()` certifies both the **race** (`top_min > work_start + height·(lines_per_row − 1)`) and the
**fit** (the deepest down-bounce clears `frame_bottom`), and names the first row that tears. Raise a
band centre, lower the split, cut the height, or reduce `lines_per_row`/`amplitude` to fix it — the
numbers tell you which. This is the classic bouncing-scroller constraint
`BANDY > WORK_START + HEIGHT·(LPR−1)`, now checked rather than trusted.

---

## 6. Don't tear the active zone

During the active display the CPU and the video shifter share the bus. A screen write via
**absolute** addressing (`move.w d0,$a8000`) holds the bus differently from a register-indirect one
(`move.w d0,(a3)`) of the *same cycle cost*, and it tears (DESIGN §1.5, Hatari-proven). The border
switches and palette *are* written absolute, by design — those are hardware registers. Everything
else in the active zone must be register-indirect.

```python
from lockstep.effects import active_zone_lint, assert_active_zone_clean

for f in active_zone_lint(my_band_asm):
    print(f)          # "line 7: move.w d0,$a8000 -> absolute screen/RAM write ... tears ..."

assert_active_zone_clean(my_band_asm)   # CI guard: raises listing every tearing write
```

The lint flags absolute writes to display/RAM while allowing the required absolute writes to the
hardware registers (`$ff8xxx` / `$ffff8xxx`). It is clean on the skeleton's own border pegs — no
false positives.

Two proven idioms come as lint-clean generators:

```python
from lockstep.effects import band_writer, palette_split

band_writer(11, src="a4", dst="a2")          # 11x  move.w (a4)+,(a2)+   (register-indirect band)
palette_split(["d0", "d1", "d2"], first=0)   # move.w dN,$ffff824X  (Aurora's late-line palette split)
```

`band_writer` is the see-through-scroller idiom (register-indirect by construction, so it passes the
lint and races the beam when placed in a `beam=` window — pair it with the `BandGeometry` of §5).
`palette_split` is Aurora's trick: preload the 16 colours to registers in the slack, then write the
shifter in the free window around the pegs.

---

## 7. The whole pipeline

```python
from lockstep.skeleton import OverscanFrame
from lockstep.model import WorkStream
from lockstep.budget import assert_within_budget
from lockstep.effects import assert_active_zone_clean
from lockstep.beamrace import certify_race
from lockstep.wakestate import assert_overscan_open

frame = OverscanFrame()                                  # 1. borders, guaranteed
band  = WorkStream.repeat(band_writer(11), n=…)          # 3. effect work, register-indirect...
assert_active_zone_clean("\n".join(b.asm for b in band.blocks))   # 6. ...and lint-clean
certify_race(my_band_geometry)                           # 5. the vertical race is certified
assert_within_budget(frame, tail_cost=env.reserve)       # 4. the tail fits the frame slack
frame.build("INTRO.TOS", setup=SETUP, upper=band, tail=my_tail)
assert_overscan_open("INTRO.TOS", frames=range(320, 322))         # 2. borders open, all 4 ws
```

Every line is a guarantee. Four of them (`assert_active_zone_clean`, `certify_race`,
`assert_within_budget`) are **static** — they fail the build before Hatari is ever launched. The
fifth (`assert_overscan_open`) is the emulator confirming, on the actual `.TOS`, that the borders
opened. That is the arc: declare the pegs, pour the work, respect the budget, race the beam, don't
tear — and let the machine, not your eye, tell you it holds.

---

## Where to look next

- `DESIGN.md` — the full design: the cycle model (§1), the directive layer (§2), the Hatari oracle
  (§3), the scheduler (§7), sound (§8).
- `TIMING.md` — the ST timing facts the model rests on: the bus-phase rule, the PSG/MFP wait states,
  the VBL-entry jitter margins.
- `TUTORIAL.md` — the cost engine (`stcyc`) and the raw scheduler surface (`lockstep schedule`).
- The examples are the living proof: `examples/bordopen` (the empty frame) and `examples/aurora`
  (the cycle-exact Aurora capstone).
- The tests are working, runnable versions of every snippet here: `tests/test_skeleton.py`,
  `test_wakestate.py`, `test_budget.py`, `test_beamrace.py`, `test_effects.py`.
```
