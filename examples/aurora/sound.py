"""Capstone (sound) — profile a PSG replay's worst-case per-tick cost with Lockstep.

Aurora's `dosound` (aurora.s:1214) runs a data-driven PSG replay: each tick writes a
variable number of registers (a few when a note changes, none on a held tick). In full-sync
that variable cost is exactly what "never added up" by hand, because every PSG access is
nominal + 4c. `lockstep.sound.profile_play` runs the replay across the tune in cycle-exact
Hatari and reports the per-tick envelope — so you know the worst case to reserve (DESIGN §8)
or to fit into the post-display slack (the way Aurora does it).

This uses a minimal, position-independent stand-in for `dosound`'s inner loop (a1 walks a
command stream: a count byte, then that many register/value pairs). The profiling mechanism
is identical for the real dosound or any SNDH `play`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lockstep.sound import profile_play   # noqa: E402

# the replay's inner loop: a1 -> [count, (reg,val) x count, ...]; write `count` PSG regs.
PLAY = """\
    moveq   #0,d0
    move.b  (a1)+,d0           ; count of register writes this tick
    subq.b  #1,d0
    bmi.s   .done              ; count == 0 -> silent tick
.loop:
    move.b  (a1)+,$ffff8800    ; select PSG register   (nominal + 4c, TIMING.md)
    move.b  (a1)+,$ffff8802    ; write value            (nominal + 4c)
    dbra    d0,.loop
.done:
"""

SETUP = "    lea     __snddata(pc),a1"


def sound_frame(reserve):
    """A display line with the borders + a reserved sound slot at cycle 400 (DESIGN §8).
    The packer reserves `reserve` cycles for the worst-case replay; no work goes in it."""
    from lockstep import LineTemplate, Peg, WorkStream, pack
    tmpl = LineTemplate([
        Peg(0,   "move.b d3,(a1)\nmove.b d4,(a1)", "left"),
        Peg(376, "move.b d4,(a0)\nmove.b d3,(a0)", "right"),
        Peg(400, "jsr (a2)", "play", reserve=reserve),     # a2 -> the relocated player
    ])
    return pack(tmpl, WorkStream([]), n_lines=1)


def make_tune(counts):
    """Emit a dc.b command stream: per tick a count, then that many (reg,val) pairs."""
    lines = []
    for t, c in enumerate(counts):
        pairs = "".join(f",{r & 13},${(r * 37) & 0xff:02x}" for r in range(c))
        lines.append(f"    dc.b {c}{pairs}")
    return "\n".join(lines)


if __name__ == "__main__":
    from st68k.hatari import HatariError

    # a "tune": most ticks silent or quiet, a few loud (worst case = the 9-register tick)
    counts = [0, 1, 0, 3, 0, 2, 0, 5, 1, 0, 4, 0, 2, 9, 0, 1, 0, 3, 6, 0]
    try:
        env = profile_play(PLAY, ticks=len(counts), setup=SETUP, data=make_tune(counts))
    except HatariError as e:
        print("HATARI unavailable:", e)
        sys.exit(0)

    print(env.report())
    print()
    silent = env.per_tick[0]                       # count 0
    loudest = env.max                              # count 9
    print(f"silent tick (0 regs): {silent}c    loudest tick (9 regs): {loudest}c")
    print(f"each register pair (select+write, both PSG) costs about "
          f"{(loudest - silent) // 9}c — the +4c PSG wait states are in there.")
    print(f"\n=> a frame must reserve {env.reserve}c for this replay's worst case "
          f"(or leave that much post-display slack).")

    # reserve it as a mid-frame peg — but only if the worst case fits a line's free space.
    from st68k.annotate import block_cycles
    free = 512 - (16 + 16)                 # a line minus the left+right border switches
    print(f"\nmid-frame sound peg (DESIGN §8 model A):")
    if env.reserve <= free:
        res = sound_frame(env.reserve)
        print(f"  reserved {env.reserve}c slot; line totals {block_cycles(res.asm)[0]}c (512).")
    else:
        print(f"  worst case {env.reserve}c > one line's free space (~{free}c), so a single")
        print(f"  50 Hz mid-frame peg won't hold it — split into N smaller ticks (100/150/200")
        print(f"  Hz = N pegs) or run it in the post-display slack (Aurora's way). Demo with a")
        demo = 96
        res = sound_frame(demo)
        print(f"  fitting {demo}c reserve instead: line totals {block_cycles(res.asm)[0]}c (512).")
