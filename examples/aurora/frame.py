"""Capstone — the COMPLETE Aurora display frame, re-created with Lockstep.

This stacks every band of Aurora's full-sync display region as `pack_schedule` segments,
so the whole frame is expressed through the toolkit and every line lands on 512c. Aurora
(`../aurora/aurora.s`) is read-only reference; nothing in it is edited.

Band stack (line counts and work transcribed from Aurora; bot_lines=32):

  band            lines  aurora.s   work
  ----            -----  --------   ----
  scroller         128   :786-942   byte-shift, long/word mix  -> StepWork
  font feed          8   :957-1020  move.l (a3)+/or.l (a4)+/move.l d0,N(a5)
  border-only       59   :1023-1044 none (dcb.w 90/13/12)
  scrolltext        32   :1078-1106 palette feed (movem.l (a2) -> move.l dN,off($8240))
  bottom-border bust 1   :1109-1150 palette feed + the late switch that opens the bottom
  bottom palette    32   :1152-1197 palette feed
                   ---
                   260   (the scheduler-domain display region; 27-line top overscan +
                          beam sync are the vblank preamble, and the per-frame animation /
                          dosound logic is the demo's content, not scheduling)

Cycle-faithful, not byte-faithful: the work keeps Aurora's instruction *costs* (so each
line is 512c) with data operands pointed at scratch RAM. The exact per-gap placement of the
palette writes (a beam-race constraint, DESIGN §5 Q9), the dosound peg (DESIGN §8), and a
pixel-level visual diff (needs a video-on harness) are the remaining capstone milestones.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lockstep import (LineTemplate, Move, Peg, Segment, StepWork,   # noqa: E402
                      WorkStream, pack_schedule)

# Shared "all borders open" template at Aurora's real offsets (left@0, right@376, extra@444).
ALLBORDERS = LineTemplate([
    Peg(0,   "move.b d3,(a1)\nmove.b d4,(a1)",      "left"),
    Peg(376, "move.b d4,(a0)\nmove.b d3,(a0)",      "right"),
    Peg(444, "move.b d3,(a1)\nnop\nmove.b d4,(a1)", "extra"),
])

# The bottom-border-bust line: the same three pegs, then a LATE 60/50 switch at 496 that
# also opens the bottom border (aurora.s:1138-1148). The 32c gap before it carries a
# palette write (movem.l d0-d2,(a6)).
BOTTOMBUST = LineTemplate([
    Peg(0,   "move.b d3,(a1)\nmove.b d4,(a1)",      "left"),
    Peg(376, "move.b d4,(a0)\nmove.b d3,(a0)",      "right"),
    Peg(444, "move.b d3,(a1)\nnop\nmove.b d4,(a1)", "extra"),
    Peg(496, "move.b d4,(a0)\nmove.b d3,(a0)",      "bottom-open"),
])

# --- work, transcribed from Aurora with data operands aimed at scratch (cost-identical) ---

# scroller byte-shift: long (4 bytes / 32c) + word (2 bytes / 24c) — the move.l/move.w trick
SCROLLER = StepWork(steps=44, menu=[
    Move("move.l 8(a6),(a6)+\naddq #4,a6", steps=4, label="long"),
    Move("move.w 8(a6),(a6)+\naddq #4,a6", steps=2, label="word"),
])

# font feed (aurora.s:965-1005): 8 copies of move.l/or.l/move.l, then advance — ~348c, fits gap0
FONT_LINE = (
    "move.l (a3)+,d0\nor.l (a4)+,d0\nmove.l d0,(a5)\n"          # 40c (1st, no displacement)
    + "".join(f"move.l (a3)+,d0\nor.l (a4)+,d0\nmove.l d0,{k}*230(a5)\n"
              for k in range(1, 8))                             # 7 x 44c
    + "lea 8*230(a5),a5"                                        # advance
)

# palette feed (aurora.s:1085-1105): load a palette block, splat it to $ffff8240 — ~200c
PALETTE_LINE = (
    "move.l (a5)+,a2\n"                 # 12c  (a5 walks a table of valid scratch pointers)
    "move.w #$8240,a6\n"               # 8c   (#$8240 sign-extends to $ffff8240, palette base)
    "movem.l (a2),d0-d2/d5-d7/a3-a4\n"  # 76c
    "move.l d7,20(a6)\n"               # 16c
    "move.l a3,24(a6)\n"               # 16c
    "move.l a4,28(a6)\n"               # 16c
    "movem.l d0-d2/d5-d6,(a6)"          # 48c
)

# bottom-bust line work: a palette load, split so 32c lands in the gap before the late switch
BUST_LINE = (
    "move.l (a5)+,a2\n"
    "move.w #$8240,a6\n"
    "movem.l (a2),d0-d2/d5-d7/a3-a4\n"  # 76c
    "move.l d7,20(a6)\n"
    "move.l a3,24(a6)\n"
    "move.l a4,28(a6)\n"               # gaps 0/1
    "movem.l d0-d2,(a6)"                # 32c  -> the gap before the bottom-open switch
)


def frame_segments():
    """Aurora's full display region as a list of Lockstep bands (top→bottom)."""
    return [
        Segment(ALLBORDERS, SCROLLER, 128),                            # scroller byte-shift
        Segment(ALLBORDERS, WorkStream.repeat(FONT_LINE, 8), 8),       # font feed
        Segment(ALLBORDERS, WorkStream([]), 59),                       # border-only middle
        Segment(ALLBORDERS, WorkStream.repeat(PALETTE_LINE, 32), 32),  # scrolltext palette
        Segment(BOTTOMBUST, WorkStream.repeat(BUST_LINE, 1), 1),       # bottom-border bust
        Segment(ALLBORDERS, WorkStream.repeat(PALETTE_LINE, 32), 32),  # bottom palette
    ]


def aurora_frame():
    """The full display-region frame as a Lockstep band stack (returns a PackResult)."""
    return pack_schedule(frame_segments())


# scratch harness: fill a region with self-pointers so every data deref stays valid, then
# aim the border writes at scratch (cycle-identical to the real border regs).
FRAME_SETUP = """\
    lea     $90000,a0
    move.w  #$1fff,d0
.fillscratch:
    move.l  #$90000,(a0)+
    dbra    d0,.fillscratch
    move.l  #$90000,a2
    move.l  #$90000,a3
    move.l  #$90000,a4
    move.l  #$90000,a5
    move.l  #$90000,a6
    move.l  #$f0000,a0
    move.l  #$f0000,a1
    moveq   #2,d3
    moveq   #0,d4
"""


if __name__ == "__main__":
    from st68k.annotate import block_cycles

    res = aurora_frame()
    lo, hi = block_cycles(res.asm)
    print(f"Aurora display frame re-created: {res.n_lines} lines, {lo}c "
          f"(== {res.n_lines} x 512 = {res.n_lines * 512}).")
    assert lo == hi == res.n_lines * 512, "every line must be 512c"
    print(f"work units placed: {res.units_placed}, nop filler: {res.nop_cycles}c")
    print("band line counts:", res.placed_per_line[:1], "...,",
          f"{res.n_lines} total")
    print("\nstatic check OK. Run frame_verify (below) for the Hatari per-band proof.")
