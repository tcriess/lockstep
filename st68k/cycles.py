"""ST cycle engine: nominal 68000 timing (m68k_table) + an ST wait-state layer.

The wait-state layer is pluggable (WaitStateModel). For P1 it ships FirstOrderRound4 —
the documented `round up to a multiple of 4` approximation, which is exact for the
phase-aligned (4c-multiple) code Aurora's hand counts use, but is NOT the general model
(see DESIGN §1.1: the real rule is a bus-phase accumulator). The interface already passes
a phase through so the bus-phase model can drop in without touching callers, once P0
(TIMING.md, from Hatari source) pins the exact rule and the PSG/MFP/contention numbers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .m68k_table import Confidence, Cost, nominal_cost
from .parser import AsmLine, Mode, classify_operand

# IO-access wait states (P0, verified against Hatari source + oracle, see TIMING.md).
# Keyed by absolute address (24-bit normalised). Returned as (min, max, note).
_ABS_HEX = re.compile(r"\$([0-9a-fA-F]+)")


def io_penalty(line: AsmLine) -> tuple[int, int, str]:
    """Extra cycles for touching a slow peripheral via a *literal absolute* operand.

    PSG/MFP add a flat +4 on the first access; ACIA adds 6 + E-clock sync (0..9). Only
    detectable when the address is an immediate in the instruction — register-indirect IO
    (e.g. `move.b d0,(a0)` with a0=$ff8800) can't be seen statically; the oracle catches
    those. Border/shifter registers ($ff8240/$ff820a/$ff8260) carry NO penalty (verified).
    """
    pmin = pmax = 0
    note = ""
    for op in line.operands:
        if classify_operand(op) not in (Mode.ABSW, Mode.ABSL):
            continue
        m = _ABS_HEX.search(op)
        if not m:
            continue
        a = int(m.group(1), 16) & 0xFFFFFF
        if 0xFF8800 <= a <= 0xFF88FF:
            lo, hi, n = 4, 4, "PSG +4"
        elif 0xFFFA00 <= a <= 0xFFFA3F:
            lo, hi, n = 4, 4, "MFP +4"
        elif 0xFFFC00 <= a <= 0xFFFC07:
            lo, hi, n = 6, 15, "ACIA 6+Eclk"
        else:
            continue
        if hi > pmax:                       # one penalty per instruction (first access)
            pmin, pmax, note = lo, hi, n
    return pmin, pmax, note


def round_up_4(n: int) -> int:
    return (n + 3) & ~3


@dataclass
class Machine:
    name: str
    cpu_hz: int = 8_000_000
    cycles_per_line: int = 512
    lines_per_frame: int = 313        # PAL 50 Hz

    @property
    def cycles_per_frame(self) -> int:
        return self.cycles_per_line * self.lines_per_frame


STF_PAL = Machine("1040 STF / PAL", lines_per_frame=313)    # Aurora's target, default
STF_NTSC = Machine("1040 STF / NTSC", lines_per_frame=263)


class WaitStateModel:
    """Maps nominal 68000 cycles -> effective ST cycles, carrying a bus phase (0/2)."""

    name = "abstract"
    approximate = False

    def apply(self, nmin: int, nmax: int, odd_ea: bool,
              phase: int) -> tuple[int, int, int]:
        raise NotImplementedError


class FirstOrderRound4(WaitStateModel):
    name = "first-order round-to-4 (APPROX, phase-blind)"
    approximate = True

    def apply(self, nmin, nmax, odd_ea, phase):
        return round_up_4(nmin), round_up_4(nmax), 0


class BusPhaseModel(WaitStateModel):
    """Oracle-calibrated bus-phase model (validated against Hatari cycle-exact; see
    TIMING.md). The CPU bus is granted on a 4-cycle grid; an access starting off-grid
    waits to realign. Tracking the running phase (cumulative cycles mod 4, in {0,2}):

      - a normal instruction starting at phase 2 pays +2 to realign;
      - an "odd-EA" instruction (nominal == 2 mod 4 AND it touches data memory — i.e. an
        indexed (d8,An,Xn) or predecrement operand whose internal odd step is the
        misalignment) instead pays +2 at phase 0 and self-aligns at phase 2.

    Exact for straight-line code; for variable-cost ops (branches/shifts) the phase is
    advanced by the max-cost path and flagged.
    """

    name = "bus-phase (oracle-calibrated; DESIGN §1.1, TIMING.md)"
    approximate = False

    def apply(self, nmin, nmax, odd_ea, phase):
        if odd_ea:
            wait = 2 if phase == 0 else 0
        else:
            wait = 2 if phase == 2 else 0
        smin, smax = nmin + wait, nmax + wait
        return smin, smax, (phase + smax) % 4


@dataclass
class StCost:
    nominal: Cost
    st_min: int
    st_max: int
    note: str
    confidence: Confidence
    approximate: bool

    @property
    def fixed(self) -> bool:
        return self.st_min == self.st_max


# branch/jump operands are targets, not data EAs — exclude from the odd-EA check.
_CONTROL_FLOW = {
    "bra", "bsr", "jmp", "jsr",
    "bhi", "bls", "bcc", "bcs", "bne", "beq", "bvc", "bvs",
    "bpl", "bmi", "bge", "blt", "bgt", "ble", "bhs", "blo",
    "dbra", "dbf", "dbt", "dbhi", "dbls", "dbcc", "dbcs", "dbne", "dbeq",
    "dbvc", "dbvs", "dbpl", "dbmi", "dbge", "dblt", "dbgt", "dble",
}


def _has_mem_operand(line: AsmLine) -> bool:
    from .parser import MEMORY_MODES
    return any(classify_operand(o) in MEMORY_MODES for o in line.operands)


def _is_odd_ea(line: AsmLine, nominal: int) -> bool:
    # nominal == 2 mod 4 with a data-memory operand -> indexed/predecrement misalignment
    if line.mnemonic in _CONTROL_FLOW:
        return False
    return nominal % 4 == 2 and _has_mem_operand(line)


class CycleEngine:
    def __init__(self, wait_model: WaitStateModel | None = None,
                 machine: Machine = STF_PAL):
        self.wm = wait_model or BusPhaseModel()
        self.machine = machine

    def cost(self, line: AsmLine, phase: int = 0) -> tuple[StCost, int]:
        """Return (StCost, new_phase) for an instruction line."""
        nc = nominal_cost(line)
        odd_ea = _is_odd_ea(line, nc.min)
        smin, smax, new_phase = self.wm.apply(nc.min, nc.max, odd_ea, phase)
        pmin, pmax, pnote = io_penalty(line)
        smin += pmin
        smax += pmax
        note = nc.note
        conf = nc.confidence
        if pnote:
            note = f"{note}; {pnote}" if note else pnote
            if pmax != pmin:
                conf = Confidence.VARIABLE
        sc = StCost(nc, smin, smax, note, conf, self.wm.approximate)
        return sc, new_phase
