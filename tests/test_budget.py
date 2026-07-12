"""Tests for lockstep.budget (the frame-level slack / VBL-jitter safety net).

Fast tests (no emulator) pin the cost model and the warning thresholds: the skeleton cost, the
per-frame slack, the pause-loop formula, and the OVER / RISK / UNRESERVED warnings. A hatari-marked
acceptance test proves the model's slack boundary is REAL — a tail over budget warns at build time
AND actually closes the borders in Hatari (the warning corresponds to a real closure), while a
small tail stays quiet and open.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from st68k.cycles import STF_PAL                                        # noqa: E402
from st68k.hatari import HatariError, find_tos                          # noqa: E402
from lockstep.budget import (DEFAULT_JITTER_MARGIN, FrameBudget,        # noqa: E402
                             _pause_loop_cost, assert_within_budget, frame_budget)
from lockstep.skeleton import OverscanFrame                             # noqa: E402



def test_pause_loop_cost_matches_known_figure():
    # move.w #1064,d0 / .p: nop / dbra d0,.p == ~17052c (bordopen's documented figure)
    assert _pause_loop_cost(1064) == 17052
    assert _pause_loop_cost(0) == 28


def test_skeleton_and_slack_math():
    fb = frame_budget(OverscanFrame())
    assert fb.bands == 260 * 512                       # 260 lines x 512c, exact
    assert fb.skeleton == fb.handler_wrap + fb.prelude + fb.bands
    assert fb.slack_budget == STF_PAL.cycles_per_frame - fb.skeleton
    # the standard frame leaves a few thousand cycles of slack (sanity band, not a magic number)
    assert 5000 < fb.slack_budget < 15000
    assert fb.ok and not fb.warnings                   # no tail -> within budget


def test_small_tail_is_quiet():
    fb = frame_budget(OverscanFrame(), tail="\n".join(["nop"] * 20))    # 80c
    assert fb.tail_cost == 80
    assert fb.ok and fb.slack_after_tail == fb.slack_budget - 80


def test_over_budget_warns():
    f = OverscanFrame()
    slack = frame_budget(f).slack_budget
    fb = frame_budget(f, tail_cost=slack + 500)
    assert not fb.ok
    assert any("OVER budget" in w for w in fb.warnings)
    assert "500c over" in fb.warnings[0]


def test_near_boundary_is_risk_not_over():
    f = OverscanFrame()
    slack = frame_budget(f).slack_budget
    fb = frame_budget(f, tail_cost=slack - 10)          # inside the jitter margin
    assert not fb.ok
    assert any("RISK" in w for w in fb.warnings)
    assert not any("OVER budget" in w for w in fb.warnings)


def test_just_inside_margin_is_ok():
    f = OverscanFrame()
    slack = frame_budget(f).slack_budget
    fb = frame_budget(f, tail_cost=slack - DEFAULT_JITTER_MARGIN - 100)
    assert fb.ok


def test_unreserved_data_dependent_tail_warns():
    fb = frame_budget(OverscanFrame(), tail_cost=100, reserved=False)
    assert any("UNRESERVED" in w for w in fb.warnings)
    # the same cost, reserved (worst-cased), is fine
    assert frame_budget(OverscanFrame(), tail_cost=100, reserved=True).ok


def test_assert_within_budget_guard():
    import pytest
    f = OverscanFrame()
    slack = frame_budget(f).slack_budget
    assert_within_budget(f, tail_cost=100)                       # fits -> no raise
    with pytest.raises(AssertionError):
        assert_within_budget(f, tail_cost=slack + 500)           # over -> raise
    with pytest.raises(AssertionError):
        assert_within_budget(f, tail_cost=slack - 10)            # risk -> raise by default
    assert_within_budget(f, tail_cost=slack - 10, allow_risk=True)   # risk tolerated


def test_report_names_cost_and_margin():
    f = OverscanFrame()
    rep = frame_budget(f, tail_cost=frame_budget(f).slack_budget + 200).report()
    assert "OVER budget" in rep and "slack" in rep


# ------------------------------------------------------------------ acceptance (needs hatari)
@pytest.mark.hatari
def test_over_budget_tail_actually_closes_borders(tmp_path):
    """The model's slack boundary is REAL: a post-display tail over budget warns statically AND
    closes the borders in Hatari — the warning corresponds to a real closure."""
    from lockstep.wakestate import verify_overscan
    from tests.test_skeleton import GREEN_SETUP

    f = OverscanFrame()
    slack = frame_budget(f).slack_budget
    big_n = slack // 4 + 3000                            # dcb.w count -> ~12000c over slack
    fb = frame_budget(f, tail_cost=big_n * 4)
    assert not fb.ok and any("OVER budget" in w for w in fb.warnings)   # warned BEFORE hatari

    prog = str(tmp_path / "OVER.TOS")
    f.build(prog, setup=GREEN_SETUP, tail=f"\n    dcb.w {big_n},$4e71")
    rep = verify_overscan(prog, wakestates=(3,), frames=(320,), timeout=90.0)
    # ws3 opens all four borders on the shipped skeleton; the over-budget tail must close some.
    assert not rep.results["ws3"].ok(("top", "right", "bottom")), \
        "over-budget tail should close borders, but they stayed open:\n" + rep.matrix()


if __name__ == "__main__":
    print(frame_budget(OverscanFrame(), tail="\n".join(["nop"] * 100)).report())
