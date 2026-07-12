"""Tests for lockstep.skeleton (the OverscanFrame primitive).

Fast structural tests (no emulator) pin the frame shape: the sync prelude sets the border-switch
registers and marks __lock/__band0; the packed bands are every-line-512c; the OverscanFrame API
and the free robust_sync/robust_bands functions agree. A hatari-marked acceptance test builds an
empty OverscanFrame straight from the toolkit (a minimal green setup, no example code) and proves
it opens all four borders on all four wakestates via the W2 verifier — the W1 acceptance.
"""

import os
import shutil
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lockstep.skeleton import (LINE_LEN, OverscanFrame, SyncConfig,     # noqa: E402
                               robust_bands, robust_sync)
from lockstep.verify import _expected_per_line                          # noqa: E402


# A minimal green screen so an open border is visible — enough to prove the PRIMITIVE (not the
# bordopen example) opens borders. palette[0]=black border, palette[15]=green, fill + video base.
_GREEN = 0xA8000
GREEN_SETUP = f"""\
    move.w  #$0000,$ffff8240
    move.w  #$0070,$ffff825e
    move.l  #${_GREEN:x},a2
    move.w  #$3fff,d0
.gf:
    move.l  #$ffffffff,(a2)+
    dbra    d0,.gf
    move.b  #${(_GREEN >> 16) & 0xff:02x},$ffff8201
    move.b  #${(_GREEN >> 8) & 0xff:02x},$ffff8203
    lea     $ffff8260,a1
    moveq   #2,d3
    moveq   #0,d4
"""


def test_sync_prelude_sets_switch_registers():
    a = robust_sync()
    assert "__lock:" in a and "__band0:" in a
    assert "$8209" in a          # the MMU video-counter lock
    assert "#$820a,a0" in a       # a0 = right-border sync-mode reg
    assert "$ffff8260,a1" in a    # a1 = left-border resolution reg


def test_overscan_frame_reproduces_robust_bands():
    # the OverscanFrame band stack == the free robust_bands() helper, byte-for-byte
    assert OverscanFrame().bands().asm == robust_bands().asm
    # and the frame body is prelude + bands
    body = OverscanFrame().frame_body()
    assert body == robust_sync() + "\n" + robust_bands().asm


def test_empty_frame_is_512c_every_line():
    res = OverscanFrame().bands()
    # main_lines(227) + cross-bust line(1) + bot_lines(32) = 260 (Aurora's frame height)
    assert res.n_lines == 227 + 1 + 32
    budgets = _expected_per_line(res.asm)
    assert budgets == [LINE_LEN] * res.n_lines         # every scanline exactly 512c


def test_frame_variants():
    # bust=False -> one template across all lines (top+left+right only)
    top3 = OverscanFrame(bust=False, main_lines=10, bot_lines=5).bands()
    assert top3.n_lines == 15
    # within-line bust (cross=False) differs from the cross-boundary bust (cross=True)
    within = OverscanFrame(cross=False, main_lines=10, bot_lines=5).bands().asm
    cross = OverscanFrame(cross=True, main_lines=10, bot_lines=5).bands().asm
    assert within != cross
    assert all(b == LINE_LEN for b in _expected_per_line(cross))


def test_tail_is_appended_after_bands():
    body = OverscanFrame().frame_body(tail="\n    addq.l #1,$1000")
    assert body.endswith("\n    addq.l #1,$1000")


def test_hbl_sync_needs_handler_flag():
    assert not SyncConfig().needs_hbl_handler
    assert SyncConfig(coarse="hbl").needs_hbl_handler


# ---------------------------------------------------------------- regression locks on the sync
# The all-wakestate acceptance test for this exact binary lives in test_wakestate.py
# (`test_robust_build_opens_all_borders_all_wakestates`). It used to be duplicated here, costing a
# second run of 4 wakestates x 2 frames = 8 emulator launches (~1 min) to assert the same fact about
# the same bytes. One canonical pixel proof is enough. What belongs here instead are the *static*
# guards on the three things that make that binary work — none of which had any test at all, which is
# how examples/aurora/visual.py was able to drift away from the shipped sync and sit broken.

def test_sync_does_not_reassert_the_baseline():
    """`baseline` must stay off. Re-asserting 50 Hz / lo-res at handler entry shifts the pre-sync
    timing by ~28c and lands the top-border switch metastably => the top border flickers on every
    other frame. Aurora's own `my_70` does not do it; the bands self-establish 50 Hz / lo-res.

    This is a real regression: a hand-copied sync carrying `baseline` (plus a short `first_line`) is
    exactly what left the aurora example unable to open its borders.
    """
    assert SyncConfig().baseline is False
    prelude = SyncConfig().asm().split(".pause")[0]
    assert "$ffff820a" not in prelude, "no 50 Hz re-assert before the pause"
    assert "$ffff8260" not in prelude, "no lo-res re-assert before the pause"


