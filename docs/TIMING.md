# TIMING.md — Atari ST cycle / bus-timing model (as modelled by Hatari)

> ## ✅ VERIFIED FINDINGS (main session, from Hatari source)
>
> The original research banner below was written by a *sandboxed subagent* that had no
> network and no out-of-workdir reads. The **main session does** have both (Hatari
> v2.6.0-devel binary present; `raw.githubusercontent.com/hatari/hatari` reachable). The
> following are read directly from source and supersede the "could not obtain" banner for
> the topics covered. The rest of this file remains a research map / checklist (still
> useful) until each item is likewise verified.
>
> ### YM2149 / PSG wait states — the dosound mystery, solved  `[VERIFIED: src/psg.c:116-171]`
>
> Model Hatari implements (and lists verified-on-hardware examples for):
> - **Any instruction that accesses a valid YM2149 register ($ff8800/$ff8802, and the
>   $ff8801/$ff8803 shadows for .b/movep) takes an initial +4-cycle wait state on its
>   first access** — whether it writes 1 register (`move.b`) or up to 4 (`movep.l`).
> - Further accesses by the *same* instruction add nothing — **except MOVEM**, which adds
>   +4 each time it reaches another pair of registers. Verified table (psg.c:124-155):
>   ```
>   move.b d1,(a1)      8 + 4  = 12      move.l d1,(a1)     12 + 4  = 16
>   move.w d1,(a1)      8 + 4  = 12      movep.w d1,(a1)    16 + 4  = 20
>   movep.l d1,(a1)    24 + 4  = 28      clr.b (a1)         12 + 8  = 20  (read+write)
>   movem.l d1,(a1)    16 + 4  = 20      movem.l d1-d3,(a1) 32 + 8  = 40
>   movem.l d1-d5,(a1) 48 + 12 = 60      movem.l d0-d7,(a1) 72 + 16 = 88
>   ```
> - **Consequence for sync code:** a dosound replay is a stream of `move.b dn,$ff8800`
>   (reg select) + `move.b dn,$ff8802` (data) — *each* such instruction is nominal+4. A
>   select+write pair costs +8 over what a naïve count gives. This is the discrepancy
>   tecer could never reconcile by hand.
> - **Caveat the source itself states (psg.c:120-122):** this +4/round-to-4 scheme "only
>   works when the cpu rounds all cycles to the next multiple of 4 … it will not work when
>   running in cycle exact mode." → independent confirmation of DESIGN §1.1: round-to-4 is
>   the *non-exact* approximation; cycle-exact mode computes finer (bus-phase) internal
>   cycles. For the toolkit: model PSG access as nominal + 4 (first access; MOVEM pair
>   rule) in the static engine, and let the Hatari oracle settle the cycle-exact cases.
>
> ### CPU bus-phase — measured directly (Hatari oracle, `stcyc measure`)
>
> Cycle-exact measurements that settle DESIGN §1.1 empirically (cpu-exact mode):
> - `exg d0,d1` = **6c** (round-to-4 would say 8). Round-to-4 is wrong even for ONE
>   instruction whose nominal time isn't a 4c multiple.
> - `exg`×2 = **14c**, `exg`×4 = **30c** (= 6 + 8·(n−1)) — a wait state hits the chained
>   ones. Note this refines the "6+6=12" memory: it's 6+8=14, a phase effect.
> - `moveq`×4 = **16c** — matches round-to-4 exactly (moveq is a clean 4c op).
> So: round-to-4 is exact for 4c-multiple instructions, wrong otherwise. `FrameCycles`
> deltas + `HBL`/`LineCycles` (beam position) come straight from Hatari's `DebugInfo_Default`.
>
> **The bus-phase model (built, `cycles.BusPhaseModel`, oracle-calibrated).** Track phase
> ∈ {0,2} = cumulative cycles mod 4. Per instruction:
> - **normal**: cost = nominal + 2·[phase == 2]   (realign the next bus access)
> - **odd-EA** (nominal ≡ 2 mod 4 AND a data-memory operand — indexed/predecrement):
>   cost = nominal + 2·[phase == 0]   (its internal odd step *is* the misalignment, so it
>   self-aligns when entered at phase 2)
> - branches/jumps are "normal" (their label operand is a target, not a data EA).
>
> Validated cycle-exact against the oracle over ~35 sequences, e.g. `exg`=6, `exg`×2=14,
> `exg`×4=30, `exg+nop`=12, `nop+exg`=10, `movea.l 0(a0,d0.w),a5`=20, `exg+movea.l idx`=24,
> `dbra` steady-state loop=12 (the source of Aurora's "12"), and mixed straight-line blocks
> (26/40/48/40/48) all match. IO penalties (PSG/MFP +4) layer on top.
>
> ### IO peripheral access wait states  `[VERIFIED from source]`
>
> All ST IO-register access penalties funnel through `M68000_WaitState(n)`. Per device:
>
> | device        | addresses        | penalty | source |
> |---------------|------------------|---------|--------|
> | PSG / YM2149  | `$ff8800/02`     | **+4c** first access (MOVEM: +4/pair) | psg.c:158-171 |
> | MFP 68901     | `$fffaxx`        | **+4c** flat, every register r/w | mfp.c (every handler: `M68000_WaitState(4)`) |
> | ACIA 6850     | `$fffc00-06` (kbd/MIDI) | **6c + E-clock sync (0..9c)**, first access of the instruction | acia.c:547 `ACIA_AddWaitCycles` (`+ M68000_WaitEClock()`) |
>
> These are deterministic per-access (except the ACIA E-clock term) and depend only on
> *which* address the operand touches — so the static engine can add them directly once it
> classifies an operand's absolute address into the PSG/MFP/ACIA ranges. (Planned: an
> `IoAccessPenalty` layer in cycles.py.)
>
> ### No CPU/shifter contention on STF  `[VERIFIED]`
>
> `video.c` contains **zero** `M68000_WaitState` / `M68000_AddCycle` / CPU-wait calls — the
> shifter does not slow the CPU during active display on a standard STF. The MMU schedules
> the shifter into bus slots the 68000 isn't using, so a given instruction costs the same
> in the display window as in the border. This **corrects** the earlier "display contention
> slows the CPU" assumption: it does not (for normal code). *Race-the-beam remains a visual
> -correctness constraint* — which scanline-cycle a screen write lands at, relative to where
> the shifter reads that address — not a CPU timing penalty. Verifiable with the oracle by
> measuring the same chunk at different beam positions.
>
> ### Blitter bus sharing (STE / MegaSTE)  `[VERIFIED: blitter.c:19-64]`
>
> The blitter is a second bus master with a cycle-exact sharing model:
> - Start latency: the CPU can still run ~4c after starting the blit; then bus arbitration
>   takes **4c (STE) / 8c (MegaSTE)** with no CPU or blitter access; then the blitter owns
>   the bus. Handback to the CPU costs **4c** on both.
> - Non-HOG mode: the blitter uses the bus for **64 accesses, then yields 64 to the CPU**,
>   alternating (a blitter bug sometimes makes it 63). HOG mode: blitter holds the bus until
>   done.
> - CPU *internal* cycles (div/mul prefetch-free work) run **in parallel** with the blit, so
>   costly instructions can overlap and save wall-clock. Whether a CPU instruction's bus
>   accesses interleave depends on its read/write/prefetch order (blitter.c:47-57).
> STF has no blitter (it's STE/MegaSTE/MegaST hardware) — gated behind the machine profile.
>
> ### CPU cycle model  `[VERIFIED: cycles.c header]`
>
> In **cycle-exact** mode Hatari uses the **WinUAE CPU core's sub-cycle timing** (not
> heuristics) — this is the authority the oracle taps, and the source of the bus-phase
> behaviour measured above (`exg`=6c etc.). The non-cycle-exact path uses the round-to-4
> heuristic (`CurrentInstrCycles`), and `BusMode` tracks cpu-vs-blitter bus ownership.


