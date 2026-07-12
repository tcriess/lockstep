# Lockstep — design

*Pack every line in lockstep with the beam.*

**Lockstep** is a toolkit for writing **fully synchronized** Atari ST code: code that
lives only in the VBL, runs with interrupts masked, and must hit exact cycle counts to
open borders and steer the shifter. (Working directory is still `fullsynctoolbox/`; the
internal cost engine is the `st68k` package with its `stcyc` CLI, and the scheduler is the
`lockstep` package on top — see §4. The full directory/CLI rename is deferred to the end.)

**North star (§7), now built: a full-sync *scheduler*.** The end goal is not to hand-place
code into the gaps between border switches, but to declare the *work* (effect logic) and
the *line template* (the fixed border-busting hardware events at their exact cycle slots)
separately, and have the toolkit weave them together — distributing whole code blocks
across the scanlines so the 512c-per-line budget holds and every border switch lands on
time. The cycle bookkeeping done by hand today (the `dcb.w n,$4e71` fillers, the "even
out the branch" nops, the `; E: 296c (74 nops)` comments) becomes the *cost model the
scheduler runs on*. As of P5 (§6, §7.4) the scheduler exists as the `lockstep` package and
reproduces Aurora's hand-tuned display loop; everything below P1/P2 was substrate for it.

Reference workload: `../aurora/aurora.s` (4kb intro, all borders open, single VBL).

## 0. Goals / non-goals

Goals
- **Schedule** declared work blocks across the frame against a fixed line template so
  borders stay open and every scanline is exactly 512c (§7) — the headline.
- Compute ST-accurate cycle counts for a chunk of 68000 source (the cost model).
- Let the author declare *intent* ("this region is one scanline = 512c", "pad to cycle
  368", "these two branch arms must cost the same") and have the tool emit the exact
  filler to satisfy it — or fail the build if it can't.
- Verify the static numbers against a cycle-exact emulator (Hatari), including the
  display-window shifter contention that a static table can't model.
- Drop into the existing workflow: vasm (`vasmm68k_mot`), a `Makefile`, Python codegen.

Non-goals (for now)
- Not a full 68000 assembler or a vasm replacement. We lean on vasm for assembly,
  symbols, and listings.
- Not a general profiler. Scope is straight-line, interrupts-off sync code.
- Not auto-writing the demo's *logic*. The author writes the effect code; the toolkit
  sizes, places, verifies, and unrolls it.

## 1. The cycle model

### 1.1 First-order rule (an approximation) and the real model

A useful *first-order* estimate of ST instruction time:

    st_cycles ~= round_up_to_multiple_of_4( motorola_68000_cycles )

`motorola_68000_cycles` is the standard MC68000 figure (PRM section 8: base + effective
-address time + per-register/movem terms).

**But round-to-4 is per-instruction and that is wrong in general.** The real rule is
about the **bus phase**, not the instruction: the CPU runs its nominal 68000 cycle
counts, and each bus access (prefetch/read/write) stalls only until the next free
4-aligned MMU slot. Whether a stall happens depends on the running position *mod 4*, so:

- two nominally-6c instructions starting phase-aligned cost **6 + 6 = 12c** (phase walks
  0 -> 2 -> 0), *not* 8 + 8 = 16c. (Observed empirically by tecer; the key correction.)
- per-instruction round-to-4 only happens to be right when instructions are already 4c
  multiples (which keeps the phase at 0) — which is why Aurora's all-4c-multiple hand
  counts looked like clean round-to-4.

So the static engine is a **bus-phase accumulator** — and it is now **built and
oracle-validated** (`cycles.BusPhaseModel`, the default; `--round4` selects the old
phase-blind model). Carry a phase ∈ {0,2} (cumulative cycles mod 4) and charge a +2
realign wait per the calibrated rule:

- a **normal** instruction starting at phase 2 pays **+2**;
- an **odd-EA** instruction (nominal ≡ 2 mod 4 *and* a data-memory operand — i.e. an
  indexed `(d8,An,Xn)` or predecrement EA, whose internal odd step is itself the
  misalignment) instead pays **+2 at phase 0** and self-aligns at phase 2.

Validated cycle-exact against Hatari across ~35 sequences (TIMING.md): `exg`=6,
`exg`×2=14, `exg`×4=30, `exg+nop`=12, `movea.l (d8,An,Xn)`=20, `dbra` steady-state=12,
and mixed straight-line blocks match the oracle exactly. `round_up_to_4` is kept only as
a fast phase-blind estimate. The IO penalties (§1.3) layer on top; display contention is
*not* a CPU cost on STF (§1.3).

The first-order rule is still validated by Aurora's hand-counted (phase-aligned) numbers:

| op                                | Motorola | ST (round-4) | Aurora comment |
|-----------------------------------|---------:|-------------:|----------------|
| `nop`                             |        4 |            4 | filler unit    |
| `dbra` taken (counter >= 0)       |       10 |           12 | "1064x 12 cycles" |
| `dbra` expired (counter = -1)     |       14 |           16 | "1x 16 cycles (counter exp)" |
| `movem.l (an),d0-d3`              |       44 |           44 | "44c"          |
| `movem.l d0-d3,(an)`              |       40 |           40 | "40c"          |
| `move.l (d8,an,xn),an`            |       18 |           20 | "20 c?" (the `?` the tool removes) |
| `lea d16(an),an`                  |        8 |            8 | "8c"           |
| `move.l (a3)+,d4`                 |       12 |           12 | "12c"          |

The author's `?` on the `movea.l 0(a0,d0.w),a0` line is exactly the uncertainty the
tool removes: 18 Motorola -> 20 ST.

### 1.2 Variable-cost instructions

Some ops depend on operands/flow and have no single number:
- `lsl/lsr/asl/.. Dn,Dn` : 6 + 2n (then round-4). Used at aurora.s:203 as the sync
  stabiliser — the count *is* the point.
- `Bcc.s` : 10 taken / 8 not-taken -> ST 12 / 8.
- `dbra`  : 12 looping / 16 expiring (ST).
- `mulu/muls`, `divu/divs` : data-dependent, large.

The tool reports these as a **range** with the taken/not-taken (or n=min..max) called
out, and:
- for `@pad`/`@fill` it only ever emits *fixed-cost* fillers (`nop`=4, `dcb.w`), so the
  padding itself is never ambiguous;
- for verification it asks Hatari for the path actually taken at runtime.

### 1.3 The bus has other masters and slow peripherals

The phase accumulator (§1.1) handles plain CPU-hits-RAM. Everything that makes ST timing
hard is some *other* claimant on the bus. All are modelled as additional state in the
same accumulator (slots stolen / wait states injected), and all are reconciled against
Hatari (§3), whose source is the authoritative, executable spec for the numbers.

1. **Video shifter — does NOT slow the CPU on STF (P0-verified, was an assumption).**
   `video.c` injects zero CPU wait states; the MMU schedules the shifter into bus slots
   the 68000 isn't using, so an instruction costs the same in the display window as in the
   border. The earlier "display contention slows the CPU" framing was wrong for normal
   STF code. (TIMING.md.)

2. **Race-the-beam (screen writes) — a *visual* constraint, not a cost.** A CPU write to
   the screen word for position P on line L produces correct pixels only inside the cycle
   window where the shifter is not fetching P (write safely ahead of, or behind, the
   beam). Per (1) it does not change the write's *cycle cost* — it constrains *where in the
   line the write may be placed*. This ties a block's cycle position to a screen address
   -> a first-class scheduler constraint (§7), verified via Hatari's beam counter
   (HBL/LineCycles). Central to full-sync, where there is no time to draw outside display.
   **✅ Implemented:** `WorkBlock(..., beam=(lo, hi))` — the packer places the block only
   where it runs inside the cycle window (padding up to `lo`, enforcing `hi`), and errors if
   no gap can host it. Directive: `;@work beam=lo:hi`. (`lo=0` is a pure deadline.)

3. **IO peripheral wait states (P0-verified).** Per-access penalties, address-determined:
   PSG `$ff88xx` **+4c** (first access), MFP `$fffaxx` **+4c** (every access), ACIA
   `$fffc0x` **6c + E-clock (0..9c)**. The reason a dosound replay never added up. These
   are deterministic from the operand's absolute address -> an `IoAccessPenalty` layer the
   static engine can add directly (cycles.py), no bus-phase needed. (TIMING.md.)

4. **Blitter / DMA sound — second bus masters (machine-dependent).** STE / Mega ST only;
   plain STF (Aurora's target) has neither. P0-verified blitter model (blitter.c): 4c/8c
   (STE/MegaSTE) arbitration, 64/64-access alternation in non-HOG mode, CPU internal
   cycles overlap the blit. Behind the **machine profile**, later phase.

### 1.4 Machine profile

Cost depends on the target: **STF vs STE** (blitter, DMA sound, extra video registers),
**PAL vs NTSC** (313 vs 263 lines, 50 vs 60 Hz), wakestate. The toolkit carries an
explicit machine profile; the cycle engine, line templates (§7), and Hatari run config
all read from it. Default profile = Aurora's: 1040 STF, PAL, lo-res.

### 1.5 Why cycle-counting is necessary but NOT sufficient (empirical, 2026-06-20 scroller)

The toolkit's whole premise is *cycle exactness*: pack every scanline to exactly 512 CPU
cycles (§7), prove it in Hatari (`lockstep verify`), borders hold. That is **necessary** — a
line that isn't 512c drifts the beam and the borders/display fall apart. But building the
see-through scroller proved it is **far from sufficient**. A scanline can be provably,
measured-in-Hatari exactly 512 CPU cycles and *still* scramble the display. Four reasons the
cycle count is blind to — all of them only visible by running the real thing, video on:

1. **Bus bandwidth — the CPU and the video shifter share the bus.** During the active
   display the shifter is DMA-fetching screen words; CPU memory accesses compete for the
   same bus slots. A line can be 512 CPU cycles (verified with `--disable-video`) yet TEAR
   with video on, because the CPU's accesses *starve the shifter*. There is a budget on the
   **number of bus accesses per scanline × band area**, not on cycles. Measured: an opaque
   in-place shift = **2 bus accesses/column** → clean at 32px; an XOR see-through =
   **3/column** (the extra one is the font read) → drifts above ~24px. The drift is
   proportional to *accesses × area*, and the cycle count cannot see it. (This is the §1.3.1
   "video DMA doesn't slow the CPU" rule's flip side: it doesn't add CPU *cycles*, but the
   CPU *can* steal the shifter's slots — a bandwidth conflict, not a cycle one.)

2. **Bus access *pattern*, not just count.** `move.w abs,abs` (absolute→absolute) TEARS;
   `move.w (a2)+,(a3)` (register-indirect) of the *same cycle cost* is clean. A read-modify-
   write `eor d,(a)` holds the bus differently than a split `move (a),d / eor / move d,(a)`.
   Identical cycle counts, different behaviour — the instruction's bus footprint (how many
   fetch/data cycles, how they interleave with the shifter) is what matters.

3. **The cost MODEL itself was wrong — so even the cycle count was a lie.** The static engine
   over-counted `adda.l #imm,An` (says 16c, real **8c**), `adda.w #imm,An` (12 vs 8), and
   `lea 0(An),An` (8 vs **0** — zero-displacement special case). Each silently *under-pads*
   the line to <512c → drift → whole-frame garble. The packer said 512; the silicon said
   496/504/508. Cycle-counting is only as good as the model, and the model needs per-
   instruction empirical validation. Rule learned: **always `hatari.measure()` the packed
   line == 512c after building any new active-zone effect** — never trust the static number.

4. **Memory layout — not a timing thing at all.** The pre-shifted strip data grew the
   program image to 164KB; on a high TPA load it ran through the magnify buffers at $48000,
   so the pre-render overwrote the code → scramble. A purely *spatial* (RAM-budget) failure
   the cycle counter is completely blind to. (Fix: boot-generate the big data into a known
   free RAM gap, keep the image small.)

So the real model is layered: **cycle-exactness (the floor) + bus-bandwidth budget + bus-
pattern awareness + an oracle-validated cost model + memory-layout discipline + beam-race
placement (§1.3.2)**. The static engine gives the floor; only Hatari — the executable spec
(§3) — reveals the rest. "Count the cycles" gets you a routine that's 512c on paper; "run it
with the shifter on" is what tells you it actually draws. (And see §1.3.2: *where* a screen
write lands relative to the beam is a visual constraint orthogonal to all of the above.)

## 2. Author-facing directives

Pragmas are plain assembler comments prefixed `;@`, so a file with directives **still
assembles unchanged under vanilla vasm** (graceful degradation). The preprocessor
reads `foo.src.s` and writes the vasm input `foo.s`, expanding directives into real
`dcb.w`/`nop` and refreshing cycle comments.

Core concept: a **sync anchor** sets cycle 0; counts are measured forward from it.

| Directive            | Meaning |
|----------------------|---------|
| `;@sync`             | Define cycle origin here; running count resets to 0. |
| `;@pad N`            | Emit `dcb.w`/`nop` filler so the running count *at this point* becomes exactly N. Error if already past N. |
| `;@at N`             | Assert running count == N here. Emits nothing; build fails if off. Documentation + guard. |
| `;@budget N` / `;@end` | Bracket a region that must total exactly N cycles. `;@end` may auto-pad if the region contains one `;@fill`. |
| `;@fill`             | Inside a `;@budget`, the single point that absorbs the remaining cycles to hit the budget. |
| `;@balance` / `;@balance alt` / `;@balance end` | Bracket the two arms of a conditional branch; pad the cheaper arm to match the dearer (charging the branch's not-taken cost to arm 1, taken to arm 2). Encodes the INNER-CODE-1 pattern (§2.2). |
| `;@verify`           | Mark the enclosing region for Hatari ground-truth checking, not just static. |

### 2.1 Worked example — the border scanline

Aurora's debug border loop, today (aurora.s:218-238), is hand-tuned to 512:

```
    rept    227
    move.b  d3,(a1)
    move.b  d4,(a1)
    dcb.w   90,$4e71        ; 360c   <- hand-counted
    move.b  d4,(a0)
    move.b  d3,(a0)
    dcb.w   13,$4e71        ; 52c    <- hand-counted
    move.b  d3,(a1)
    nop
    move.b  d4,(a1)
    dcb.w   12,$4e71        ; 48c    <- hand-counted
    endr
```

With directives the magic numbers become intent, and the tool computes the fillers:

```
    rept    227
;@budget 512
    move.b  d3,(a1)         ; mono
    move.b  d4,(a1)         ; lo-res
;@pad 376                   ; <- right edge here
    move.b  d4,(a0)         ; 60Hz
    move.b  d3,(a0)         ; 50Hz
;@pad 440
    move.b  d3,(a1)
    nop
    move.b  d4,(a1)
;@fill                      ; absorb the rest to 512
;@end
    endr
```

If the author moves a switch by a few cycles, the `dcb.w` counts re-solve; nothing is
hand-recounted. `stcyc check` fails loudly if a region can't be made to fit.

### 2.2 Worked example — branch balancing (IMPLEMENTED, oracle-validated)

The INNER-CODE-1 pattern (aurora.s:297-333): both arms of `bge.s` must cost the same so
the VBL stays deterministic, today balanced with a hand-sized `dcb.w 58,$4e71` and two
"even out" nops. With directives:

```
;@balance                   ; the NEXT instruction is the conditional branch
    bge.s .cnt_ok
    move.l 6(a3),a4         ; arm 1 = fall-through (branch not taken)
    ... INNER CODE 1 ...
    bra.s .cont             ; arm 1 ends by branching to the convergence label
;@balance alt               ; arm 2 = the branch target (branch taken)
.cnt_ok:
;@fill                      ; pad point (at an arm's end)
;@balance end
.cont:
```

The tool detects the conditional branch, charges its **not-taken** cost to arm 1 and its
**taken** cost to arm 2, threads the **bus phase** through each arm (the two arms enter at
*opposite* phases, since taken−nottaken = 2), sizes the single `;@fill` to equalize, and
adds the balanced cost to the enclosing budget. The "two nops to even out the bge/bra
construct" become automatic. Verified: both branch directions measure equal in Hatari.

**The 2-cycle residue is real (and surfaced).** Because nop filler is 4c and a `Bcc`+`bra`
construct carries an irreducible 2-cycle parity, *not every* imbalance is nop-fillable —
the arms must naturally differ by a nop-bridgeable amount at the fill arm's phase (Aurora's
232c inner code does; two register ops often do via the phase realign). When they don't,
the tool fails with an explicit "odd-residue" message rather than silently mis-sizing, and
the author restructures by 2c — exactly the manual judgement that produced the "2 nops".
`@fill` must be the last line of its arm (so the realign doesn't shift downstream phase).

## 3. Hatari ground-truth layer

Two distinct uses of Hatari:

- **As spec (offline, read its source).** Hatari's cycle/bus/IO-access code is the
  authoritative, executable description of the ST timing this toolkit must reproduce —
  the phase model, video contention, and especially the PSG/MFP/blitter wait states
  (§1.3) that aren't in any 68000 manual. Mine the numbers from source once; bake into
  the cost model. *This is the "better source" for the sound timing that never added up.*
- **As oracle (runtime, measure).** Static handles everything except display contention,
  IO wait states, and data-dependent paths. For those, assemble and measure.

Pipeline (the oracle use):

Pipeline:
1. `vasmm68k_mot ... -L listing.txt -o prog.tos` — get the binary, a symbol table, and
   a listing that maps every source line to an address and the actual emitted words.
2. Emit marker symbols around the region of interest (the preprocessor already knows
   where `;@sync` / `;@budget` boundaries are; it injects labels like `__stcyc_m0`).
3. Generate a Hatari debugger script that sets breakpoints at the marker addresses and,
   at each, prints the cycle/beam state, then runs N VBLs and exits.
4. Run Hatari headless in cycle-exact mode (`--compatible`/`--cpu-exact`, sound off,
   fast-forward boot) feeding the debugger script; capture stdout.
5. Parse the cycle/beam deltas between consecutive markers; compare to the static
   numbers; report drift and the *real* per-region cost (contention included).

Beam-aware truth: Hatari exposes per-line / per-frame cycle counters and the current
video position in its debugger expression language (e.g. line-cycle, frame-cycle, HBL,
video-counter variables). For sync code the useful question is often not "how many
cycles" but "where is the beam when I reach marker X" — the same mechanism answers both.
(Exact debugger variable + flag names will be pinned against the installed Hatari build
when this layer is implemented; Hatari is at `/usr/local/bin/hatari`.)

Output reconciliation: a region is reported as `OK` (static == Hatari), `CONTENTION
+Nc` (Hatari higher, inside display — expected, now you know the true number), or
`DRIFT` (mismatch outside display — a bug in the static table or the source).

## 4. Architecture

Two layers: `st68k` is the cycle-exact cost engine + directive preprocessor; `lockstep`
is the scheduler (§7) built on top of it. `lockstep` is the *product*; `st68k` stays the
internal 68000/ST timing library.

```
fullsynctoolbox/                 # working dir (rename to lockstep/ deferred to the end)
  st68k/                         # the cost engine + directive layer (P1–P3)
    m68k_table.py  # nominal 68000 timings (motorola), EA timing, ranges
    cycles.py      # nominal -> ST cycles; bus-phase wait-state model; IO penalties
    parser.py      # minimal vasm-mot line parser: label, mnemonic, size, operands, modes
    preprocess.py  # directive expansion: @sync @pad @at @budget @fill @balance
    annotate.py    # per-line + running cycle counts; block_cycles(); rept/dcb aware
    hatari.py      # vasm build, debugger-script gen, headless run, delta parsing (oracle)
    __main__.py    # stcyc: annotate | total | build | check | measure
  lockstep/                      # the scheduler (P5), on top of st68k
    model.py       # Peg, LineTemplate, WorkBlock, WorkStream; Move, StepWork (step solver)
    packer.py      # pack(): WorkStream -> greedy pour; StepWork -> exact-cover DP. Pure
                   #         placement -> directive intermediate -> preprocess.expand()
    directives.py  # ;@template/@peg/@work/@stepwork/@move/@schedule -> the same model objects
    __main__.py    # lockstep: schedule
  tests/           # test_{cycles,preprocess,balance,hatari,pack}.py
  DESIGN.md  TIMING.md  TUTORIAL.md
```

CLI sketch:
- `stcyc annotate foo.s` — per-line + running cycle counts (read-only).
- `stcyc total foo.s` — total (min..max) cycles of a region.
- `stcyc build foo.src.s -o foo.s` — expand `@sync/@pad/@at/@budget/@fill/@balance`, fail if a region can't fit.
- `stcyc check foo.src.s` — static verification of all directive regions; exit nonzero on drift.
- `stcyc measure chunk.s [--setup regs.s]` — REAL cycles + beam in headless cycle-exact Hatari (P3 oracle).
- `lockstep schedule foo.src.s -o foo.s` — pack a `;@template/@work/@stepwork/@schedule` spec into the unrolled, 512c-per-line routine (P5).

### 4.1 Key decision: parse source vs. use vasm's listing

Reimplementing vasm (macros, `rept/endr`, `if DEBUG`, includes, expressions) is a tar
pit. Hybrid instead:
- **Directives** are a source-level text pass over the lines *between* markers. Sync
  regions are overwhelmingly straight-line, macro-free code, so `parser.py` only needs
  to time literal instruction lines it can see locally — it does not need full macro
  expansion to size a `@pad`.
- **Whole-file annotation, checking, and Hatari markers** use the vasm **listing**
  (`-L`), which already has macro/`rept` expansion, resolved addresses, and emitted
  words. The timing engine reads mnemonics+operands from the listing -> no second
  assembler, and addresses for free.

So `cycles.py` is the shared core; it is fed either raw source lines (directive pass) or
listing lines (annotate/verify pass).

## 5. Open questions (for review)

1. **Output model.** Generated file (`foo.src.s` -> `foo.s`, like the existing `gen_*.s`)
   vs. idempotent in-place rewrite of the padding between markers. Generated is cleaner
   and Makefile-native; in-place keeps one file. Leaning generated.
2. **Directive surface.** Is `@sync/@pad/@at/@budget/@fill/@balance` the right minimal
   set, or do you reason in different units (e.g. always per-line 512, or in
   beam/HBL terms)? Would a `@line` sugar (= `@budget 512`) pull its weight?
3. **Filler / 6c granularity — DE-PRIORITIZED.** tecer tried a 6c filler once, believes
   it didn't work, doesn't want it prioritized. More important: his memory that *specific
   instruction pairs don't round to 4 individually* (6c + 6c = 12c, not 16c) is what
   reframed §1.1 into the bus-phase model. So odd-residue fills, if ever needed, fall out
   of the phase model naturally rather than from a hand-picked magic instruction. Park it.
4. **`rept` regions.** Size the body once and trust `rept`, or expand and verify each
   iteration (matters only if something inside varies per iteration)?
5. **Conditionals.** `if DEBUG` blocks: time the active branch only (driven by the same
   `-D` flags passed to vasm)?
6. **Macros in sync regions.** Acceptable to require sync-critical code to be macro-free
   in the source-level directive pass, and rely on the listing for everything else?
7. **Scope creep check — RESOLVED.** First useful slice = `stcyc annotate` (kill the hand
   comments) + `@pad`/`@fill`. `@balance`, Hatari, and the scheduler come after.
8. **Machine profile granularity.** Start STF/PAL only (Aurora's target) and add STE
   (blitter, DMA sound) + NTSC later? Almost certainly yes.
9. **Beam-race surface.** How should a screen-write block declare its address/beam
   dependency so the scheduler can place it — explicit `;@screen <addr-expr>` tag, or
   inferred from the write target? Affects §7 constraint modelling.

## 6. Phasing

- **P0 — timing research (de-risks everything).** Mine Hatari source for the bus-phase
  model, video contention, and PSG/MFP(/blitter) wait states (§1.3); write the findings
  + citations into a `TIMING.md`. Independent of P1's CPU core, so can run alongside it.
- **P1 — static core.** Bus-phase `cycles.py` + `parser.py` + `tests/` reproducing the
  §1.1 table and the Aurora 512c line. `stcyc annotate`. **(First slice — confirmed.)**
- **P2 — directives. ✅ DONE.** `@sync/@pad/@at/@budget/@fill` and `@balance` (branch-arm
  equalization, bus-phase aware, oracle-validated). `stcyc build/check`.
- **P3 — Hatari oracle. ✅ DONE.** `st68k/hatari.py` + `stcyc measure`: self-relocating
  harness to a fixed address, headless cycle-exact Hatari, PC-breakpoint `FrameCycles`
  deltas + beam (HBL/LineCycles) readout, static-vs-real reconciliation. Empirically
  confirmed the bus-phase model: `exg`=6c (not round-4's 8), `2x exg`=14c, `4x exg`=30c,
  while `4x moveq`=16c matches round-4. `moveq`-clean (4c-multiple) code is exact under
  the first-order model; everything else needs the oracle / the future bus-phase engine.
- **P4 — ergonomics.** Makefile integration, error messages that point at the exact line
  and the cycles over/under.
- **P5 — the scheduler (§7). ✅ MVP DONE.** The `lockstep` package: line template (pegs) +
  work (a poured WorkStream, or a StepWork covered by an exact-cover long/word move mix)
  -> packed, unrolled, 512c-per-line routine. Two front-ends (Python API + `;@` directives)
  over one core; placement reuses `preprocess.expand()` for sizing/phase/odd-residue. Static
  output reproduces Aurora's hand-tuned display loop (§7.4) and is **Hatari-verified** — every
  packed scanline measures exactly 512c on cycle-exact silicon (`lockstep verify`). Multi-variant
  templates (top/bottom-border bands vs mid-screen) via `pack_schedule` / `;@screen`. Still open:
  beam-race constraints, register-clobber detection, global step budget.
- **CAPSTONE — re-implement Aurora through the toolkit** (`examples/aurora/`; Aurora itself is
  never edited). **✅ Cycle-exact done:** `frame.py` re-creates Aurora's complete 260-line display
  region (scroller / font-feed / border-only / scrolltext-palette / bottom-border-bust / bottom
  palette) as a `pack_schedule` band stack — Hatari-verified every line 512c, 0 off-budget; the
  border-only band emits Aurora's exact `dcb.w 90/13/12`. Cycle-faithful, not byte-faithful.
  **✅ Sound done** (§8): `profile_play` measures the PSG replay's worst-case per-tick cost in
  Hatari (the part tecer couldn't account for by hand); `Peg(reserve=W)` reserves it as a sound peg.
  **✅ Visual done** (`visual.py`): run video-on with the real registers + Aurora's beam-sync, the
  generated frame **removes all four borders** — the display fills 56% → 100% of the overscan canvas,
  captured headless via Hatari's `screenshot` and asserted by a test. **Remaining nicety:** beam-race
  placement of the palette writes (§5 Q9) so colour K lands on scanline K — affects the raster-bar
  *colours*, not whether the borders open.

## 7. North star — the full-sync scheduler

The author should write *what to compute* and declare *where the immovable border events
are*, and the toolkit produces the flat, cycle-perfect VBL. Two inputs, one output.

### 7.1 Inputs

**Line template** — the fixed hardware events that bust/hold borders, as pegs in the
512c grid. Each event = (instruction(s), exact cycle offset within the line, line range
it applies to). Examples drawn from Aurora/the border idiom:
- right border: 60Hz/50Hz toggle on `$ff820a` (`move.b d4,(a0)` / `move.b d3,(a0)`) at
  the cycle the shifter checks the right-edge stop;
- left border: lo-res/mono flip on `$ff8260` (`move.b d3,(a1)` / `move.b d4,(a1)`);
- top/bottom: the same flips on the specific lines that remove the vertical borders.
The template is data, reusable across demos — define the standard "all borders open"
template once.

**Work blocks** — the effect logic, each tagged with: cost (from the cycle engine),
*atomic* vs *splittable* (and where it may be split — only at points with no live
timing dependency), clobber/register constraints so the packer doesn't interleave two
blocks that fight over registers, and an optional **beam-race constraint** (§1.3.2): a
screen-writing block carries the screen address it touches, so the packer may only place
it where the beam is in the safe window for that address on that line.

### 7.2 The packer

Treat each scanline as a 512c bin with the template's pegs nailed in place; the gaps
between pegs are free capacity. Walk the work stream and pour blocks into gaps across
consecutive lines:
- a block that fits in the current gap drops in;
- a splittable block straddles a peg (run part, do the border switch, resume);
- an atomic block too big for the remaining gap forces a jump to the next gap, leaving
  filler (which the §2 machinery sizes exactly);
- a beam-race-constrained block is placed only in its safe cycle window (it may force
  earlier blocks to reflow);
- every line is closed to exactly 512c; every peg lands on its cycle.
Output is the unrolled routine (no per-line loop where the schedule varies), the same
shape as the hand-written `rept` body in Aurora but generated and provably on-budget.

### 7.3 Why P1–P4 first

The packer is bin-packing under hard timing constraints — it is only as correct as the
per-block cost (the bus-phase engine, P1), needs the IO/contention numbers (P0) to place
sound and screen writes, and can only be *trusted* once Hatari confirms the packed result
holds through the display window (P3). So the scheduler is last to build but is the point
of all of it.

### 7.4 Status — what the `lockstep` package does today (P5 MVP)

Inputs are built two ways that meet at one core (`packer.pack` / `packer.pack_schedule`):
- **Python API** — `LineTemplate([Peg(offset, asm, label), …], line_len=512)` plus either a
  `WorkStream` (ordered `WorkBlock`s, atomic or `splittable`) or a `StepWork(steps, menu)`.
  A multi-band screen is a list of `Segment(template, work, n_lines)` → `pack_schedule`.
- **`;@` directives** — `;@template/@peg/@endtemplate`, `;@work…/@endwork`, or
  `;@stepwork/@move/@endstepwork`, then `;@schedule <template> lines=N` — or, for a screen
  of several templates, named work (`;@work name=X`) and a `;@screen` / `;@segment <template>
  [work=X] lines=N` / `;@endscreen` block. The parser compiles these into the *same* objects
  (tests assert byte-identical output to the API).

**Multi-variant templates (DESIGN §7.1).** A real screen is a sequence of vertical bands —
top-border lines, the display split into scroller blocks, bottom-border lines — each with its
own line template AND its own work (a band may be border-only: empty work, nop-filled).
`pack_schedule` packs them into one routine, numbering scanlines globally and threading the
bus phase across band boundaries (each line is line_len ≡ 0 mod 4).

**Placement is pure; sizing is reused.** The packer decides which work lands in which gap,
then emits a `;@budget 512 … ;@pad <peg-offset> … ;@fill ;@end` intermediate and hands it to
`preprocess.expand()` — so gap sizing, bus-phase threading, and the odd-residue guard are the
already-tested P1/P2 code, not a second implementation. Every line is 512c (≡0 mod 4), so the
bus phase entering each scanline equals the phase at the sync origin.

- **WorkStream** pours blocks greedily into the gaps between pegs; a block that won't fit the
  current gap falls to the next, leftover → `nop` filler. Reproduces Aurora's hand layout: 11
  scroller columns, then the 8c `nop` remainder, then the right-border flip (aurora.s:843).
- **StepWork** is the move.l/move.w trick (aurora.s:850) made first-class: declare the byte
  budget and a menu of move granularities `Move(asm, steps, cost)`; a per-line exact-cover DP
  (`_solve_line`) chooses the long/word mix that covers *exactly* `steps` while every gap fills
  to its peg, *minimising* `nop` waste — turning would-be filler into useful shifting.

**Deliberate limits (not silently dropped).** The solver picks the *mix* and emits
self-contained moves; cross-granularity pointer reconciliation (Aurora's `lea 18(a6)`, the
"adjustment" `addq`s) is still the author's craft — Lockstep does cycle+step packing, not
data-structure correctness. StepWork currently requires phase-stable moves (cost ≡ 0 mod 4)
and a per-line budget. Beam-race constraints (§5 Q9) and register-clobber detection are still
open.

**Verified on silicon (`lockstep verify`, `verify.py`).** A packed routine is labelled at
each scanline start, run headless in cycle-exact Hatari with **interrupts masked** (full-sync),
and the FrameCycles delta across each line is read back: every line measures exactly 512c, and
the beam enters each line at the *same* intra-line cycle — borders would hold. (Masking matters:
an unmasked run lets an HBL/Timer-C ISR's ~152c land between two markers; `measure()` got away
without it only because its chunks are short. The verifier emits `move #$2700,sr` first.) It
reuses the P3 oracle via a new multi-marker entry point `hatari.measure_markers`, leaving the
proven single-span `measure()` untouched.

## 8. External code blocks — SNDH music players (reference / future)

A SNDH file is a packaged, relocatable 68000 player exposing `init(d0=tune)`, `exit`, and
`play`. `play` is meant to be called once per *tick* by whatever the header declares: VBL
(50/60 Hz) or an MFP timer (often Timer C at 200 Hz). Folding music into a full-sync demo
runs into the architecture head-on, in a way that fits the scheduler (§7) well.

**Interrupts-off forces inline replay.** With the frame masked and hand-timed, a
timer-driven replay can't fire (and would wreck timing if it did). So `play` must be
called **inline, a fixed number of times per frame, at fixed scanlines** — it becomes a
recurring peg in the line template.

**"50 Hz only?" — no, integer-multiple-of-frame-rate.** The replay rate must map to N
fixed inline calls/frame: 50 Hz -> 1, 100/150/200 Hz -> 2/3/4 calls placed at evenly
spaced scanlines (literally "Timer-C-in-VBL"). Rates that aren't an integer multiple of
the frame rate (e.g. a 187.5 Hz timer) can't be cleanly realised -> reject or resample.

**The real crux: `play` has variable cycle cost.** Different notes/effects each tick, and
the cost is dominated by PSG register writes — each **nominal + 4 cycles** (TIMING.md,
verified). In a normal demo the timer absorbs this; in full-sync every cycle is accounted,
so a variable-length `play` blows the budget. Fix = **reserve the worst-case `play` budget
and pad to it every frame**. The Hatari oracle (§3) profiles `play` across the *entire
tune* to find the per-call worst case (and per scanline-slot), which the scheduler then
reserves.

**✅ Profiler DONE (`lockstep/sound.py: profile_play`).** Runs the replay across the tune
tick-by-tick in cycle-exact Hatari (reusing `measure_markers`, interrupts masked) and returns
the per-tick `PlayEnvelope` (min / typical / worst, and `.reserve` = worst rounded to a
multiple of 4). This pins the number that "never added up" by hand — the PSG +4c wait states
are in the measurement. Demo: `examples/aurora/sound.py`.

**✅ Reserved peg DONE (model A).** `Peg(offset, call, reserve=W)` — the packer reserves W
cycles for the slot (footprint = W, pours no work into it; size W from `profile_play(...).reserve`).
The line stays exactly 512c statically with the slot carved out, so the borders and work place
around it; N pegs give N×framerate (100/150/200 Hz). **Runtime constancy is the player's job**
(a worst-case-padded player, or a beam-wait to the slot end that the verifier can't exercise
under `--disable-video`) — Lockstep reserves the budget; it can't make a variable call constant.
**Real constraint surfaced:** W must fit a line's free space; the demo's worst tick (532c) exceeds
one line (~480c free), so a loud 50 Hz replay must split into N smaller ticks or run in the slack.
That slack model — Aurora's own `dosound` (aurora.s:1214, "the time critical stuff is done, and
we still have a few cycles for sound") runs the variable replay in the **post-display slack**,
gated by a frame counter, letting the next frame's beam-sync re-absorb the variation — is the
alternative (B), and belongs with the conductor (frame structure: display + sound tail + sync).

**As a work block (§7.1):** SNDH `play` is a black box with a Hatari-measured cycle
envelope (min/typical/worst), a reserved worst-case budget, full register clobber (the
SNDH ABI lets `play` trash everything; caller saves), and PSG access cost folded in. The
scheduler slots N copies at fixed lines. STE DMA-sound SNDH (TB/DMA tag) is separate — the
DMA hardware plays autonomously; `play` only feeds it.

Open: SNDH timer-tag parsing (which tunes are N×framerate and thus usable), and whether to
*relocate + call* the player as-is vs. extract its `play` for tighter scheduling.

## 9. The overscan authoring layer (W1–W5, built 2026-07-11)

Above the scheduler sits a layer that promotes the hard-won overscan craft — previously
hand-coded in `examples/bordopen` and re-derived per demo — into first-class, *verified* toolkit
objects. The full walkthrough is **`HOWTO_OVERSCAN.md`**; the plan and status are
the sections below. In brief:

- **`lockstep/skeleton.py` — `OverscanFrame` (W1).** The robust four-border-open frame as an
  object: it owns the once-per-frame `$8209` MMU lock + fine-sync, the all-borders template, the
  left stabiliser, and the cross-boundary bottom bust; the author supplies the `setup` and the band
  work. `bordopen` and `aurora` drive the *same* object. Byte-transparent extraction — the
  shipped `.TOS` binaries are unchanged.
- **`lockstep/wakestate.py` — `verify_overscan` (W2).** The border-open guarantee, made a number:
  runs a built `.TOS` across ws1–4 × consecutive frames, detects each of the four borders from the
  rendered overscan edge bands, and reports a wakestate × border matrix with period-2 flicker
  flagged. Certifies a real demo under load (Aurora: all four borders on all four ws). This is the
  *pixel proof*; `verify.verify_segments` is the *cycle gate* (every line 512c, wakestate-invariant).
- **`lockstep/budget.py` — `frame_budget` (W3).** The frame-level cost model the line-level engine
  lacked: it costs the fixed skeleton (handler wrap + sync prelude incl. the pause loop + bands) and
  exposes `slack_budget` (~8.6kc), the free cycles for the post-display tail. Warns OVER / RISK /
  UNRESERVED *before Hatari* — the ≈672c "tail eats the slack → top border silently closes"
  regression is now a build-time number. The slack boundary is silicon-verified.
- **`lockstep/beamrace.py` — `BandGeometry` (W4).** The *vertical* beam-race, checked: a band
  written row-by-row down the screen must lay each row down ahead of the beam. Certifies the race
  (`top_min > work_start + height·(LPR−1)`) and the fit (clears the bottom-border structure),
  naming the first violating row. Replaces a trusted hand comment with a certificate. Orthogonal
  to the packer's
  intra-line `WorkBlock(beam=(lo,hi))` window (§1.3.2), which is unchanged.
- **`lockstep/effects.py` — the active-zone lint + recipes (W5).** `active_zone_lint` enforces the
  §1.5 tear rule (absolute display writes tear; register-indirect is clean) while allowing the
  required absolute writes to the hardware registers; `band_writer` / `palette_split` are lint-clean
  generators of the see-through-scroller and late-line-palette-split idioms.

Design invariants held throughout: **correct by reuse** (every new check calls `st68k`/the packer,
never a second cost model), **the emulator is the oracle** (each guarantee terminates in a headless
Hatari measurement or a static check validated against one), and **the examples are the proof** (the
migration keeps the shipped binaries byte-identical while the bespoke skeleton/scripts disappear).
