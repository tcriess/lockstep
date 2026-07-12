"""Tests for lockstep.wakestate (the all-wakestate border guarantee).

Two tiers:
  - detector unit tests on SYNTHETIC frames (no emulator) — always run, fast. They pin the
    edge-band open/closed logic and the flicker/status reporting against the exact pixel
    geometry the shipped fixtures produce (832×552, black border, ~0.00 vs ~0.7 edge fill).
  - a hatari-marked contract test on the real .TOS fixtures: `bordws.tos` (the wakestate-robust
    build) must open all four borders on all four wakestates, and `bordopen.tos` (the original
    Aurora lock) must FAIL on ws2 — the documented, hand-verified behaviour, now automatic.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from st68k.hatari import HatariError, find_tos                         # noqa: E402
from lockstep.wakestate import (OverscanReport, WakestateResult,       # noqa: E402
                                borders_open, edge_fill, verify_overscan)


FIX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "examples", "bordopen")

CANVAS = (552, 832)   # (h, w) — the full-overscan canvas the fixtures render at


def _frame(png, *, left=True, right=True, top=True, bottom=True):
    """Synthesize an 832×552 frame: black border, a green display rectangle whose extent
    encodes which borders are open (an open border => the display reaches that edge band)."""
    import numpy as np
    from PIL import Image
    h, w = CANVAS
    a = np.zeros((h, w, 3), dtype=np.uint8)          # black border everywhere
    # display rectangle. An OPEN border reaches to within a few px of the canvas edge (like the
    # real fixtures: bbox 0..823 on an 832-wide canvas — the extreme corners stay border, so the
    # corner-sampled border colour is reliable). A CLOSED border pulls its edge ~96px (LR) /
    # ~90px (TB) inward, leaving that whole edge band at border colour.
    x0 = 4 if left else 96
    x1 = w - 4 if right else w - 96
    y0 = 4 if top else 90
    y1 = h - 4 if bottom else h - 90
    a[y0:y1, x0:x1] = (0, 255, 0)                    # green display fill
    Image.fromarray(a, "RGB").save(png)
    return png


def test_edge_fill_separates_open_from_closed(tmp_path):
    allopen = _frame(str(tmp_path / "all.png"))
    f = edge_fill(allopen)
    for e in ("left", "right", "top", "bottom"):
        assert f[e] > 0.5, f"{e} band should be filled when open, got {f[e]}"
    assert f["coverage"] > 0.9


def test_borders_open_detects_each_closed_edge(tmp_path):
    # left+bottom closed, top+right open — the exact bordopen ws2 signature
    p = _frame(str(tmp_path / "lb.png"), left=False, bottom=False)
    st = borders_open(p)
    assert st == {"left": False, "right": True, "top": True, "bottom": False,
                  "coverage": st["coverage"]}
    assert st["coverage"] < 0.9   # a closed border reduces coverage


def test_border_color_read_from_corner_even_when_fully_open(tmp_path):
    # all four borders open but the extreme corners are still border colour -> detector works
    p = _frame(str(tmp_path / "open.png"))
    assert borders_open(p)["left"] is True


def test_status_and_flicker_reporting(tmp_path):
    open_f = borders_open(_frame(str(tmp_path / "o.png")))
    closed_bot = borders_open(_frame(str(tmp_path / "c.png"), bottom=False))
    # steady open on both frames -> 'open'
    r = WakestateResult("ws1", [320, 321], [open_f, open_f], [])
    assert r.status("bottom") == "open" and r.ok()
    # bottom differs between consecutive frames -> 'flicker' (the period-2 trap)
    r2 = WakestateResult("ws2", [320, 321], [open_f, closed_bot], [])
    assert r2.status("bottom") == "flicker"
    assert not r2.ok()
    # closed on every frame -> 'closed'
    r3 = WakestateResult("ws3", [320, 321], [closed_bot, closed_bot], [])
    assert r3.status("bottom") == "closed"


def test_report_matrix_and_ok(tmp_path):
    op = borders_open(_frame(str(tmp_path / "o.png")))
    good = WakestateResult("ws1", [320, 321], [op, op], [])
    rep = OverscanReport({"ws1": good}, ("left", "right", "top", "bottom"), [320, 321])
    assert rep.ok
    assert "ALL borders open" in rep.matrix()


# --------------------------------------------------------------------- fixture contract
@pytest.mark.hatari
def test_robust_build_opens_all_borders_all_wakestates():
    """bordws.tos (left stabiliser + cross-boundary bottom bust) opens all four borders on
    ws1..ws4, flicker-free across consecutive frames."""
    prog = os.path.join(FIX, "bordws.tos")
    rep = verify_overscan(prog, frames=range(320, 322), timeout=90.0)
    assert rep.ok, "robust build should open all borders on all wakestates:\n" + rep.matrix()


@pytest.mark.hatari
def test_original_lock_fails_bottom_on_ws2():
    """bordopen.tos (the plain Aurora MMU lock) leaves the left AND bottom borders CLOSED on
    ws2 — the documented wakestate frontier the robust build fixes. Guards against a silent
    'both builds look the same' regression in the detector or the fixtures."""
    prog = os.path.join(FIX, "bordopen.tos")
    rep = verify_overscan(prog, wakestates=(2,), frames=(320,), timeout=90.0)
    st = rep.results["ws2"].per_frame[0]
    assert st["top"] and st["right"], "ws2 should still open top+right"
    assert not st["bottom"], "ws2 bottom should be CLOSED on the original lock"
    assert not st["left"], "ws2 left should be CLOSED on the original lock"
