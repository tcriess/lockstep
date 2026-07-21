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

## 8. STE hardware horizontal scroll (the `base_aware` lock)

On the STE you can scroll a wide playfield for free by moving the video base (`$ff8201/03/0d`)
plus the fine-scroll nibble (`$ff8265`) — no CPU/blitter copy. But there is a catch that is
invisible until you try it, and it lives in the beam-lock itself.

The standard sync locks on the **video address counter low byte** (`$ff8209`):

```
    move.w  #$8209,a0          ; a0 sign-extends to $ffff8209
.wait:
    move.b  (a0),d0
    beq.s   .wait              ; lock the instant the counter leaves 0
```

That counter is `(video_base + bytes_fetched) & 0xff`. The moment it leaves 0 is the lock's beam
reference — so it silently **assumes the base low byte is 0**. Give the base a non-zero low byte
(i.e. scroll coarse by anything that is not a whole 256-byte step) and the zero-crossing moves,
the lock lands on the wrong beam cycle, and the borders mistime — you get a per-line shear, or
for some offsets the borders fail to open at all (a black box). The failure is base-value
dependent and does not look like a scroll bug; it looks like the overscan broke.

`SyncConfig(base_aware=True)` fixes it. It reads the current base low byte from `$ff820d` and
keys the lock off `fetched` alone (`cmp.b (a0),d5` against the base low byte, same 2-instruction
loop period as the original so the Aurora fine-sync stays calibrated), then recaptures the phase
after the loop. Verified: static base offsets `0..248` all render clean, and a live base-move
scroll stays clean, all four borders open.

```python
from lockstep.skeleton import OverscanFrame, SyncConfig

frame = OverscanFrame(sync=SyncConfig(base_aware=True))   # STE hardware-hscroll lock
# ... in the tail, move the base each frame; write $ff820d LAST (writing $8201/$8203
#     forces the STE base-low byte to 0, so a low-first order is clobbered):
#         move.b d_high,$ffff8201 / move.b d_mid,$ffff8203 / move.b d_low,$ffff820d
```

**`base_aware` is STE-only and opt-in** (default `False` keeps the wakestate-certified ST path
byte-for-byte). It assumes the STE's deterministic video settle — do **not** pair it with the ST
wakestate use-case, and it does not need the four-wakestate certification (there is no wakestate
lottery on the STE).

### Fine (sub-chunk) scroll: use `$ff8264`, not `$ff8265`

For pixel-smooth scroll you want the STE fine-scroll offset (0–15 px) on top of the coarse
base move. **The documented register `$ff8265` does not work under overscan:** writing a non-zero
`$8265` makes the shifter fetch an extra 16-px group per line, which shifts its line timing so
the resolution/sync border-open toggles (cycles `0/376/444`) miss the GLUE's border-removal
window and the left/right (and bottom) borders **close** — you drop from `H_DE 4<->512` back to a
normal `H_DE 56<->376`. (Watch it with `hatari --trace video_border_h,video_res`.) No `$820f`
line-offset or sync compensation recovers it, because the extra fetch is the whole problem.

The STE has an **undocumented twin at `$ff8264`** — "HSCROLL, no prefetch". It sets the same
0–15 px offset **without** the extra fetch, so the shifter timing doesn't move and the borders
stay open. Fine-scroll to `$8264` and the four-border frame survives; no `$820f` compensation is
needed either (there is no extra fetch to compensate for). The trade is that the right-hand
16-px group isn't pre-fetched — fine on a wide overscan playfield you have content there anyway.

```
    ; scroll position in pixels in d0 — the whole per-frame scroll, in the VBL tail:
    move.w  d0,d2
    and.w   #15,d2
    move.b  d2,$ffff8264       ; FINE: 0..15 px, no-prefetch register (BYTE write — see below)
    moveq   #0,d1
    move.w  d0,d1
    add.w   #15,d1
    lsr.w   #4,d1              ; COARSE: CEIL(d0/16) chunks — rounded UP, see below
    lsl.w   #3,d1              ; * 8 bytes/chunk -> video base, low byte LAST (base_aware sync)
```

Two rules that cost a day each if you learn them the hard way:

- **Byte write, not word.** `move.w` to `$ffff8264` also writes `$8265` (= 0), and the `$8265`
  half wins: the scroll count is zeroed every frame and the fine scroll silently does nothing —
  the image steps in 16-px chunks and looks like the fine write "isn't working".