> ## ⚠️ PROVENANCE / VERIFICATION STATUS — READ FIRST
>
> **(Superseded for PSG — see the VERIFIED FINDINGS box above.)** The Hatari source could
> not be obtained *by the sandboxed subagent*; the main session reached it. The original
> subagent notes follow. Every avenue the subagent had was unavailable:
>
> - **No Hatari source on disk.** Reads outside the working directory
>   (`/home/spanz/development/atari/fullsynctoolbox`) are denied by the sandbox, and the
>   working directory contains only `DESIGN.md` and `.claude/`. There is no vendored
>   `hatari/src/` here.
> - **No network.** `git clone`, `WebFetch`, and `WebSearch` are all denied, so I could
>   not pull `raw.githubusercontent.com/hatari/hatari` or `apt-get source hatari`.
> - **No access to the installed binary or manpage.** `/usr/local/bin/hatari`,
>   `hatari --version`, `hatari --help`, and `man hatari` all live outside the working
>   directory and are denied. I could not even read the help text.
>
> **Consequence:** I could not open a single line of Hatari source, so I cannot give you
> *verified* file+line citations. What follows is written from my own knowledge of
> Hatari's source architecture and of documented Atari ST hardware behaviour. **Treat
> every Hatari file/function/line reference below as a POINTER TO LOOK, not a verified
> citation.** Each such pointer is tagged **[UNVERIFIED — confirm in source]**. Concrete
> cycle numbers are tagged by confidence:
>
> - **[HW — well documented]** — Atari ST hardware behaviour that is independently
>   well established (e.g. the 4-cycle bus, the 50 Hz PAL line = 512 cycles). High
>   confidence, but still not read out of *this* Hatari build.
> - **[HATARI — from memory]** — a value I recall Hatari using, *not re-read here*.
>   Medium confidence; verify the constant before baking it into the cost table.
> - **[UNVERIFIED]** — a specific claim about *where in the source* something lives, or a
>   number I am not confident about. Verify before use.
>
> **Do not bake any number from this document into `cycles.py` without re-deriving it
> from the actual Hatari source.** This file is a research map and a checklist of exactly
> which functions to open and what to look for, not a substitute for reading the source.
> The whole point of the §3 "Hatari as spec" approach in DESIGN.md is that the emulator
> is the executable spec — and I was unable to execute or read it here.
>
> The user's priority question — **PSG/YM2149 access wait states** — is answered below at
> a hardware level with high confidence (the rounding-to-the-4-cycle-grid-plus-extra
> behaviour is well documented), but the *exact constant Hatari adds* must be confirmed in
> `src/psg.c` / `src/ioMem*.c`. See §4 and the Open/uncertain section.

