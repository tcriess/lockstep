"""Lockstep — the all-wakestate, multi-frame border guarantee.

`verify.py` proves every scanline is 512c with the video OFF; `visual.py` takes a single
screenshot in one wakestate. Neither catches the property that actually decides whether a
full-sync intro ships: **do all four borders open, on every wakestate, and stay open frame
after frame** (no period-2 flicker). That has been checked by hand — bespoke `/tmp` scripts
and tecer's interactive eye — every single time, and the two regressions that bit this
project (a +672c rewrite that silently closed the borders; a slack-guard that flickered
them every other frame) were invisible to the toolkit. This module makes the check
first-class:

  cycles as the gate — `verify.verify_segments` proves the bands are 512c (wakestate-
    invariant: the counted 512c lines don't change with the wakestate, only the once-per-
    frame lock does — so one cheap `--disable-video` run gates every build);
  pixels as the proof — `verify_overscan` runs the built `.TOS` with video ON across
    ws1..ws4 × consecutive frames, detects each of the four borders from the rendered
    frame, and reports a wakestate × border matrix with flicker flagged.

The detector keys on the **outer overscan edge bands**: on the 832×552 full-overscan canvas
a closed border leaves its edge band at the border colour (measured fill ≈ 0.00), an open
one spills display colour into it (≈ 0.6–1.0). A threshold of 0.2 separates them with a mile
to spare. The border colour is read from the canvas corners (always overscan, even with all
four borders open), so any demo whose display differs from its border works with no probe;
for a demo whose effect can leave the overscan edge dark, fill a bright `probe_fill()` strip
or pass an explicit `border=`.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass

from st68k.hatari import HatariError
from .visual import active_bbox, shoot_counter, shoot_tos  # noqa: F401  (active_bbox re-exported)

EDGES = ("left", "right", "top", "bottom")

# Outer edge-band widths (px) sampled for fill. The overscan margins on the 832×552 canvas
# are ~96px (left/right) and ~76px (top/bottom); these bands sit well inside the margin, so
# they only fill when that border is actually open.
_BAND_LR = 32
_BAND_TB = 24
_OPEN_THRESH = 0.2   # edge-band fill fraction above which the border is "open" (0.00 vs 0.6+)


# --------------------------------------------------------------------------- detectors
def _load(png: str):
    import numpy as np
    from PIL import Image
    return np.asarray(Image.open(png).convert("RGB")).astype(np.int16)


def _border_color(a):
    """The border (overscan) colour, taken as the most common of the four canvas corners.
    Corners are overscan even when all four borders are open, so this is robust; using the
    mode tolerates one corner being clipped by the display rectangle."""
    import numpy as np
    h, w, _ = a.shape
    corners = np.stack([a[0, 0], a[0, w - 1], a[h - 1, 0], a[h - 1, w - 1]])
    # most common corner colour
    uniq, counts = np.unique(corners, axis=0, return_counts=True)
    return tuple(int(v) for v in uniq[int(counts.argmax())])


def edge_fill(png: str, *, border=None, band_lr: int = _BAND_LR,
              band_tb: int = _BAND_TB) -> dict:
    """Fraction of each outer overscan edge band that is display (differs from the border
    colour), plus overall `coverage`. A closed border reads ~0.00; an open one ~0.6–1.0."""
    import numpy as np
    a = _load(png)
    h, w, _ = a.shape
    if border is None:
        border = _border_color(a)
    mask = np.any(a != np.array(border), axis=2)
    return {
        "left":   float(mask[:, :band_lr].mean()),
        "right":  float(mask[:, w - band_lr:].mean()),
        "top":    float(mask[:band_tb, :].mean()),
        "bottom": float(mask[h - band_tb:, :].mean()),
        "coverage": float(mask.mean()),
    }


def borders_open(png: str, *, border=None, thresh: float = _OPEN_THRESH,
                 band_lr: int = _BAND_LR, band_tb: int = _BAND_TB) -> dict:
    """Which of the four borders are open in `png` — {edge: bool} for the four edges plus
    the raw `coverage` float. See `edge_fill` for the measurement."""
    f = edge_fill(png, border=border, band_lr=band_lr, band_tb=band_tb)
    out = {e: f[e] > thresh for e in EDGES}
    out["coverage"] = f["coverage"]
    return out


def all_open(png: str, edges=EDGES, **kw) -> bool:
    """True iff every requested border is open in `png`."""
    st = borders_open(png, **kw)
    return all(st[e] for e in edges)


# A ready-made bright-fill snippet for demos whose effect could leave the overscan edge
# dark: paint the whole screen a non-border colour so an open border is unambiguous. Handy
# when building a probe variant of a demo that churns the palette (Aurora does) for
# `verify_overscan`, which otherwise cannot tell an open border from a repainted one.
def probe_fill(screen_addr: int, *, words: int = 0x4000, value: int = 0xFFFFFFFF) -> str:
    """Asm that fills `words`*2 bytes at `screen_addr` with `value` (default all planes set =
    the brightest palette entry). Drop into a demo's setup so every open border shows fill."""
    return (f"    move.l  #${screen_addr:x},a2\n"
            f"    move.w  #{words - 1},d0\n"
            f".pfill: move.l #${value & 0xffffffff:x},(a2)+\n"
            f"    dbra    d0,.pfill\n")


