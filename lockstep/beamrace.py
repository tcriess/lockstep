"""Lockstep — checked beam-race band geometry.

The packer's `WorkBlock(beam=(lo,hi))` pins a write to a cycle window *within* a line. This
module handles the orthogonal, *vertical* constraint: a band written row-by-row down the screen
while the beam is displaying it must lay each row down BEFORE the beam reaches it — the write
races the ray. A see-through bouncing scroller is the case: a text band that wanders vertically,
each row taking `lines_per_row` scanlines of work to write, starting from the upper/lower split.

The race was solved on paper and left as a hand comment (`BANDY > SCR_HALF + SCR_H·(LPR-1)`),
unchecked — if the band drifts too high (its up-bounce), the last row's write falls behind the
beam and the text tears. This module makes it a computed certificate: declare the band geometry
once, and `BandGeometry.check()` confirms the race holds for every row at the worst-case bounce,
or reports the first violating row. Pure arithmetic — no emulator.

The model (all in display lines; row 0 = the band's top row):
  - the band's write work starts at display line `work_start` (the split), row r finishing at
    `work_start + (r+1)*lines_per_row`;
  - at its highest up-bounce the band's top row sits at `top_min = center - height//2 - amplitude`,
    so row r is displayed at `top_min + r`;
  - RACE: for every row, write-completion <= display line -> `work_start + (r+1)*LPR <= top_min + r`
    (tightest at the last row; the aggregate form is `top_min > work_start + height*(LPR-1)`);
  - FIT: at its deepest down-bounce the band's bottom must clear the frame's lower structure —
    `bottom_max + settle < frame_bottom` (e.g. the bottom-border bust-settle at main_lines).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RaceResult:
    ok: bool
    violations: list[str]
    first_bad_row: int | None    # first row index whose write falls behind the beam (or None)

    def report(self) -> str:
        if self.ok:
            return "beam-race: OK — every band row is written ahead of the beam (worst-case bounce)"
        return "beam-race: FAIL\n" + "\n".join(f"  !! {v}" for v in self.violations)


@dataclass(frozen=True)
class BandGeometry:
    """A vertically-bouncing band written row-by-row, racing the beam. All fields are in display
    lines (or rows for `height`). Construct it from the demo's band constants and `check()` it."""

    work_start: int      # display line where the band's row-writing work begins (the split)
    center: int          # band CENTRE display line at rest (bounces up/down)
    height: int          # band height in ROWS, guards included
    lines_per_row: int   # work scanlines to lay down one band row
    amplitude: int       # worst-case UP-bounce amplitude, in display lines (drives the race)
    frame_bottom: int    # first line the band must stay ABOVE (e.g. main_lines / the bust line)
    amp_down: int | None = None   # DOWN-bounce amplitude if asymmetric (e.g. a down-bias);
                                  #   defaults to `amplitude` (symmetric bounce). Drives the fit.
    settle: int = 0      # extra margin the band must leave below itself (bust-settle guard)

    @property
    def _down(self) -> int:
        return self.amplitude if self.amp_down is None else self.amp_down

    @property
    def top_min(self) -> int:
        """Highest the band's top row reaches (worst case for the race: nearest the split)."""
        return self.center - self.height // 2 - self.amplitude

    @property
    def bottom_max(self) -> int:
        """Deepest the band's bottom row reaches (worst case for the fit)."""
        return self.center + self.height // 2 + self._down

    @property
    def race_floor(self) -> int:
        """`top_min` must exceed this for the whole band to race the beam (aggregate form)."""
        return self.work_start + self.height * (self.lines_per_row - 1)

    def _first_bad_row(self) -> int | None:
        """The first row whose write-completion line exceeds its display line at the up-bounce."""
        for r in range(self.height):
            write_done = self.work_start + (r + 1) * self.lines_per_row
            display_at = self.top_min + r
            if write_done > display_at:
                return r
        return None

    def check(self) -> RaceResult:
        """Certify the race (every row written ahead of the beam) AND the fit (band clears the
        frame's lower structure), at the worst-case bounce. Returns a RaceResult."""
        violations: list[str] = []
        bad = self._first_bad_row()
        if bad is not None:
            wd = self.work_start + (bad + 1) * self.lines_per_row
            da = self.top_min + bad
            violations.append(
                f"row {bad} of {self.height}: written by line {wd} but the beam displays it at "
                f"line {da} (top_min={self.top_min}) — the write falls {wd - da} line(s) behind, "
                f"text tears. Need top_min > {self.race_floor} (raise band centre, lower the "
                f"split, cut band height, or reduce lines_per_row/amplitude).")
        if self.bottom_max + self.settle >= self.frame_bottom:
            violations.append(
                f"fit: band bottom reaches line {self.bottom_max} (+{self.settle} settle) but must "
                f"stay above line {self.frame_bottom} — the band collides with the bottom-border "
                f"structure. Lower band centre or amplitude, or raise frame_bottom.")
        return RaceResult(not violations, violations, bad)


def certify_race(geom: BandGeometry) -> BandGeometry:
    """Raise ValueError (with the first violating row / fit) if `geom` does not race the beam;
    return it unchanged if it does. Use at build time to replace the hand-checked band comment."""
    res = geom.check()
    if not res.ok:
        raise ValueError(res.report())
    return geom
