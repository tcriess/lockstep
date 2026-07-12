"""Capstone — re-create Aurora's full-sync all-borders screen with Lockstep.

Aurora itself (`../aurora/aurora.s`) is NOT touched; this rebuilds its VBL structure from
the Lockstep primitives so the toolkit's acceptance test ("reproduce the hand-tuned VBL")
runs through the real pipeline. It doubles as the headline tutorial example.

Aurora's display is a stack of vertical bands that all share ONE border template —
    left flip @ 0   (move.b d3/d4,(a1))         aurora.s:220-221 / 960-962
    right flip @ 376 (move.b d4/d3,(a0))        aurora.s:225-227 / 1008-1010
    extra left @ 444 (move.b d3 / nop / d4,(a1)) aurora.s:231-234 / 1014-1017
— and differ only in the WORK poured into the gaps:
    border-only (the DEBUG loop)   aurora.s:218-238  -> empty WorkStream  (dcb.w 90/13/12)
    scroller byte-shift            aurora.s:786-942  -> StepWork (move.l/move.w mix)
    font feed / scrolltext / palette-feed / bottom-border bust  -> later slices.

This module builds the first two as `pack_schedule` bands and prints the unrolled, exactly
512c-per-line routine. `lockstep verify` (or verify.py) confirms every line on real silicon.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lockstep import (LineTemplate, Move, Peg, Segment, StepWork,   # noqa: E402
                      WorkStream, pack_schedule)

# The "all borders open" line template, at Aurora's real cycle offsets (aurora.s:218-238).
# Border/shifter writes carry no wait state (TIMING.md), so the costs are 8c each.
ALLBORDERS = LineTemplate([
    Peg(0,   "move.b d3,(a1)\nmove.b d4,(a1)",        "left  (mono/lo-res)"),
    Peg(376, "move.b d4,(a0)\nmove.b d3,(a0)",        "right (60/50 Hz)"),
    Peg(444, "move.b d3,(a1)\nnop\nmove.b d4,(a1)",   "extra (left flip)"),
])

# Aurora's scroller feed shifts a fixed byte span per line using a mix of long and word
# moves (aurora.s:850, the "12.5 column" trick). As a StepWork the solver picks the mix.
SCROLLER_MENU = [
    Move("move.l 8(a6),(a6)+\naddq #4,a6", steps=4, label="long"),   # 4 bytes / 32c
    Move("move.w 8(a6),(a6)+\naddq #4,a6", steps=2, label="word"),   # 2 bytes / 24c
]


def allborders_screen(n_lines: int = 227):
    """The DEBUG-loop screen: `n_lines` identical border-only lines (aurora.s:218-238).
    With Aurora's offsets and empty work, the gaps fill to dcb.w 90 / 13 / 12 — Aurora's
    own hand counts, derived."""
    return pack_schedule([Segment(ALLBORDERS, WorkStream([]), n_lines)])


def scroller_screen(top: int = 1, display: int = 4, bottom: int = 1, steps: int = 40):
    """A multi-band screen: border-only top/bottom bands wrapping a scroller display band
    (StepWork). Mirrors Aurora's band stack (border region / scroller / border region)."""
    return pack_schedule([
        Segment(ALLBORDERS, WorkStream([]), top),                       # top border lines
        Segment(ALLBORDERS, StepWork(steps=steps, menu=SCROLLER_MENU), display),
        Segment(ALLBORDERS, WorkStream([]), bottom),                    # bottom border lines
    ])


def _first_scanline(asm: str) -> str:
    lines = asm.splitlines()
    end = next((i for i, l in enumerate(lines) if "scanline 1" in l), len(lines))
    return "\n".join(lines[:end])


if __name__ == "__main__":
    from st68k.annotate import block_cycles

    print("=" * 70)
    print("Aurora all-borders screen (border-only) — reproduces aurora.s:218-238")
    print("=" * 70)
    res = allborders_screen(227)
    asm = res.asm
    # the emitted nop-filler must match Aurora's hand counts exactly
    assert "dcb.w 90,$4e71" in asm, "left->right gap should be 90 nops (360c)"
    assert "dcb.w 13,$4e71" in asm, "right->extra gap should be 13 nops (52c)"
    assert "dcb.w 12,$4e71" in asm, "extra->end gap should be 12 nops (48c)"
    lo, hi = block_cycles(asm)
    assert lo == hi == 227 * 512
    print(f"227 lines, {lo}c total (== 227 x 512). Fillers: dcb.w 90 / 13 / 12 "
          f"— identical to Aurora's hand-tuned debug loop.\n")
    print("first scanline:")
    print(_first_scanline(asm))

    print("\n" + "=" * 70)
    print("Multi-band scroller screen (top border / scroller / bottom border)")
    print("=" * 70)
    s = scroller_screen(top=1, display=4, bottom=1, steps=40)
    lo, hi = block_cycles(s.asm)
    print(f"{s.n_lines} lines, {lo}c total (== {s.n_lines} x 512), "
          f"placed/line={s.placed_per_line}, nop waste={s.nop_cycles}c")
    print("\nrun `lockstep verify` on either spec to confirm 512c/line on real silicon.")
