# Lockstep — tutorial

A short, practical guide to what works **today**. The cycle engine, the directive
preprocessor, the Hatari oracle, and the **scheduler** (§5, DESIGN §7) are all usable now.
See `DESIGN.md` for the full plan.

## What it is

**Lockstep** owns the cycle bookkeeping for full-sync Atari ST code — counting cycles,
sizing filler to exact targets, measuring the *real* cost in a cycle-exact emulator, and
**packing** your effect code into the gaps between border switches so every scanline is
exactly 512c. It is two layers: the `st68k` cost engine (CLI `stcyc`, §1–4 below) and the
`lockstep` scheduler on top of it (CLI `lockstep`, §5).

## Prerequisites

- Python 3.10+. The cycle engine and the scheduler have **no dependencies**.
- `Pillow` + `numpy` — only for the pixel-level border checks (`lockstep.wakestate`,
  `lockstep.visual`), which read the rendered overscan out of a screenshot.
- `vasmm68k_mot` (vasm, Motorola syntax) on `PATH` — for the Hatari oracle only.
- `hatari` (cycle-exact build) + a TOS/EmuTOS ROM — for the Hatari oracle only.
  Override discovery with `STCYC_HATARI`, `STCYC_VASM`, `STCYC_TOS` env vars.

Run everything as a module from the repo root. The cost engine:

```
python -m st68k <command> ...      # annotate | total | build | check | measure
```

and the scheduler (§5):

```
python -m lockstep schedule <spec>.src.s -o out.s
```

---

## 1. `annotate` — see the cycles

Per-line and running cycle counts for a region. Counts `dcb.w n,$4e71` filler (4n
cycles), multiplies `rept`/`endr`, and resets the running total at a `;@sync` marker.

```
python -m st68k annotate myfile.s
```

```
   8        8c   move.b d3,(a1)       ; run=8c
   9      360c   dcb.w 90,$4e71       ; run=368c
  ...
  26             endr                 ; <<< body=512c x227 = 116224c  run=...
```

The header tells you the cycle model and machine profile.

> Cycle model note: the default engine is the **bus-phase model** (oracle-calibrated
> against Hatari; DESIGN §1.1, TIMING.md) — it threads the 4-cycle bus phase and is exact
> for straight-line code, including ops like `exg` (6c) that the old round-to-4 got wrong.
> Pass `--round4` for the phase-blind round-to-4 estimate; use `measure` (§4) for the
> ground truth that also captures display contention and IO wait states.

### `;@stall N` — declared bus stalls (the blitter as code)

Some cycles the CPU spends are not instructions: start a HOG-mode blit and the CPU is
halted while the blitter owns the bus — a **deterministic** `4·accesses + 8` cycles for a
small blit (4c arbitration in, 4c handback; ≤ 64 bus accesses so the non-HOG alternation
never enters). The model can't infer that from the start write, so you declare it:

```
    move.w  #16,$ffff8a38      ; ycount: arm 16 rows
    move.b  #$c0,$ffff8a3c     ; busy+HOG -> blit runs, CPU halted
    ;@stall 264                 ; 64 accesses x 4c + 8c, on the model's books
```

The line assembles as a comment and costs exactly `N` (4-aligned, phase-preserving)
everywhere the model reads code — `annotate`, budgets, and the scheduler's work items,
which is the point: a blit command becomes a constant-cost block the packer can place
between border pegs (HOWTO_OVERSCAN §10). The number is yours to get right; the oracle
(§4) is the check, and the failure mode is loud — a wrong stall shifts every peg after it.

---

## 2. `build` — turn intent into exact filler

Instead of hand-counting `dcb.w`, declare the intent with `;@` pragmas (which are plain
comments, so the file still assembles under vanilla vasm) and let the tool emit the exact
filler. A whole scanline as intent:

```asm
;@budget 512                 ; this region must total exactly one scanline
    move.b  d3,(a1)          ; left border
    move.b  d4,(a1)
;@pad 376                    ; be exactly at cycle 376 here
    move.b  d4,(a0)          ; right border
    move.b  d3,(a0)
;@pad 444
    move.b  d3,(a1)
    nop
    move.b  d4,(a1)
;@fill                       ; absorb the remainder to hit 512
;@end
```

```
python -m st68k build scanline.src.s -o scanline.s
```

emits real `dcb.w 90,$4e71` / `dcb.w 13,$4e71` / `dcb.w 12,$4e71` at the markers — the
same magic numbers you would have counted by hand, derived instead.

The directives:

| directive | meaning |
|---|---|
| `;@sync` | reset the cycle origin to 0 here |
| `;@pad N` | emit filler so the running count here is exactly N |
| `;@at N` | assert the running count is exactly N (no output; fails the build if off) |
| `;@budget N` / `;@end` | bracket a region that must total exactly N cycles |
| `;@fill` | inside a budget, the point that absorbs the remainder to reach N |

It **fails loudly** rather than mis-size: going over budget, an off-budget `;@at`, a gap
that is not a multiple of 4, or a variable-cost instruction (e.g. an unbalanced branch)
in a sized region all stop the build with a line number and the cycles over/under.