- **Round the coarse base UP (`ceil(px/16)` chunks), not down.** The no-prefetch register has a
  discontinuity at zero: with `$8264` **non-zero** the shifter fetches the first 16-px group
  *during* display, so the line starts **16 px late**; with `$8264 = 0` it starts on time. Pair a
  floor-rounded base with it and every fine wrap produces a +16/−16 px hiccup pair (it reads as
  "fine and coarse land in different frames" — it isn't; the register pairing is fine). One extra
  chunk of base exactly when fine > 0 — which is just rounding the chunk index up — cancels the
  late start: `fine=0 → 16·c` on time, `fine=k → 16·(c+1)+k−16 = 16·c+k` late — continuous.

Where in the frame the `$8264` write goes does NOT matter (A/B-verified): written in the tail it
applies from the next frame, exactly like the tail-latched base. This is how the STE
side-scroller built on this toolkit does full-overscan pixel-smooth scroll — verified over 41
consecutive frames: exactly +2 px each, across every chunk boundary and the pattern wrap, all
four borders open.

## 9. The zero-jitter idle (`idle="stop"`)

The VBL interrupts whatever the main program is doing, and the 68000 finishes the current
instruction first — so the **VBL entry cycle jitters** by the remaining cycles of that
instruction. The default idle is a 10-cycle spin loop (`bra.s __wait`), which looks harmless but
isn't: the entry phase drifts frame-to-frame by (frame+handler length mod 10), visiting up to 5
distinct phases in a cycle. Everything *after* the beam lock is immune (the lock eats the
jitter), but the **top-border sync dance rides the fixed VBL-entry pause, before the lock** — it
shifts 1:1 with entry jitter. On the STE, a 50 Hz restore drifted into the GLUE's left+2 window
(cycles 36..56 of a fetch line) shreds the whole frame: borders shut, every line shifted 8 bytes
diagonally.

The insidious part is the symptom pattern: with a 10c loop the orbit has period ≤ 5, so you see
**one shredded frame every N ≤ 5 frames — or none at all**, depending on the *total handler
length mod 10*. Add two instructions to your tail and a perfectly clean demo starts glitching
(or vice versa). It looks exactly like whatever you just added broke the video — in the field it
masqueraded as "writing the scroll registers closes the borders" until a nop-padded tail with
**no** register writes shredded on the exact same frames.

Two remedies, both in the toolkit:

- **`emit_program(..., idle="stop")`** (also via `OverscanFrame.build(..., idle="stop")`): idle
  in `stop #$2300` instead of spinning. The 68000 leaves the stopped state with a **fixed**
  interrupt latency, so the VBL enters from the identical machine state every frame — zero entry
  jitter by construction, whatever the handler length. Right for any demo whose main program has
  nothing to do; a custom `main` gets the same guarantee by parking in `stop #$2300` before each
  VBL. Default stays `"spin"` (all historical binaries byte-identical).
- **`SyncConfig(dance_gap=...)`** (the SYNCFIX pattern): widen the dance's safe window so it
  tolerates the jitter instead of eliminating it. Needed when the main program *does* real work
  between frames and can be caught mid-`movem` (jitter spikes ~20+ cycles, beyond what any loop
  choice fixes).

## 10. The blitter inside the raster (`;@stall`)

The blitter is a second bus master, so a blit running while the beam-raced schedule executes
steals the CPU's bus slots — *unaccounted*, that shreds the frame. But the stealing is
**deterministic on the same 4-cycle grid as everything else** (see arnaud-carre's 4KTribute
write-up), which turns a blit into just another constant-cost work item:

- Issue **small HOG-mode blits** (≤ 64 bus accesses, so the 64/64 non-HOG alternation never
  enters the picture). The CPU is halted for exactly `4·accesses + 8` cycles (4c arbitration in,
  4c handback) — during display fetch too; the video DMA already owns its half of the grid.
- Configure every blitter register *outside* the schedule (setup / the vblank tail); the
  in-raster work item is just `ycount` + `start`:

```
    move.w  #16,$ffff8a38      ; ycount: arm 16 rows (x 4-word lines = 64 accesses)
    move.b  #$c0,$ffff8a3c     ; busy+HOG: blit runs, CPU halted
    ;@stall 264                 ; 64 accesses x 4c + 8c — declared, so the packer accounts it
```

`;@stall N` is a cost-model annotation (assembles as a comment): the line costs `N` cycles of
declared bus stall, 4-aligned, phase-preserving. It works anywhere the cycle model reads code —
band work items, `pre`/`post` budgets. The author owns the number and the Hatari oracle is the
check; the failure mode of a wrong stall is unmissable (every peg after it drifts — the whole
frame collapses, verified ±4c around the true value).

One `;@stall` item per gap, 260 lines per frame: ~80k cycles of in-raster blitter throughput,
against ~9k in the vblank tail. This is how a game grows its sprite counts.

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
