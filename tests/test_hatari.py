"""The Hatari oracle: the tests that end in a measurement on cycle-exact silicon rather than in an
assertion about our own cost model. Skipped (visibly) when hatari/TOS are absent — see conftest.py.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from st68k.hatari import measure   # noqa: E402

# Every test in this file drives a real emulator; conftest skips them all when the
# oracle is absent (visibly — as `skipped`, never as a silent pass).
pytestmark = pytest.mark.hatari



def test_moveq_chain_is_16():
    m = measure("moveq #0,d0\nmoveq #1,d1\nmoveq #2,d2\nmoveq #3,d3")
    assert m.cycles == 16, f"4x moveq should be 16c, got {m.cycles}"


def test_exg_is_six_not_eight():
    # the bus-phase result: a single exg is genuinely 6c, NOT round-to-4's 8c.
    m = measure("exg d0,d1")
    assert m.cycles == 6, f"exg should be 6c (not round-4's 8), got {m.cycles}"


def test_beam_position_is_reported():
    m = measure("nop")
    assert m.start.hbl >= 0 and m.start.linecycles >= 0


def test_balance_paths_equal():
    # @balance must make both branch directions cost the same (deterministic VBL).
    from st68k.preprocess import expand
    src = (";@balance\n    bge.s .alt\n;@fill\n    bra.s .end\n;@balance alt\n.alt:\n"
           "    add.l d1,d2\n    add.l d1,d2\n;@balance end\n.end:\n    nop\n    nop\n    nop\n")
    out, _ = expand(src)
    taken = measure(out, setup="moveq #0,d2")        # d2>=0 -> branch taken
    nottaken = measure(out, setup="moveq #-1,d2")    # d2<0  -> fall-through
    assert taken.cycles == nottaken.cycles, \
        f"balance failed: taken {taken.cycles}c vs not-taken {nottaken.cycles}c"


def test_branch_costs_match_hatari():
    """The branch table, against the oracle. These five numbers are load-bearing: `@balance` sizes
    every arm's filler from them, and being 4c out is enough to walk Aurora's 60/50 Hz top-border
    pulse off its scanline — which shuts the top AND bottom borders while leaving left/right open
    (they are driven by absolute writes, not by the pulse). That is exactly the bug this pins.

    Note the asymmetry is a full 4c, not the 2c the 68000 manual implies: a taken branch refills the
    prefetch queue and the refill realigns the CPU to the ST's 4-cycle bus, so raw 10c/18c land as
    12c/20c and the remainder never comes back."""
    n2 = measure("    nop\n    nop\n").cycles                                  # 8c reference

    def c(code):
        return measure(code).cycles

    bra = c("    nop\n    bra.s bx\n    nop\nbx:\n    nop\n") - n2
    taken = c("    moveq #1,d0\n    tst.w d0\n    bge.s cx\n    nop\n    nop\ncx:\n") - 8
    nottaken = c("    moveq #-1,d0\n    tst.w d0\n    bge.s cx\n    nop\n    nop\ncx:\n") - 8 - 8
    takenw = c("    moveq #1,d0\n    tst.w d0\n    bge.w cw\n    nop\n    nop\ncw:\n") - 8
    dbra4 = c("    moveq #3,d0\ndl: dbra d0,dl\n") - 4        # 3 loops + 1 expiry

    assert bra == 12, f"bra.s = {bra}c (table says 12)"
    assert taken == 12, f"Bcc.s taken = {taken}c (table says 12)"
    assert nottaken == 8, f"Bcc.s not-taken = {nottaken}c (table says 8)"
    assert takenw == 12, f"Bcc.w taken = {takenw}c (table says 12)"
    assert dbra4 == 3 * 12 + 16, f"dbra x4 = {dbra4}c (table says 3*12 + 16)"


def test_lockstep_packed_line_is_512_on_silicon():
    # the P5 payoff: pack a border line + scroller work and confirm EVERY scanline is
    # exactly 512c in cycle-exact Hatari, interrupts masked (full-sync), not just statically.
    from lockstep import LineTemplate, Peg, WorkStream
    from lockstep.verify import verify
    tmpl = LineTemplate([
        Peg(0,   "move.b d3,(a1)\nmove.b d4,(a1)", "left"),
        Peg(376, "move.b d4,(a0)\nmove.b d3,(a0)", "right"),
        Peg(444, "move.b d3,(a1)\nnop\nmove.b d4,(a1)", "extra"),
    ])
    vr = verify(tmpl, WorkStream.repeat("move.l 8(a6),(a6)+\naddq #4,a6", n=39), n_lines=3)
    assert vr.per_line_cycles == [512, 512, 512], vr.report()
    assert vr.ok


def test_lockstep_multi_variant_screen_on_silicon():
    # a multi-band screen (top-border / mid-scroller / bottom-border) must hold 512c on
    # EVERY line, regardless of which template the band uses (DESIGN §7.1).
    from lockstep import LineTemplate, Peg, Segment, WorkStream
    from lockstep.verify import verify_segments
    mid = LineTemplate([
        Peg(0,   "move.b d3,(a1)\nmove.b d4,(a1)", "left"),
        Peg(376, "move.b d4,(a0)\nmove.b d3,(a0)", "right"),
        Peg(444, "move.b d3,(a1)\nnop\nmove.b d4,(a1)", "extra"),
    ])
    top = LineTemplate([
        Peg(0,   "move.b d3,(a1)\nmove.b d4,(a1)", "left"),
        Peg(380, "move.b d4,(a0)\nmove.b d3,(a0)", "vert-open"),
    ])
    scroll = WorkStream.repeat("move.l 8(a6),(a6)+\naddq #4,a6", n=13)
    vr = verify_segments([
        Segment(top, WorkStream([]), 1),
        Segment(mid, scroll, 2),
        Segment(top, WorkStream([]), 1),
    ])
    assert vr.per_line_cycles == [512, 512, 512, 512], vr.report()
    assert vr.ok


def test_sound_profiler_per_tick_envelope():
    # DESIGN §8: a data-driven PSG replay has variable per-tick cost; the profiler measures
    # the envelope so the worst case can be reserved. (PSG writes carry the +4c wait state.)
    from examples.aurora.sound import PLAY, SETUP, make_tune
    from lockstep.sound import profile_play
    const = profile_play(PLAY, ticks=4, setup=SETUP, data=make_tune([2, 2, 2, 2]))
    assert len(set(const.per_tick)) == 1, const.per_tick      # constant tune -> equal ticks
    vary = profile_play(PLAY, ticks=3, setup=SETUP, data=make_tune([0, 6, 0]))
    assert vary.max > vary.min                                # a loud tick costs more
    assert vary.reserve % 4 == 0 and vary.reserve >= vary.max


def test_overscan_frame_opens_borders_visually():
    """The capstone's visual proof: an `OverscanFrame` really removes all four borders — the
    display fills nearly the whole overscan canvas, vs the ~56% a normal centred frame covers.

    This MUST go through the real program path (`OverscanFrame.build` -> a `.TOS` whose frame runs
    inside the `$70` VBL handler with the MFP masked). An earlier version of this test ran the same
    bands through `visual.capture`, which loops the body in the *main* program with interrupts still
    live: the left/right borders open there, but the top/bottom ones do not (the frame has to be
    entered from the VBL to be in step with the beam), so it measured 46% and failed. The bands were
    never the problem; the execution model was.
    """
    import tempfile

    import numpy as np
    from PIL import Image

    from lockstep.skeleton import OverscanFrame
    from lockstep.visual import shoot_tos

    work = tempfile.mkdtemp()
    # palette[0] = black (that IS the border colour) and the screen filled white, so an open border
    # shows up as white spilling into the overscan. `emit_program` has already put the aligned
    # screen base in a3 and pointed the video base at it, so fill that.
    setup = """\
    move.w  #$0000,$ffff8240    ; palette[0] = black  (the border colour)
    move.w  #$0777,$ffff825e    ; palette[15] = white (the display fill)
    move.l  a3,a2               ; a3 = the live, aligned screen base
    move.w  #$3fff,d0
.fill:
    move.l  #$ffffffff,(a2)+    ; 64KB white — all four planes set
    dbra    d0,.fill
    lea     $ffff8260,a1        ; the border-switch registers the bands expect
    moveq   #2,d3
    moveq   #0,d4
"""
    tos = OverscanFrame().build(os.path.join(work, "OPEN.TOS"), setup=setup)
    png = os.path.join(work, "open.png")
    shoot_tos(tos, png, video_timing="ws3")
    a = np.asarray(Image.open(png).convert("RGB")).astype(np.int16)
    coverage = float((a.min(axis=2) > 180).mean())
    assert coverage > 0.9, f"borders did not open: display coverage only {coverage:.0%}"