### Balancing a conditional — `;@balance`

In full-sync the two arms of a conditional must cost the **same** cycles so the frame
stays deterministic. `;@balance` does it for you, handling the branch taken/not-taken
asymmetry *and* the bus phase:

```asm
;@balance                ; the next instruction is the conditional branch
    bge.s .alt
    ...work...           ; arm 1 (branch not taken)
    bra.s .end           ; arm 1 ends by branching to the convergence label
;@balance alt
.alt:
    ...idle...           ; arm 2 (branch taken)
;@fill                   ; pad here (put it at the arm's end)
;@balance end
.end:
```

The tool sizes the `;@fill` so both paths reconverge at equal cycles. If the imbalance is
an irreducible 2 cycles (a `Bcc`+`bra` construct can carry one, and 4c nops can't bridge
it), it says so explicitly — adjust an arm by a couple of cycles, as you would by hand.

| directive | meaning |
|---|---|
| `;@balance` | open a balanced conditional; the next instruction is the branch |
| `;@balance alt` | start of the branch-target arm |
| `;@balance end` | convergence point |

## 3. `check` — verify without emitting

```
python -m st68k check scanline.src.s
```

Reports each region's status and exits non-zero on any failure. Drop it in a `Makefile`
to keep a hand-written file honest.

---

## 4. `measure` — the real cycle count (Hatari oracle)

The static engine is an estimate. To get the cycle-exact truth — including the things a
table cannot know (display-window shifter contention, PSG/MFP wait states) — `measure`
assembles your chunk, runs it in headless cycle-exact Hatari, and reads the real cycle
delta plus the beam position.

```
python -m st68k measure chunk.s            # chunk.s holds just the asm to measure
python -m st68k measure chunk.s --setup regs.s   # regs.s runs first (load registers etc.)
```

```
Hatari (cycle-exact): 14c
static estimate:      16c   -> DIFFERS (real vs round-4)
beam:                 line 269 cyc 96 -> line 269 cyc 110
```

`DIFFERS` is informative, not an error: it is where the round-to-4 estimate and reality
part ways (here, two `exg` are 14c, not 16). `beam` is the scanline + intra-line cycle at
each end of the chunk — the raw material for racing the beam.

Notes / limits (today):
- The chunk should be self-contained (registers via `--setup`; no references to data
  that lives outside the measured payload — it runs relocated to a fixed address).
- First boot of Hatari per call takes a few seconds.

---

## 5. `lockstep schedule` — pack work into the line (the scheduler)

The headline. Declare two things — a **line template** (the border-busting events nailed
to exact cycle offsets) and the **work** (your effect logic) — and Lockstep pours the work
into the gaps between events so every scanline closes on exactly 512c. You stop hand-placing
`dcb.w` filler and counting columns; you declare intent and get the unrolled routine.

### As `;@` directives

```asm
;@template allborders 512
;@peg 0 left                 ; left-border flip, at cycle 0
    move.b d3,(a1)
    move.b d4,(a1)
;@peg 376 right              ; right-border 60/50 Hz toggle, at cycle 376
    move.b d4,(a0)
    move.b d3,(a0)
;@peg 444 extra
    move.b d3,(a1)
    nop
    move.b d4,(a1)
;@endtemplate

;@work repeat=39             ; the scroller feed: 39 atomic "column" blocks
    move.l 8(a6),(a6)+
    addq #4,a6
;@endwork

;@schedule allborders lines=3
```

```
python -m lockstep schedule scroller.src.s -o scroller.s
```

emits 3 scanlines, each exactly 512c, with the work poured around the pegs — 11 columns
then the right flip, etc., the same shape you would hand-roll, derived instead.

### The move.l/move.w trick — `;@stepwork`

When a gap isn't a clean multiple of your work unit, a whole-unit pour wastes the remainder
on `nop`s. Declare the work as a **byte budget** plus a menu of move granularities, and the
solver picks the long/word mix that hits the budget *exactly* while filling every gap —
doing useful shifting where nops would otherwise go (aurora.s:850):

```asm
;@stepwork steps=42          ; cover exactly 42 bytes per line
;@move 4                     ; a "long" move: 4 bytes
    move.l 8(a6),(a6)+
    addq #4,a6
;@move 2                     ; a "word" move: 2 bytes
    move.w 8(a6),(a6)+
    addq #4,a6
;@endstepwork

;@schedule allborders lines=3
```

Here the 48c gap before the `extra` peg fills with 2 word-moves (real work) instead of one
long-move plus 16c of nops. The solver minimises `nop` waste; it requires phase-stable moves
(cost a multiple of 4) and counts steps per line. It chooses the *mix* — you still own the
pointer arithmetic across granularities (the `lea`/`addq` reconciliation), as you do by hand.

### Multi-variant screens — `;@screen`

A real screen isn't one template: the top- and bottom-border lines remove the *vertical*
borders with their own switches, and the display itself may split into bands. Name the works
and list the bands; Lockstep packs them into one phase-threaded routine (a band with no
`work=` is border-only — just the switches, the rest nop-filled):

