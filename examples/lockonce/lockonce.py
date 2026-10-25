"""Lock-once example: the bordopen frame (all four borders, green screen) as a lock-once loop.

Synced once at the first VBL, then no interrupts at all: every frame is one loop iteration of
exactly 160256 cycles (`lockstep.lockonce.LockOnceFrame`). The tail cycles colour 15 through a
ramp, so a running loop is visible, and bumps a frame counter at $1000 for headless captures.
Any key ends it.

    python3 examples/lockonce/lockonce.py      # -> examples/lockonce/lockonce.tos

LOCKONCE_D2B=<cycles> overrides the dance placement (probe the tolerance window with it).
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "bordopen"))

from bordopen import _setup  # noqa: E402  (the green screen, palette, video base)
from lockstep.lockonce import DANCE_TO_BAND0, LockOnceFrame  # noqa: E402

COUNTER = 0x1000

# a green ramp up and down, 32 steps, STF-safe ($0RGB, 3 bits per channel). Never black: black is
# the border colour, and the border certifier tells open from closed by it.
RAMP = [(3 + (v if v < 5 else 9 - v)) << 4 for v in range(10)]
RAMP = (RAMP * 4)[:32]


def tail() -> str:
    """Constant cost: counter, then palette entry 15 = RAMP[counter & 31]."""
    return f"""\
    addq.l  #1,${COUNTER:x}.w           ; frame counter (capture trigger)
    move.w  ${COUNTER + 2:x}.w,d0
    and.w   #31,d0
    add.w   d0,d0
    lea     lo_ramp,a0
    move.w  (a0,d0.w),$ffff825e         ; colour 15: the screen
"""


def extra() -> str:
    return "    even\nlo_ramp:\n    dc.w    " + ",".join(f"${c:03x}" for c in RAMP) + "\n"


def build(out_path: str, *, dance_to_band0: int = DANCE_TO_BAND0) -> str:
    frame = LockOnceFrame(main_lines=227, bot_lines=32, left_nops=1, cross=True,
                          dance_to_band0=dance_to_band0)
    print(f"tail budget: {frame.tail_budget()} cycles per frame")
    return frame.build(out_path, setup=f"    clr.l   ${COUNTER:x}.w\n" + _setup(),
                       tail=tail(), extra=extra())


if __name__ == "__main__":
    d2b = int(os.environ.get("LOCKONCE_D2B", str(DANCE_TO_BAND0)))
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "lockonce.tos")
    print("built", build(out, dance_to_band0=d2b))