def test_robust_frame_has_the_three_ingredients():
    """All four borders on all four wakestates needs exactly three things (skeleton.py:13-20).
    Assert each one is actually in the emitted asm, so none can quietly go missing."""
    f = OverscanFrame()
    asm = f.bands().asm

    # 1. the left stabiliser: the left blip widened 8c -> 12c by one extra nop
    assert f.left_nops == 1
    # 2. the cross-boundary bottom bust: 60 Hz SET late on the bust line, RESTORED early on the next
    assert f.cross is True
    assert ";@pad 500" in f.bands().intermediate, "60 Hz set at cycle 500 of the bust line"
    assert ";@pad 20" in f.bands().intermediate, "50 Hz restored at cycle 20 of the next line"
    # 3. the bust lands on the bottom-border scanline (a sharp resonance — 227 works, neighbours do not)
    assert f.main_lines == 227
    assert f.bands().n_lines == 227 + 1 + 32
    assert asm.count("; --- scanline") == 260


def test_program_owns_the_machine():
    """A full-sync frame cannot afford one uninvited cycle. `emit_program` must mask ALL MFP
    interrupts at source — Timer C's 200 Hz tick AND the keyboard/mouse ACIA, which is level 6 and
    preempts the level-4 VBL — and install the frame as the $70 VBL handler.

    Left on, the ACIA turns "someone moved the mouse" into "the borders closed". Nothing tested this.
    """
    from lockstep.program import emit_program
    src = emit_program(OverscanFrame().frame_body(), setup="")
    assert "clr.b   $fffffa13" in src, "MFP channel-A interrupts must be masked"
    assert "clr.b   $fffffa15" in src, "MFP channel-B (Timer C + keyboard/mouse ACIA) must be masked"
    assert "#__vbl,$70.w" in src, "the frame must run as the $70 VBL handler"


# ------------------------------------------------------------- pre-raster work (the VBL pause)
# The VBL-entry pause is 17,052 cycles of dead time — more than twice the whole post-display tail.
# `pre` pours work into it. It must be padded back to EXACTLY the pause budget: the 60/50 Hz toggle
# straight after it is the top-border bust, and its scanline is fixed purely by how many cycles come
# first. Four cycles out and the top border stays shut. (This is where Aurora draws its sprites.)

def test_pause_budget_matches_the_loop_it_replaces():
    assert SyncConfig().pause_budget == 16 * 1064 + 28 == 17052


def test_empty_pre_leaves_the_prelude_untouched():
    # no `pre` => the original nop/dbra loop, byte for byte. Existing binaries must not move.
    assert OverscanFrame().frame_body() == robust_sync() + "\n" + robust_bands().asm
    assert ".pause:" in SyncConfig().asm()


def test_pre_work_is_padded_back_to_the_exact_pause_budget():
    from st68k.annotate import block_cycles
    sc = SyncConfig()
    work = "\n".join(["    add.l   d1,d2"] * 100)          # 100 x 8c = 800c
    region = sc.asm(work).split("eor.b")[0]                # everything before the 60/50 Hz dance
    lo, hi = block_cycles(region)
    assert lo == hi == sc.pause_budget, f"pause must still cost exactly {sc.pause_budget}c, got {lo}"
    assert ".pause:" not in region, "the dead loop should be gone, replaced by the work"


def test_pre_work_over_the_pause_is_refused():
    with pytest.raises(ValueError, match="TOP BORDER WILL CLOSE"):
        SyncConfig().asm("\n".join(["    add.l   d1,d2"] * 3000))   # 24000c > 17052c


def test_pre_work_must_have_a_fixed_cost():
    """A bare branch in the pause means two different distances to the top-border pulse. It must be
    refused, and the message must say what to do about it: wrap it in ;@balance so both arms cost
    the same. (A branchy-but-BALANCED region is fine — that is what Aurora's preamble is.)"""
    with pytest.raises(ValueError, match="variable-cost"):
        SyncConfig().asm("    tst.w   d0\n    beq.s   .x\n    nop\n.x:\n")


def test_pre_work_may_contain_balanced_branches():
    """...and the balanced form IS accepted: `;@balance` equalises the arms, so the region has one
    determinate cost and the pause can be padded back to exactly its budget. This is the whole
    reason Aurora's per-frame logic can live in the pause at all."""
    sc = SyncConfig()
    branchy = ("    move.w  (a3),d2\n;@balance\n    bge.s .alt\n;@fill\n    bra.s .end\n"
               ";@balance alt\n.alt:\n    add.l d1,d2\n    add.l d1,d2\n;@balance end\n.end:\n")
    out = sc.asm(branchy)                      # must not raise
    assert "bge.s .alt" in out
    # the arms were equalised, and the region padded out to the pause budget
    assert any("@balance fill" in ln for ln in out.splitlines())
    assert any(f"budget {sc.pause_budget}" in ln for ln in out.splitlines())


@pytest.mark.hatari
def test_pre_work_still_opens_all_borders_all_wakestates(tmp_path):
    """The proof that matters: fill the pause with real work and the four borders must still open on
    all four wakestates. ~12,000c is about what Aurora's two sprites cost."""
    from lockstep.wakestate import verify_overscan
    work = "\n".join(["    add.l   d1,d2"] * 1500)          # 12000c, register-only (cannot fault)
    prog = str(tmp_path / "PRE.TOS")
    OverscanFrame(pre=work).build(prog, setup=GREEN_SETUP)
    rep = verify_overscan(prog, frames=range(320, 322), timeout=120.0)
    assert rep.ok, "work in the pause must not disturb the borders:\n" + rep.matrix()
