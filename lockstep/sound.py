"""Lockstep — sound-replay profiling (DESIGN §8).

A full-sync demo can't take an interrupt, so a tune's per-tick replay (an SNDH `play`, or
Aurora's `dosound`) must run inline at a fixed point each frame. But that replay has a
DATA-DEPENDENT cycle cost — dominated by PSG register writes, each nominal + 4c (TIMING.md,
verified) — so the budget you must reserve (or fit into the frame's slack) is the tune's
WORST-CASE per-tick cost. On paper the PSG wait states make this opaque (the number that
"never added up"); this module pins it exactly by running the replay across the tune, tick
by tick, in cycle-exact Hatari (the P3 oracle).

`profile_play` returns the per-tick cost envelope; `.reserve` is the worst case rounded to a
phase-stable budget — what the scheduler reserves for the sound peg (or must leave free in
the post-display slack, the way Aurora does it).
"""

from __future__ import annotations

from dataclasses import dataclass

from st68k.cycles import round_up_4
from st68k.hatari import measure_markers


@dataclass
class PlayEnvelope:
    """Per-tick replay cost across the profiled run (cycles)."""

    per_tick: list[int]

    @property
    def min(self) -> int:
        return min(self.per_tick)

    @property
    def max(self) -> int:
        return max(self.per_tick)

    @property
    def typical(self) -> int:
        return sorted(self.per_tick)[len(self.per_tick) // 2]

    @property
    def reserve(self) -> int:
        """Worst-case budget, rounded up to a multiple of 4 (phase-stable) — the cycles the
        scheduler reserves for this sound peg every frame (DESIGN §8)."""
        return round_up_4(self.max)

    def report(self) -> str:
        n = len(self.per_tick)
        hot = self.per_tick.count(self.max)
        return (f"sound replay: {n} ticks profiled\n"
                f"  per-tick cycles: min {self.min}  typ {self.typical}  max {self.max}"
                f"  ({hot} tick(s) at worst case)\n"
                f"  => reserve {self.reserve}c/frame for this peg (worst case, phase-stable)")


def profile_play(play_body: str, *, ticks: int, setup: str = "", data: str = "",
                 tos: str | None = None, run_vbls: int = 500,
                 timeout: float = 180.0) -> PlayEnvelope:
    """Measure a replay routine's per-tick cycle cost across `ticks` invocations in Hatari.

    `play_body` is the replay's instructions (no label/rts — it is wrapped as a subroutine
    `__play` and called once per tick). `setup` runs first (e.g. point a register at the
    tune). `data`, if given, is emitted as a `dc.b` block labelled `__snddata` that `setup`
    can address PC-relatively (`lea __snddata(pc),a1`) so it survives the harness relocation.
    Interrupts are masked (full-sync), so the measured cost is the replay's alone.
    """
    parts = ["    move    #$2700,sr      ; interrupts off (full-sync)"]
    if setup.strip():
        parts.append(setup)
    parts += [f"__t{i}:\n    bsr __play" for i in range(ticks)]
    parts.append("__tE:\n    bra.s __tE")
    parts.append("__play:\n" + play_body + "\n    rts")
    if data.strip():
        parts.append("    even\n__snddata:\n" + data)
    body = "\n".join(parts) + "\n"

    labels = [f"__t{i}" for i in range(ticks)] + ["__tE"]
    markers = measure_markers(body, labels, tos=tos, run_vbls=run_vbls, timeout=timeout)
    gc = [markers[lab].global_cycles for lab in labels]
    return PlayEnvelope([gc[i + 1] - gc[i] for i in range(ticks)])