---

## 0. How to verify this file (do this first when you have source)

When you can read the source, the fastest way to turn this document from "map" into
"verified spec" is to grep the tree for the wait-state primitives and read every call
site. The whole timing model funnels through a small number of functions:

```
# the CPU-side primitive that injects bus wait states:
grep -rn "M68000_WaitState"            src/
grep -rn "M68000_SyncCpuBus"           src/      # bus / E-clock sync entry points
grep -rn "M68000_AddCycles"            src/
grep -rn "BusCyclePenalty"             src/      # WinUAE-core penalty hook
grep -rn "CurrentInstrCycles"          src/cpu/  # (note Hatari's spelling)

# device-access cost hooks (PSG / MFP / IO):
grep -rn "WaitState\|AddCycles\|nCyclesMainCounter" src/psg.c src/mfp.c src/ioMem*.c

# the 4-cycle grid / MMU arbitration & video contention:
grep -rn "WaitStateValue\|nWaitStateCycles\|CYCLES_PER_LINE\|nCyclesPerLine" src/

# the cycle bookkeeping core:
less src/cycles.c                                 # M68000 cycle counters
less src/cycInt.c                                 # internal interrupt scheduler
less src/cpu/custom.c  src/cpu/newcpu.c           # WinUAE CE core
```

The five primitives above are the load-bearing ones. If you read every call site of
`M68000_WaitState` and `M68000_SyncCpuBus`, you will have found essentially every place
the ST adds non-68000 cycles. Everything in §2–§7 below is an annotation of what you
should expect to find at those call sites.

---

## 1. Big picture: two CPU cores, and which one carries the ST timing

Hatari embeds the **WinUAE 68000 core** (under `src/cpu/`, files such as `newcpu.c`,
`cpummu.c`, `custom.c`, `cpu_prefetch.h`, plus generated `cpuemu_*.c`). It also keeps a
legacy "old UAE" path, but cycle-exact ST work uses the WinUAE core.

Two layers cooperate:

1. **The 68000 core (`src/cpu/`)** computes the *nominal* MC68000 cycle cost of each
   instruction — base + effective-address + per-register/movem terms — exactly the
   "Motorola PRM section 8" numbers DESIGN.md §1.1 calls `motorola_68000_cycles`. In
   **cycle-exact mode** it does this at bus-cycle granularity (prefetch, read, write as
   separate bus phases), not just a lump sum per instruction. **[UNVERIFIED — confirm the
   per-phase accounting in `cpu/cpuemu_*` and `cpu_prefetch.h`.]**

2. **Hatari's ST glue (`src/m68000.c`, `src/cycles.c`, `src/cycInt.c`, `src/video.c`,
   plus the device files)** wraps each bus access with the **ST-specific** behaviour the
   bare 68000 core does not know about: the 4-cycle MMU bus slot, video shifter
   contention, and the slow peripherals (PSG, MFP). It does this through
   `M68000_WaitState(n)` (add `n` wait-state cycles to the current instruction) and the
   bus-sync helpers. **[UNVERIFIED — confirm names in `src/m68000.c` / `src/m68000.h`.]**

