"""Lockstep — the full-sync scheduler for Atari ST demos (DESIGN §7).

*Pack every line in lockstep with the beam.* The author declares two things — a **line
template** of immovable border events (pegs nailed to exact cycle offsets) and a **work
stream** of effect logic — and the packer pours the work into the gaps between pegs so
every scanline closes on exactly 512c with the borders open.

Lockstep is the *product*; it layers on top of the `st68k` package, which stays the
internal cycle-exact 68000/ST cost engine. The packer is pure *placement*: it decides
which work lands in which gap, then emits a directive-laden intermediate and hands it to
`st68k.preprocess.expand()`, which does the exact, bus-phase-aware filler sizing and the
odd-residue guard — already tested. So the scheduler is correct by reuse, not by a second
timing implementation.

Two front-ends converge on one core (DESIGN §7, P5):
  - the Python API here (`LineTemplate` / `Peg` / `WorkBlock` / `WorkStream` + `pack`),
    codegen-native like the existing `gen_*.s` flow;
  - a `;@`-directive surface (`;@template/@peg/@work/@schedule`) that compiles *down* to
    these same objects (added once the core is green).
"""

from __future__ import annotations

from .model import LineTemplate, Move, Peg, Segment, StepWork, WorkBlock, WorkStream
from .packer import PackError, PackResult, pack, pack_schedule

__all__ = [
    "LineTemplate", "Peg", "WorkBlock", "WorkStream", "Move", "StepWork", "Segment",
    "pack", "pack_schedule", "PackResult", "PackError",
]
