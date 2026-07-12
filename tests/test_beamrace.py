"""Tests for lockstep.beamrace (checked beam-race band geometry).

Pure arithmetic (no emulator): a bouncing band written row-by-row must lay each row down ahead
of the beam (race) and clear the bottom-border structure (fit). These pin the check, reproduce a
real demo's hand-derived scroller constraint, and prove the checker CATCHES a band placed too high
(tears) or too deep (collides) — replacing the trusted hand comment with a certificate.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest                                                           # noqa: E402
from lockstep.beamrace import BandGeometry, certify_race               # noqa: E402

# The geometry of a real full-sync demo's bouncing scroller band, whose author derived the race
# constraint by hand and left it as a comment. The numbers are frozen here rather than imported
# from the demo: they are the *test fixture*, and pinning them keeps this coverage independent of
# which examples happen to ship. Work starts at the upper/lower split (WORK_START); LPR is
# scanlines per written row; the up-wander drives the race, the down-bias only affects the fit.
WORK_START = 104        # upper/lower field split
BAND_Y = 193            # band centre
BAND_H = 34             # band height
LPR = 2                 # scanlines per row
AMP_UP = 7              # up-wander
AMP_DOWN = 29           # down-bias (asymmetric)
FRAME_BOTTOM = 259      # 227 main lines + 32 of opened bottom border


def _demo_band(center=None, height=None, amp_up=None):
    return BandGeometry(
        work_start=WORK_START,
        center=BAND_Y if center is None else center,
        height=BAND_H if height is None else height,
        lines_per_row=LPR,
        amplitude=AMP_UP if amp_up is None else amp_up,
        amp_down=AMP_DOWN,
        frame_bottom=FRAME_BOTTOM)


def test_real_scroller_band_certifies_the_race():
    # the real band races the beam — the hand comment BANDY > WORK_START + BAND_H*(LPR-1),
    # now COMPUTED instead of trusted.
    res = _demo_band().check()
    assert res.ok, res.report()
    assert res.first_bad_row is None
    certify_race(_demo_band())             # does not raise


def test_race_floor_matches_hand_formula():
    g = _demo_band()
    # aggregate constraint (the hand comment): top_min must exceed work_start + height*(LPR-1)
    assert g.race_floor == WORK_START + BAND_H * (LPR - 1)
    assert g.top_min > g.race_floor


def test_band_too_high_tears():
    # push the band centre up so its top row races into the split -> the last rows fall behind
    g = _demo_band(center=150)
    res = g.check()
    assert not res.ok
    assert res.first_bad_row is not None
    assert any("tears" in v for v in res.violations)
    with pytest.raises(ValueError):
        certify_race(g)


def test_band_too_deep_collides():
    # a large asymmetric down-bias pushes the band bottom past the bottom-border structure
    g = BandGeometry(work_start=104, center=193, height=34, lines_per_row=2,
                     amplitude=7, amp_down=40, frame_bottom=227)
    res = g.check()
    assert not res.ok
    assert any("collides" in v for v in res.violations)


def test_first_violating_row_is_reported():
    # lines_per_row=3 tightens deeper rows; find the exact first row that falls behind
    g = BandGeometry(work_start=100, center=130, height=20, lines_per_row=3,
                     amplitude=0, frame_bottom=300)
    res = g.check()
    assert not res.ok
    r = res.first_bad_row
    # the reported row is the first whose write-completion exceeds its display line
    assert 100 + (r + 1) * 3 > g.top_min + r
    assert 100 + r * 3 <= g.top_min + (r - 1) if r > 0 else True


def test_lower_lines_per_row_relaxes_the_race():
    # at LPR=1 the write keeps pace trivially (race_floor == work_start), so a tall band is fine
    g = BandGeometry(work_start=104, center=140, height=60, lines_per_row=1,
                     amplitude=5, frame_bottom=300)
    assert g.check().ok


def test_symmetric_amplitude_defaults_down_to_up():
    g = BandGeometry(work_start=104, center=193, height=34, lines_per_row=2,
                     amplitude=7, frame_bottom=300)
    assert g.bottom_max == 193 + 17 + 7        # amp_down defaults to amplitude


if __name__ == "__main__":
    print(_demo_band().check().report())