# --------------------------------------------------------------------------- capture
def _wsname(w) -> str:
    return w if isinstance(w, str) else f"ws{int(w)}"


def _capture(prog: str, png: str, *, wakestate: str, at_vbl: int, count_addr,
             tos, timeout: float):
    """One headless screenshot of `prog` at `wakestate`, at the frame just past `at_vbl`.
    Uses the demo's own frame counter (`shoot_counter`) when `count_addr` is given — needed
    when the open bottom border stalls Hatari's nVBLs — otherwise the fast VBL trigger."""
    if count_addr is not None:
        return shoot_counter(prog, png, count_addr=count_addr, count=at_vbl,
                             video_timing=wakestate, tos=tos, timeout=timeout)
    return shoot_tos(prog, png, at_vbl=at_vbl, video_timing=wakestate, tos=tos,
                     timeout=timeout)


@dataclass
class WakestateResult:
    wakestate: str
    frames: list           # the at_vbl trigger points, in order
    per_frame: list        # list of borders_open() dicts, one per frame
    pngs: list             # captured PNG paths (kept for inspection)

    def status(self, edge: str) -> str:
        """'open' (open on every sampled frame), 'closed' (closed on every frame), or
        'flicker' (differs between consecutive frames — the period-2 trap)."""
        vals = [bool(pf[edge]) for pf in self.per_frame]
        if all(vals):
            return "open"
        if not any(vals):
            return "closed"
        return "flicker"

    def ok(self, edges=EDGES) -> bool:
        return all(self.status(e) == "open" for e in edges)


@dataclass
class OverscanReport:
    results: dict          # wakestate name -> WakestateResult
    edges: tuple
    frames: list

    @property
    def ok(self) -> bool:
        return all(r.ok(self.edges) for r in self.results.values())

    def matrix(self) -> str:
        sym = {"open": "open  ", "closed": "CLOSED", "flicker": "FLICKER"}
        head = "  ".join(f"{e:<7}" for e in self.edges)
        out = [f"overscan matrix — wakestates × borders  (frames {self.frames[0]}"
               f"..{self.frames[-1]}, {len(self.frames)} consecutive)",
               f"        {head}"]
        for wsname, r in self.results.items():
            row = "  ".join(f"{sym[r.status(e)]:<7}" for e in self.edges)
            mark = "" if r.ok(self.edges) else "   <- FAIL"
            out.append(f"  {wsname:<5} {row}{mark}")
        out.append(f"  => {'ALL borders open on all wakestates, no flicker' if self.ok else 'FAIL — see above'}")
        return "\n".join(out)


def verify_overscan(prog: str, *, wakestates=(1, 2, 3, 4), frames=range(320, 323),
                    edges=EDGES, count_addr=None, border=None, thresh: float = _OPEN_THRESH,
                    tos: str | None = None, timeout: float = 90.0,
                    keep_pngs: bool = False, png_dir: str | None = None) -> OverscanReport:
    """Run a built `.TOS` headless across `wakestates` × `frames` (consecutive frame triggers)
    with video on, and report which borders open on each — an OverscanReport whose `.matrix()`
    is the ws×border table and whose `.ok` is the single ship/no-ship bit.

    `frames` are the `at_vbl` trigger points; use ≥2 consecutive values so period-2 flicker
    is caught (a single shot cannot see it — the lesson that cost this project a flicker bug).
    `count_addr` switches to the demo's own frame counter (for bottom-open demos that stall
    Hatari's nVBLs). Raises HatariError if hatari/TOS is unavailable."""
    frames = list(frames)
    if not frames:
        raise ValueError("need at least one frame trigger point")
    work = png_dir or tempfile.mkdtemp(prefix="lockstep_ws_")
    os.makedirs(work, exist_ok=True)
    results: dict[str, WakestateResult] = {}
    for w in wakestates:
        ws = _wsname(w)
        per_frame, pngs = [], []
        for f in frames:
            png = os.path.join(work, f"{ws}_f{f}.png")
            _capture(prog, png, wakestate=ws, at_vbl=f, count_addr=count_addr,
                     tos=tos, timeout=timeout)
            per_frame.append(borders_open(png, border=border, thresh=thresh))
            pngs.append(png)
        results[ws] = WakestateResult(ws, frames, per_frame, pngs)
    return OverscanReport(results, tuple(edges), frames)


def assert_overscan_open(prog: str, *, wakestates=(1, 2, 3, 4), frames=range(320, 323),
                         edges=EDGES, **kw) -> OverscanReport:
    """pytest one-liner: assert every requested border opens on every wakestate across
    consecutive frames. Raises AssertionError carrying the full matrix on any failure."""
    report = verify_overscan(prog, wakestates=wakestates, frames=frames, edges=edges, **kw)
    if not report.ok:
        raise AssertionError("overscan not fully open:\n" + report.matrix())
    return report