**This split is exactly DESIGN.md's split:** the 68000 core gives you
`motorola_68000_cycles`; Hatari's glue is the bus-phase accumulator that turns it into
`st_cycles`. Your `cycles.py` is re-implementing layer (2).

### 1.1 Cycle-exact flags (relevant Hatari options)

To make Hatari run the model described here you must enable the cycle-exact path; in
older-default mode it uses cheaper approximations. The relevant options
**[HATARI — from memory, confirm with `--help`]**:

- `--cpu-exact <0|1>` (a.k.a. "prefetch / cycle-exact CPU")
- `--compatible <0|1>` (prefetch emulation)
- `--cycle-exact` / per-machine "MMU + cycle exact" toggle in some builds
- `--mmu <0|1>` (only on machines that have one; the ST's "MMU" here is the **GLUE/MMU
  bus arbiter**, not a 68030 PMMU — do not confuse them)

The `tos`/machine type (`--machine st|ste|megast|...`) selects whether blitter and DMA
sound exist (see §6, §7). **[UNVERIFIED — exact flag spelling; I could not read `--help`.]**

---

## 2. CPU ↔ RAM bus timing / wait states (the 4-cycle grid)

### 2.1 The hardware rule (what Hatari is reproducing)

**[HW — well documented]** The ST's GLUE+MMU run the whole machine off a **8 MHz** master
clock and arbitrate the RAM bus into **4-cycle slots**. The 68000 (also 8 MHz) shares the
bus with the **video shifter** and (depending on the area of the screen) the
shifter takes some of those slots. A 68000 bus cycle is nominally 4 clocks, but the
processor can only *start* a bus access on a slot boundary the MMU grants it. So:

- Every memory access is effectively **aligned up to the next free 4-cycle slot**.
- The number of wait states inserted therefore depends on **the CPU's current phase mod
  4**, *not* on the instruction in isolation.

This is precisely the correction in DESIGN.md §1.1: **round-to-4 is per-instruction and
wrong in general; the real quantity is a running phase mod 4.** Two nominally-6c
instructions starting phase-aligned cost 6 + 6 = 12c because the phase walks 0 → 2 → 0 and
neither access needs a full extra slot; only when an access lands mid-slot does a wait
state appear. **[HW — this is the documented STF bus behaviour and matches the tecer
observation in DESIGN.md.]**

### 2.2 Where Hatari does this

**[UNVERIFIED — pointers to confirm]**

- **`src/cycles.c`** — Hatari's cycle counters (`Cycles_GetCounter`,
  `Cycles_GetCounterOnReadAccess` / `...OnWriteAccess`, and the `nCyclesMainCounter` /
  per-instruction accumulation). This is where a bus access is mapped to a *cycle
  position within the current line*, which is what makes the cost phase-dependent. **Open
  `Cycles_GetCounterOnWriteAccess` first** — its whole job is "given where we are in the
  instruction, what cycle does this access actually happen at," i.e. the phase.
- **`src/m68000.c`** — `M68000_WaitState()` and the `M68000_AddCycles*` family. The
  WinUAE core calls back into here (or into a `BusCyclePenalty`-style hook) to add ST wait
  states. **Open every caller of `M68000_WaitState`.**
- **`src/cpu/custom.c` / `cpu/newcpu.c`** — the WinUAE side: `do_cycles`, the prefetch
  pipeline, and the per-bus-access hook that lets Hatari inject the 4-cycle alignment.
- **`src/cpu/cpummu*.c`** — despite the name this is mostly 68030/68040 PMMU; the ST's
  bus arbitration is **not** here. Do not be misled by the filename. The ST 4-cycle slot
  logic is in the video/MMU glue, see §3.

### 2.3 What to extract for `cycles.py`

The model your accumulator needs from this section:

- Maintain a **running cycle position** (DESIGN.md's phase, but track the absolute
  line-cycle, not just mod 4 — you need the absolute value for §3 contention anyway).
- For each instruction, take the 68000 nominal cost from the core/PRM, but charge each
  **bus access** (prefetch words, operand reads, operand writes) at the next 4-aligned
  slot. The *instruction* total is then "nominal + sum of per-access alignment waits,"
  which is generally **not** the same as rounding the instruction total up to 4.
- The clean case (all instructions already 4c multiples → phase stays 0 → no extra
  waits → looks exactly like round-to-4) is why Aurora's hand counts matched round-to-4.

---

## 3. Video shifter contention (display window steals the bus)

### 3.1 Hardware rule