```asm
;@work name=scroll repeat=199
    move.l 8(a6),(a6)+
    addq #4,a6
;@endwork

;@screen
;@segment topborder lines=1                 ; opens the top border, no scroller work
;@segment mid       work=scroll lines=199   ; the display band
;@segment botborder lines=1                 ; opens the bottom border
;@endscreen
```

`lockstep verify` checks *every* line of the screen is on budget, whichever band it's in.

### As a Python API (codegen-native)

The same objects the directives compile to, for when the work is itself generated:

```python
from lockstep import LineTemplate, Peg, WorkStream, StepWork, Move, Segment, pack, pack_schedule

tmpl = LineTemplate([
    Peg(0,   "move.b d3,(a1)\nmove.b d4,(a1)", "left"),
    Peg(376, "move.b d4,(a0)\nmove.b d3,(a0)", "right"),
    Peg(444, "move.b d3,(a1)\nnop\nmove.b d4,(a1)", "extra"),
])
work = WorkStream.repeat("move.l 8(a6),(a6)+\naddq #4,a6", n=39)
res  = pack(tmpl, work, n_lines=3)
print(res.asm)            # the unrolled, 512c-per-line routine

# a multi-band screen: each Segment is (template, work, n_lines)
screen = pack_schedule([
    Segment(topborder, WorkStream([]), 1),   # border-only band
    Segment(tmpl,      work,           199),
    Segment(botborder, WorkStream([]), 1),
])
```

`pack()`/`pack_schedule()` raise `PackError` (with the line/peg/segment) if the template is
over-constrained, a block is bigger than the largest gap, the work doesn't fit, or a gap
can't be sized — never a silent mis-pack.

---

## 6. `OverscanFrame` — the borders as one object

Everything above is about a *line*. The overscan layer is about the *frame*: it promotes the
hard-won border craft — the once-per-frame beam lock, the left stabiliser, the cross-boundary
bottom bust — out of per-demo hand-code and into a toolkit object that is verified rather than
re-derived. Ask for a frame and you get all four borders, on all four wakestates, on a plain STF,
in pure lock-once full-sync (no HBL, no `stop`):

```python
from lockstep.skeleton import OverscanFrame

frame = OverscanFrame()                        # 227 main + 1 bust + 32 bottom = 260 lines, each 512c
frame.build("DEMO.TOS", setup=SETUP, upper=my_effect, tail=my_tail)
```

`build()` wraps your frame in the full-sync bootstrap (supervisor, MFP interrupts off so no timer or
mouse can steal a cycle, your frame installed as the `$70` VBL handler) and assembles a bootable
`.TOS`. `setup` runs once; `upper`/`lower` are work poured into the display bands; `tail` is the
per-frame housekeeping that runs after the picture, in the vertical blank.

Four checks guard it, and three of them run **before** Hatari is ever launched:

```python
from lockstep.budget    import assert_within_budget   # the frame's slack (~8,582c) — is the tail affordable?
from lockstep.effects   import assert_active_zone_clean  # absolute screen writes tear; use (An)
from lockstep.beamrace  import BandGeometry, certify_race  # is every band row written ahead of the beam?
from lockstep.verify    import verify_segments        # every line exactly 512c, in Hatari
from lockstep.wakestate import verify_overscan        # ...and did the borders actually open?

assert_within_budget(frame, tail=my_tail)
report = verify_overscan("DEMO.TOS", wakestates=(1, 2, 3, 4), frames=range(320, 323))
print(report.matrix())
assert report.ok
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

`verify_segments` is the **cycle gate** (every line is 512c — wakestate-invariant, video off, fast);
`verify_overscan` is the **pixel proof** (the borders really opened, on every wakestate, across
*consecutive* frames so a period-2 flicker cannot hide between samples). You want both.

Sound is data-dependent and therefore hostile to a fixed budget, so measure it rather than guess:
`sound.profile_play` runs the whole tune tick by tick in the emulator and reports the worst one, which
is what you reserve — `Peg(400, "jsr (a2)", "play", reserve=env.reserve)`, or, if the worst tick is
bigger than a line's free space, in the frame's tail.

**The full walkthrough is [HOWTO_OVERSCAN.md](HOWTO_OVERSCAN.md)** — an empty frame, then the borders,
then work in the bands, then the budget, the beam race and the active-zone lint, end to end. The
smallest working thing is `examples/bordopen/` (~90 lines, mostly comments).

## Where this is going

The cost engine (§1–4), the scheduler (§5) and the overscan layer (§6) are in place, and the
acceptance test passed: rebuilt from the peg offsets alone, the toolkit re-derives a known-good
demo's hand-counted `dcb.w 90 / 13 / 12` line after line, and every scanline measures exactly 512c in
cycle-exact Hatari. Still open (see [DESIGN.md](DESIGN.md) §6, §7.4): a global cross-line step budget,
register-clobber detection, and folding an SNDH replay in as a first-class recurring peg rather than a
hand-placed call.
