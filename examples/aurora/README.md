# Capstone — re-creating Aurora with Lockstep

The acceptance test for Lockstep (DESIGN §6) is to reproduce Aurora's hand-tuned, all-borders-open,
full-sync VBL through the toolkit. **Aurora itself (`../../../aurora/aurora.s`) is never edited** —
this directory rebuilds its structure from Lockstep primitives.

## What's here

| file | what it does |
|---|---|
| `screen.py` | the all-borders template + a small screen (border-only, and a scroller demo) |
| `allbord.s` | the same border-only screen as a `;@`-directive spec (tutorial twin) |
| `frame.py` | **the full capstone** — Aurora's entire 260-line display frame as a band stack |
| `sound.py` | profile a PSG replay's worst-case per-tick cost; reserve it as a sound peg |
| `visual.py` | **see it**: run the generated frame video-on and prove the borders open |

Run:

```
python examples/aurora/screen.py                              # build + print, asserts the fillers
python -m lockstep schedule examples/aurora/allbord.s  # emit the asm
python -m lockstep verify   examples/aurora/allbord.s  # confirm 512c/line in Hatari
```

## The key result

With the border switches pegged at Aurora's real offsets (left @ 0, right @ 376, extra @ 444) and
**no work between them**, Lockstep sizes the gaps to **`dcb.w 90 / 13 / 12`** — *exactly* the nop
counts hand-tuned in `aurora.s:218-238`. Every line is 512c, verified on cycle-exact Hatari, beam
constant per line (borders hold). The toolkit regenerates the hand-written full-sync screen.

## How Aurora's VBL maps to Lockstep bands

Aurora's display is a stack of vertical bands that **all share one border template** and differ only
in the *work* poured into the gaps — exactly `pack_schedule` over `Segment(template, work, n_lines)`.

All bands below are reconstructed in `frame.py` and **Hatari-verified at 512c/line** (the whole
260-line frame measures `260 x 512`, 0 off-budget lines, beam constant per line):

| Aurora region | lines | work per line | Lockstep | status |
|---|---|---|---|---|
| `my_70` entry + beam sync `:248,177-205` | — | establish cycle 0 | preamble (vblank, not packed) | n/a |
| scroller byte-shift `:786-942` | 128 | `move.l/move.w 8(a6),(a6)+` mix | `StepWork` band | ✅ verified |
| font feed `:957-1020` | 8 | `move.l (a3)+ / or.l (a4)+ / move.l d0,N*230(a5)` | `WorkStream` band | ✅ verified |
| border-only middle `:1023-1044` | 59 | none (`dcb.w 90/13/12`) | empty `WorkStream` band | ✅ verified |
| scrolltext palette `:1078-1106` | 32 | `movem.l (a2) / move.l dN,offs($8240)` | `WorkStream` band | ✅ verified |
| bottom-border bust `:1109-1150` | 1 | palette load + late switch that opens the bottom | `BOTTOMBUST` template (4th peg @496) | ✅ verified |
| bottom palette-feed `:1152-1197` | 32 | palette feed | `WorkStream` band | ✅ verified |
| dosound / PSG replay `:1228+` | — | variable-cost `play`, PSG +4c/reg | `profile_play` (worst case) + `Peg(reserve=W)` (DESIGN §8) | ✅ profiled + reserved |

## Reproduced vs. deferred

**Reproduced & Hatari-verified (cycles):** the all-borders template at the real offsets; the
border-only screen (== Aurora's debug loop, exact `dcb.w 90/13/12`); and **the complete
260-line display frame** — every Aurora band, including the bottom-border-bust line — packed
through `pack_schedule`, every line 512c on cycle-exact silicon.

It is **cycle-faithful, not byte-faithful**: the work keeps Aurora's instruction *costs* with
data operands aimed at scratch RAM.

**Sound (`sound.py`):** ✅ `lockstep.sound.profile_play` measures the PSG replay's worst-case
per-tick cost in Hatari (the +4c-per-PSG-access number that never added up by hand), and a
`Peg(reserve=W)` reserves that budget as a mid-frame sound slot (DESIGN §8). The replay's
runtime constancy (worst-case-padded player or a beam-wait) is the player's responsibility, and
a worst case larger than a line's free space must split into N ticks or use the post-display slack.

**Visual (`visual.py`):** ✅ the generated all-borders frame, run with video on + the real
beam-sync (transcribed read-only from Aurora) + the real shifter/sync registers, **removes all
four borders** in cycle-exact Hatari: the white display goes from 640×400 (a normal centred
display, 56% of the overscan canvas) to **832×552 — the full canvas, 100%** (+192px wide from the
left+right borders, +152px tall from top+bottom). `lockstep.visual.capture` grabs the frame
headless via Hatari's `screenshot`; a test asserts the coverage. Seeing-is-believing, not just cycles.

**Beam-race placement** ✅ (DESIGN §1.3.2): `WorkBlock(..., beam=(lo,hi))` / `;@work beam=lo:hi`
pins a screen/palette write to the cycle window where the shifter isn't fetching it — the packer
places it there (padding up to `lo`, enforcing `hi`) and errors if it can't, so colour K lands on
scanline K instead of relying on greedy luck. (The exact window *values* are beam-calibrated data,
like the border offsets.)

The cycle-exact full-sync backbone — the scheduler's job — is **done, verified, and visible**:
borders open on the real hardware model, every line 512c, sound budget profiled and reservable,
beam-sensitive writes placeable in their safe window.