**[HW — well documented]** During the **active display window** the shifter fetches screen
RAM and consumes bus slots, so CPU accesses to RAM in that window can stall waiting for a
free slot. Outside the display (border, blank, opened-border regions), the shifter is not
fetching, so the CPU has the bus to itself and accesses are "clean" (just the §2 4-cycle
grid, no extra contention). This is exactly DESIGN.md §1.3.1.

Key ST geometry numbers your model needs **[HW]**:

- **512 cycles per scanline** (PAL 50 Hz, lo-res) — the line budget DESIGN.md is built on.
- **313 lines/frame PAL**, 263 NTSC; 50 Hz vs 60 Hz. (DESIGN.md §1.4.)
- The display window, border start/stop, and the exact cycle positions where the
  shifter checks the left/right-edge "stop" registers (`$ff8260`, `$ff820a`) are the pegs
  the line template (DESIGN.md §7) nails down.

### 3.2 Where Hatari does this — **this is the richest timing file in the tree**

**`src/video.c`** is the heart of ST timing. **[UNVERIFIED — pointers]**

- A big table / set of `#define`s gives the **cycle positions of every video event** on a
  line: `LINE_START_CYCLE`, `LINE_END_CYCLE`, `LINE_LEFT_BORDER`, `LINE_RIGHT_BORDER`,
  the HBL and timer-B positions, the 50/60 Hz and lo/hi-res switch deadlines, and the
  "remove left/right/top/bottom border" windows. **These constants ARE your line
  template.** Find them and copy the geometry, not guess it.
- `Video_GetPosition()` / `Video_GetHBLPos()` / the `nCyclesPerLine`,
  `ScreenBorderMask`, `LineStartCycle`/`LineEndCycle` variables give the beam position as
  a function of the cycle counter. This is the same `Cycles_GetCounter` value from §2,
  reinterpreted as (line, cycle-in-line).
