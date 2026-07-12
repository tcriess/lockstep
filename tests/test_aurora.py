"""Aurora as a golden test of the cycle model.

`examples/aurora` rebuilds a demo that provably runs on real hardware, and the original source
carries its author's hand-counted cycle padding — every `dcb.w N,$4e71` in the VBL preamble is a
number a human derived with a pencil and then *verified on an ST*. That makes those numbers an
oracle we own: if Lockstep's `;@balance` re-derives them exactly, the branch costs and the arm
accounting are right; if it is off by even one word, they are not.

This is not a decorative test. Lockstep once emitted every one of these fills 4 cycles short (it
costed a taken branch at the 68000 manual's raw 10c instead of the 12c the ST's prefetch-refill bus
realignment actually charges). 4 cycles was enough to walk the 60/50 Hz pulse off its scanline, and
the top *and* bottom borders silently stayed shut — while left/right still opened, because those are
driven by absolute register writes rather than by the pulse. The scroller lives in the bottom border,
so the visible symptom was "the scroller does not render", metres away from the cause.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util  # noqa: E402

_AURORA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "examples", "aurora", "aurora.py")


def _aurora():
    spec = importlib.util.spec_from_file_location("aurora_ex", _AURORA)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _hand_counted_fills(m) -> list[int]:
    """Aurora's own `dcb.w N,$4e71` balance padding, in source order."""
    src = m._orig("aurora.s").splitlines()
    start = next(i for i, ln in enumerate(src) if "first, toggle the screen addresses" in ln)
    end = next(i for i, ln in enumerate(src) if re.match(r"\s*dcb\.w 798,\$4e71", ln))
    return [int(mo.group(1)) for ln in src[start:end]
            if (mo := re.match(r"\s+dcb\.w\s+(\d+),\$4e71", ln))]


def test_balance_reproduces_auroras_hand_counted_padding():
    from lockstep.skeleton import SyncConfig

    m = _aurora()
    hand = _hand_counted_fills(m)
    assert len(hand) == 9, f"expected 9 hand-balanced blocks in aurora.s, found {len(hand)}"

    prelude = SyncConfig()._prelude(m.aurora_pre())
    got = [int(mo.group(1)) for ln in prelude.splitlines()
           if (mo := re.match(r"\s+dcb\.w\s+(\d+),\$4e71.*@balance fill", ln))]

    assert got == hand, (
        f"@balance no longer re-derives Aurora's hand-counted padding.\n"
        f"  aurora.s (verified on hardware): {hand}\n"
        f"  lockstep ;@balance             : {got}\n"
        f"A uniform off-by-one-word means a branch cost is wrong — see m68k_table._branch."
    )


def test_pre_fits_the_pause_budget():
    """The preamble is a measured distance, not slack: it must close to exactly `pause_budget`, and
    the padding Lockstep needs must land within a couple of words of the one Aurora hand-wrote
    (`dcb.w 798`). A large divergence means the region's cost drifted, and the top-border pulse with
    it."""
    from lockstep.skeleton import SyncConfig

    m = _aurora()
    sc = SyncConfig()
    prelude = sc._prelude(m.aurora_pre())
    final = [int(mo.group(1)) for ln in prelude.splitlines()
             if (mo := re.match(r"\s+dcb\.w\s+(\d+),\$4e71.*@fill", ln))]
    assert len(final) == 1, "expected exactly one ;@fill closing the pause region"
    assert abs(final[0] - 798) <= 4, (
        f"pause padding is dcb.w {final[0]}; aurora.s hand-wrote dcb.w 798. The few words of "
        f"slack are the difference between Aurora's VBL prologue and emit_program's."
    )