- The **contention** itself: look for where a memory access in the display window adds
  cycles. In Hatari this is often modelled by the cycle counter advancing differently
  inside the display, and/or by the shifter "stealing" via the `Video_` interrupt
  handlers, rather than a single `WaitState(n)` per access. **Confirm exactly how the
  steal is charged** — whether it is per-CPU-access wait states or a coarser per-line
  accounting — because that determines whether your static engine can predict it or
  whether you must defer to the Hatari oracle (DESIGN.md §3 says contention is the one
  thing the static table can't fully model — verify that assumption against `video.c`).
- **Border-opening timing:** the windows in which writing `$ff820a`/`$ff8260`/`$ff8260`
  removes a border are defined as cycle comparisons in `video.c` (e.g.
  `Video_StoreResolution`, the 60Hz/50Hz handlers, `Video_RemoveLeftRightBorder`-style
  logic). The exact cycle each switch must land on (DESIGN.md §7's "the cycle the shifter
  checks the right-edge stop") is **in these comparisons** — extract them verbatim.

### 3.3 What to extract

- The full per-line **cycle-position table** (border/display/HBL/timer-B positions) → this
  is the line template grid for the scheduler.
- The **border-removal windows** (which cycle a switch must hit) → the pegs.
- The **contention charge model** → either a per-access wait formula you can fold into the
  §2 accumulator, or a "defer to Hatari oracle" flag if it's not cleanly per-access.

---

## 4. PSG / YM2149 access wait states — **PRIORITY**

### 4.1 The hardware reason it never adds up by hand

**[HW — well documented]** The YM2149 PSG is clocked at **2 MHz**, i.e. **one quarter of
the 8 MHz CPU clock**. A CPU access to the sound chip registers at
**`$ff8800` (register select / read)** and **`$ff8802` (data write)** must be
**synchronised to the slow 2 MHz PSG clock**. The bus access cannot complete until the PSG
is ready on its own clock edge, so the MMU inserts wait states to stretch the CPU access
out to a 2 MHz boundary. **This is the device-specific wait state DESIGN.md §1.3.3 is
about, and it is exactly why a hand count of a `dosound`/sound-replay routine never adds
up: every `move.b dx,$ff8800` and `move.b dx,$ff8802` costs more than the 68000 figure
plus the 4-cycle grid would suggest.**

In practical terms, because the chip runs at 2 MHz, a PSG access is rounded up to the next
**2 MHz** boundary — i.e. effectively to a multiple that can be **larger than the 4-cycle
RAM grid** (the 2 MHz period is 4 CPU clocks, but the sync-up to the chip's *internal*
phase, combined with the access already being a slow `move.b` to IO space, is what adds
the surprise cycles). The precise extra-cycle constant is the thing to pull from
`src/psg.c`.

### 4.2 What I recall Hatari doing — **CONFIRM THESE NUMBERS**

**[HATARI — from memory; the exact constant MUST be re-read from `src/psg.c`/`ioMem*.c`]**

- Hatari handles `$ff8800`–`$ff8803` through IO handlers in **`src/psg.c`**:
  `PSG_ff8800_ReadByte` / `PSG_ff8800_WriteByte` (register select + read),
  `PSG_ff8802_WriteByte` (data write), with the `PSG_Void_*` stubs for the
  mirror/unused addresses. **[UNVERIFIED — exact handler names.]**
- These handlers call into the cycle machinery to **add wait-state cycles** for the 2 MHz
  sync — look for a call to `M68000_WaitState(...)` or an explicit add to the cycle
  counter inside the PSG IO handlers, and for a comment mentioning **"2 MHz"** or
  **"round to 4"** there. **The argument to that call is the number you want.**
- My recollection is that the PSG access is **rounded up to a multiple of 4 CPU cycles**
  by the IO subsystem (the IO bus is itself on the 4-cycle grid), **and the YM-specific
  sync adds further cycles on top**. I do **not** have a confident single integer for "a
  PSG write costs N extra cycles" — **this is the #1 thing to read out of the source.**
  Do not let me hand you a fabricated constant here.

### 4.3 Where exactly to look (priority order)

```
src/psg.c        -> PSG_ff8800_WriteByte / PSG_ff8802_WriteByte / PSG_ff8800_ReadByte
                    look INSIDE each for: M68000_WaitState(...)  or  += <n>
                    and any comment with "2 MHz" / "sync" / "wait"
src/ioMem.c      -> the dispatcher that calls those handlers; check whether a generic
src/ioMemTabST.c    IO-access wait state is added for ALL $ff8800-range accesses here
src/ioMemTabSTE.c   (i.e. the cost might be in the IO table layer, not in psg.c itself).
src/m68000.c     -> M68000_WaitState definition: confirm it adds to the CURRENT
                    instruction's cycle total (so it composes with the §2 phase).
```

**Deliverable for the cost table:** a per-access cost for `$ff8800` read, `$ff8800`
write, `$ff8802` write (and the `$ff8801/$ff8803` mirrors) expressed as
"68000 nominal + IO/2MHz wait = total," taken **verbatim** from the handler. Treat the
sound-replay routine in the Aurora reference as the acceptance test: sum these per-access
costs over the replay and it should match Hatari's measured cycles (DESIGN.md §3 oracle).

---

## 5. MFP 68901 access timing ($fffaxx)

### 5.1 Hardware reason

**[HW — well documented]** The MC68901 MFP is a **6800-family-style peripheral** on the
ST. Two things make its accesses slow:

1. It sits on the IO bus (4-cycle grid like all IO), and
2. Reads/writes of MFP registers can require **synchronisation to the MFP / E-clock**
   domain, adding wait states — analogous to the PSG but for a different clock.

So a `move.b $fffaXX` (reading timer data, the interrupt registers, the USART, etc.) costs
more than the bare 68000 + RAM-grid figure. Relevant to sync code because MFP timer
reads/acks (Timer A/B/C/D, the `$fffa0f`-area interrupt registers) appear in tight
border/sound code.

### 5.2 Where Hatari does this — **CONFIRM**

**[UNVERIFIED / HATARI-from-memory]**

```
src/mfp.c        -> MFP_ReadByte / MFP_WriteByte handlers (per-register), and any
                    wait-state add for MFP access; look for M68000_WaitState / += <n>
                    and comments about MFP/68901 access timing.
src/ioMem*.c     -> as with PSG, the generic IO wait might be applied at the dispatcher
                    layer for the whole $fffa00-$fffaff range rather than per-handler.
```

I do **not** have a confident extra-cycle integer for MFP accesses either — **read it from
`src/mfp.c`/`ioMem*.c`.** Note that some ST IO regions are byte-only and only on
odd/even addresses; accessing the "wrong" half can have its own cost — check the IO table
(`ioMemTabST*.c`) for how `$fffaxx` half-word access is handled.

---

## 6. Blitter bus stealing (STE / Mega ST)

**[HW + HATARI-from-memory — confirm in `src/blitter.c`]**

The BLiTTER is a **second bus master**, present on **STE and Mega ST** but **NOT on the
plain STF** (Aurora's target — DESIGN.md §1.3.4 / §1.4 note this is a later, machine-
profile-gated phase). When active it contends with the CPU for the bus.

Two operating modes (hardware) you'll see reflected in `src/blitter.c`:

- **Bus-hog / "blit now" mode:** the blitter grabs the bus for the whole blit; the CPU is
  effectively stalled. Cost ≈ the blit's own word/line count, CPU gets nothing meanwhile.
- **Shared / "blit on HOG=0" mode:** the blitter takes the bus in bursts (a fixed number
  of bus cycles), then yields to the CPU for a window, alternating — so CPU code runs
  *slower but not stopped* during a blit.

What to extract from **`src/blitter.c`** **[UNVERIFIED — pointers]**:

- `Blitter_*` functions; look for the **cycle cost per word and per line**, the
  source/destination read+write bus accesses per word, and the **HOG / shared arbitration
  burst sizes** (how many bus cycles the blitter holds vs. yields).
- How the cost is charged to the CPU timeline — whether via `M68000_WaitState`, via the
  `cycInt`/`cycles` machinery, or by advancing the main cycle counter directly.
- Per-machine gating: confirm the blitter is only wired up for `MACHINE_STE` /
  `MACHINE_MEGA_ST` (so your STF default profile correctly has **zero** blitter cost).

This is explicitly a **later phase** in DESIGN.md (machine profile, post-STF). For the STF
default profile it contributes nothing.

---

## 7. Other ST-specific timing quirks for cycle-exact sync code

**[HW + HATARI-from-memory — all to confirm in source]**

1. **Prefetch.** The 68000 prefetches instruction words ahead of execution. In Hatari's
   cycle-exact mode the prefetch reads are real bus accesses on the 4-cycle grid (see
   `src/cpu/cpu_prefetch.h`, `cpuemu_*`), so prefetch participates in the §2 phase. The
   `--compatible`/`--cpu-exact` flags toggle this. Practically: your accumulator must
   count the prefetch words of each instruction as bus accesses, not just operand
   reads/writes — otherwise the phase drifts. **[UNVERIFIED — confirm prefetch is on the
   grid in the CE core.]**

2. **E-clock (6800 peripherals).** The MFP and any 6800-style peripheral access can be
   synchronised to the **E clock** (the 68000's `E`/VPA mechanism for 6800 peripherals),
   which runs at clock/10 and is **not** phase-aligned to the 4-cycle RAM grid. This
   produces *variable* wait states (0–9 extra cycles depending on where the access falls
   in the E period). Look for `M68000_SyncCpuBus` / an E-clock helper / `get_e_cycles`
   style code. This is a candidate explanation for "MFP accesses that don't add up."
   **[UNVERIFIED — confirm whether the ST actually routes MFP through VPA/E in Hatari, or
   treats it as plain IO; this materially changes §5.]**

3. **STE DMA sound bus stealing.** On the **STE**, the DMA sound channel fetches sample
   data from RAM at the replay frequency, stealing bus slots like the shifter — a third
   master (DESIGN.md §1.3.4). Present only on STE; gated by machine profile. Look in
   `src/dmaSnd.c` (a.k.a. `dma_snd`/sound DMA) for how/where it steals. **[UNVERIFIED.]**
   Zero on STF.

4. **IO byte-access width / mirror behaviour.** ST IO registers are frequently byte-wide
   on a specific (odd or even) address; a `.w`/`.l` access to an IO register, or an access
   to the "other" byte, can split into multiple bus cycles or hit a mirror. The IO tables
   `src/ioMemTabST.c` / `ioMemTabSTE.c` encode which addresses are valid and how wide —
   relevant if sync code does word writes to byte IO registers. **[UNVERIFIED.]**

5. **`cycInt` internal-interrupt scheduler.** `src/cycInt.c` schedules internal events
   (HBL, VBL, MFP timers, etc.) in *cycle* time. It does not itself add CPU wait states,
   but it defines **when** the video/HBL/timer events that gate border opening fire,
   relative to the same cycle counter your accumulator tracks. For the scheduler
   (DESIGN.md §7) the HBL/timer-B fire cycles come from here + `video.c`. **[UNVERIFIED.]**

6. **VBL-entry jitter margins (the frame-level budget, DESIGN §9 / `lockstep/budget.py`).**
   The border-opening tolerance is *tight in cycles* and *wakestate-dependent*. Two figures the
   overscan authoring layer relies on, both empirical (calibrated against Hatari across wakestates,
   not from a manual):
   - **top-border eor-dance tolerance ≈ 20c.** The eor-dance top-border removal is timed from
     VBL-entry (before the `$8209` re-lock), so anything that shifts VBL-entry by ~20c lands the
     top-removal pulse off its line and closes the top border. This is the mechanism behind the
     `budget.py` RISK warning.
   - **per-wakestate margin ≈ 0–3c.** The cold-start GLUE phase (Hatari `--video-timing ws1..ws4`)
     shifts the whole frame by a sub-cycle-to-few-cycle amount fixed at power-on; the border
     switches must still hit their GLUE-check cycles. This is why "opened on ws3" says nothing about
     ws2/ws4, and why the standard frame is engineered with a left stabiliser + a cross-boundary
     bottom bust rather than a tighter single lock. The pause-loop cost `16N+28` (N = the sync
     pause count) is exact and static; the `$8209` beam-wait is runtime-bounded (≤ ~one line). The
     frame slack (`frame_cycles − skeleton ≈ 8.6kc` on PAL) is the budget the post-display tail must
     fit inside before the handler overruns into the next VBL and the top border closes.

---

## 8. Summary mapping to DESIGN.md's cost model

| DESIGN.md concept | Hatari location to mine | Status here |
|---|---|---|
| `motorola_68000_cycles` (PRM §8) | `src/cpu/` (WinUAE core, `cpuemu_*`, `newcpu.c`) | pointer only, UNVERIFIED |
| bus-phase accumulator / 4-cycle grid (§1.1) | `src/cycles.c` (`Cycles_GetCounterOnWriteAccess`), `src/m68000.c` (`M68000_WaitState`) | pointer only, UNVERIFIED |
| video shifter contention (§1.3.1) | `src/video.c` (cycle-position table + contention charge) | pointer only, UNVERIFIED |
| race-the-beam constraint (§1.3.2) | `src/video.c` (`Video_GetPosition`, border-remove windows) | pointer only, UNVERIFIED |
| **PSG/YM2149 wait (§1.3.3) — PRIORITY** | **`src/psg.c`** (ff8800/ff8802 handlers, `M68000_WaitState`), `src/ioMem*.c` | **number NOT obtained — read source** |
| MFP wait (§1.3.3) | `src/mfp.c`, `src/ioMem*.c`, possibly E-clock helper | number NOT obtained — read source |
| blitter master (§1.3.4) | `src/blitter.c` (STE/Mega only) | pointer only, UNVERIFIED |
| STE DMA sound master (§1.3.4) | `src/dmaSnd.c` (STE only) | pointer only, UNVERIFIED |

---

## 9. Open / uncertain (could NOT pin down)

Everything in this file is, strictly, "could not verify against source in this run." The
items below are the ones that are *also* uncertain at the knowledge level and that you
**must** resolve from source before the cost model can be trusted:

1. **The single most important number: the exact extra cycles a PSG write to `$ff8800`
   and `$ff8802` costs in Hatari.** I could not read `src/psg.c`. The hardware reason
   (2 MHz sync) is solid; the *constant* is not obtained. **Highest priority — read
   `src/psg.c` IO handlers and the `M68000_WaitState` argument.**
2. **The exact MFP access extra-cycle cost**, and *whether* Hatari routes MFP through an
   E-clock/VPA path (variable 0–9 wait) or treats `$fffaxx` as plain 4-cycle-grid IO.
   This changes whether MFP cost is a constant or a phase-dependent range. Unresolved.
3. **Whether video-display contention is charged per-CPU-access (so the static engine can
   predict it) or only coarsely per line (so it must defer to the Hatari oracle).**
   DESIGN.md §3 assumes the latter; verify against `src/video.c`. Unresolved.
4. **The exact per-line cycle-position constants** (border start/stop, HBL, timer-B,
   border-removal windows) — these define the line template (DESIGN.md §7) and must be
   copied verbatim from `src/video.c`, not guessed. Not obtained.
5. **Whether Hatari's cycle-exact prefetch puts prefetch words on the 4-cycle grid** (it
   should, but the phase model in `cycles.py` depends on it). Unconfirmed.
6. **The blitter HOG/shared arbitration burst sizes and per-word cost** in `src/blitter.c`
   (STE/Mega only; not needed for the STF default profile but needed for the STE profile).
7. **STE DMA sound steal model** in `src/dmaSnd.c` (STE only).
8. **Exact Hatari function/variable/flag names** — every name in this document
   (`M68000_WaitState`, `Cycles_GetCounterOnWriteAccess`, `PSG_ff8800_WriteByte`,
   `--cpu-exact`, etc.) is from memory and may differ in spelling/signature in the
   installed build. Re-grep before relying on any of them.

**Recommended next action:** obtain the source (`git clone --depth 1
https://github.com/hatari/hatari`, or `apt-get source hatari`, or point this toolkit's
research step at a machine with network/source access), then re-run this research with the
grep checklist in §0 to replace every UNVERIFIED tag with a real `file:line` citation and,
above all, the concrete PSG/MFP wait-state numbers in §4 and §5.
```
