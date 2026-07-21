"""Nominal MC68000 instruction timings (clock periods), independent of the ST.

These are the textbook Motorola figures (M68000 PRM, section 8): base execution + effective
-address calculation + per-register movem terms, assuming the instruction's own 4-clock bus
accesses and no external wait states. The ST-specific wait-state / bus-phase layer lives in
cycles.py and is applied on top of these.

A cost is returned as a Cost(min, max, confidence, note). Fixed instructions have min==max.
Data-/flow-dependent instructions (shifts by Dn, Bcc, DBcc, mul/div) return a range with a
note naming the cases — the ST layer and Hatari resolve which case actually runs.

Unknown mnemonics raise UnknownInstruction rather than returning a guess: a cycle-exact tool
must never be silently wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .parser import AsmLine, Mode, classify_operand, count_reglist


class Confidence(Enum):
    EXACT = "exact"        # well-documented fixed timing
    VARIABLE = "variable"  # data/flow dependent; min..max with a note
    LOW = "low"            # timing believed correct but less battle-tested here
    UNKNOWN = "unknown"


class UnknownInstruction(Exception):
    pass


@dataclass
class Cost:
    min: int
    max: int
    confidence: Confidence
    note: str = ""

    @property
    def fixed(self) -> bool:
        return self.min == self.max


# --- effective-address calculation time (added to base for ALU-style ops) ---------------

_EA_BW = {  # byte/word EA calculation time
    Mode.DREG: 0, Mode.AREG: 0, Mode.AIND: 4, Mode.AINC: 4, Mode.ADEC: 6,
    Mode.ADISP: 8, Mode.AINDEX: 10, Mode.ABSW: 8, Mode.ABSL: 12,
    Mode.PCDISP: 8, Mode.PCINDEX: 10, Mode.IMM: 4,
}
_EA_L = {  # long EA calculation time
    Mode.DREG: 0, Mode.AREG: 0, Mode.AIND: 8, Mode.AINC: 8, Mode.ADEC: 10,
    Mode.ADISP: 12, Mode.AINDEX: 14, Mode.ABSW: 12, Mode.ABSL: 16,
    Mode.PCDISP: 12, Mode.PCINDEX: 14, Mode.IMM: 8,
}


def ea_time(mode: Mode, size: str) -> int:
    return (_EA_L if size == "l" else _EA_BW)[mode]


# --- MOVE timing matrices --------------------------------------------------------------
# rows = source mode, cols = destination mode. Standard MC68000 MOVE.B/.W and MOVE.L tables.

_SRC = [Mode.DREG, Mode.AREG, Mode.AIND, Mode.AINC, Mode.ADEC, Mode.ADISP,
        Mode.AINDEX, Mode.ABSW, Mode.ABSL, Mode.PCDISP, Mode.PCINDEX, Mode.IMM]
_DST = [Mode.DREG, Mode.AREG, Mode.AIND, Mode.AINC, Mode.ADEC, Mode.ADISP,
        Mode.AINDEX, Mode.ABSW, Mode.ABSL]

_MOVE_BW = [
    # Dn  An  (An)(An)+-(An)d(An)d(AX)abW abL
    [4,   4,  8,  8,  8,  12, 14, 12, 16],  # Dn
    [4,   4,  8,  8,  8,  12, 14, 12, 16],  # An
    [8,   8,  12, 12, 12, 16, 18, 16, 20],  # (An)
    [8,   8,  12, 12, 12, 16, 18, 16, 20],  # (An)+
    [10, 10,  14, 14, 14, 18, 20, 18, 22],  # -(An)
    [12, 12,  16, 16, 16, 20, 22, 20, 24],  # d(An)
    [14, 14,  18, 18, 18, 22, 24, 22, 26],  # d(An,Xn)
    [12, 12,  16, 16, 16, 20, 22, 20, 24],  # abs.W
    [16, 16,  20, 20, 20, 24, 26, 24, 28],  # abs.L
    [12, 12,  16, 16, 16, 20, 22, 20, 24],  # d(PC)
    [14, 14,  18, 18, 18, 22, 24, 22, 26],  # d(PC,Xn)
    [8,   8,  12, 12, 12, 16, 18, 16, 20],  # #imm
]
_MOVE_L = [
    [4,   4,  12, 12, 12, 16, 18, 16, 20],  # Dn
    [4,   4,  12, 12, 12, 16, 18, 16, 20],  # An
    [12, 12,  20, 20, 20, 24, 26, 24, 28],  # (An)
    [12, 12,  20, 20, 20, 24, 26, 24, 28],  # (An)+
    [14, 14,  22, 22, 22, 26, 28, 26, 30],  # -(An)
    [16, 16,  24, 24, 24, 28, 30, 28, 32],  # d(An)
    [18, 18,  26, 26, 26, 30, 32, 30, 34],  # d(An,Xn)
    [16, 16,  24, 24, 24, 28, 30, 28, 32],  # abs.W
    [20, 20,  28, 28, 28, 32, 34, 32, 36],  # abs.L
    [16, 16,  24, 24, 24, 28, 30, 28, 32],  # d(PC)
    [18, 18,  26, 26, 26, 30, 32, 30, 34],  # d(PC,Xn)
    [12, 12,  20, 20, 20, 24, 26, 24, 28],  # #imm
]
_SRC_IX = {m: i for i, m in enumerate(_SRC)}
_DST_IX = {m: i for i, m in enumerate(_DST)}


def move_cycles(src: Mode, dst: Mode, size: str) -> int:
    table = _MOVE_L if size == "l" else _MOVE_BW
    try:
        return table[_SRC_IX[src]][_DST_IX[dst]]
    except KeyError:
        raise UnknownInstruction(f"unsupported MOVE operands {src} -> {dst}")


# --- MOVEM base (before +K*n) -----------------------------------------------------------

_MOVEM_M2R = {Mode.AIND: 12, Mode.AINC: 12, Mode.ADISP: 16, Mode.AINDEX: 18,
              Mode.ABSW: 16, Mode.ABSL: 20, Mode.PCDISP: 16, Mode.PCINDEX: 18}
_MOVEM_R2M = {Mode.AIND: 8, Mode.ADEC: 8, Mode.ADISP: 12, Mode.AINDEX: 14,
              Mode.ABSW: 12, Mode.ABSL: 16}

# --- LEA / PEA --------------------------------------------------------------------------

_LEA = {Mode.AIND: 4, Mode.ADISP: 8, Mode.AINDEX: 12, Mode.ABSW: 8, Mode.ABSL: 12,
        Mode.PCDISP: 8, Mode.PCINDEX: 12}
_PEA = {Mode.AIND: 12, Mode.ADISP: 16, Mode.AINDEX: 20, Mode.ABSW: 16, Mode.ABSL: 20,
        Mode.PCDISP: 16, Mode.PCINDEX: 20}
_JMP = {Mode.AIND: 8, Mode.ADISP: 10, Mode.AINDEX: 14, Mode.ABSW: 10, Mode.ABSL: 12,
        Mode.PCDISP: 10, Mode.PCINDEX: 14}
_JSR = {Mode.AIND: 16, Mode.ADISP: 18, Mode.AINDEX: 22, Mode.ABSW: 18, Mode.ABSL: 20,
        Mode.PCDISP: 18, Mode.PCINDEX: 22}


def _fixed(n: int, note: str = "", conf: Confidence = Confidence.EXACT) -> Cost:
    return Cost(n, n, conf, note)


def _modes(line: AsmLine) -> list[Mode]:
    return [classify_operand(o) for o in line.operands]


def nominal_cost(line: AsmLine) -> Cost:
    """Nominal MC68000 cycle cost for an instruction line."""
    if not line.is_instruction:
        raise UnknownInstruction(f"not an instruction: {line.raw!r}")
    m = line.mnemonic
    sz = line.size or "w"
    ms = _modes(line)
    src = ms[0] if ms else None
    dst = ms[1] if len(ms) > 1 else None

    if m == "nop":
        return _fixed(4)
    if m in ("reset",):
        return _fixed(132)
    if m == "rts":
        return _fixed(16)
    if m in ("rte", "rtr"):
        return _fixed(20)
    if m == "swap":
        return _fixed(4)
    if m == "exg":
        return _fixed(6)
    if m == "ext":
        return _fixed(4)
    if m == "unlk":
        return _fixed(12)
    if m == "link":
        return _fixed(16)
    if m == "moveq":
        return _fixed(4)

    if m in ("move", "movea"):
        return _move_family(src, dst, sz)
    if m == "movep":
        return _fixed(24 if sz == "l" else 16, "MOVEP", Confidence.LOW)

    if m == "lea":
        return _fixed(_lookup(_LEA, src, "LEA"))
    if m == "pea":
        return _fixed(_lookup(_PEA, src, "PEA"))
    if m == "jmp":
        return _fixed(_lookup(_JMP, src, "JMP"))
    if m == "jsr":
        return _fixed(_lookup(_JSR, src, "JSR"))

    if m == "movem":
        return _movem(line, sz)

    if m in ("add", "sub"):
        return _add_sub(m, src, dst, sz, line)
    if m in ("adda", "suba"):
        return _adda_suba(src, sz)
    if m in ("addq", "subq"):
        return _addq_subq(src, dst, sz)
    if m in ("addi", "subi"):
        return _imm_alu(dst, sz, to_dn_bw=8, to_dn_l=16, to_mem_bw=12, to_mem_l=20)
    if m in ("and", "or"):
        return _and_or(src, dst, sz)
    if m == "eor":
        return _eor(src, dst, sz)
    if m in ("andi", "ori", "eori"):
        return _imm_logic(m, dst, sz)
    if m == "cmp":
        return _cmp(src, dst, sz)
    if m == "cmpa":
        ea = ea_time(src, sz)
        base = 6 if sz == "l" else 6
        return _fixed(base + ea)
    if m == "cmpi":
        return _imm_alu(dst, sz, to_dn_bw=8, to_dn_l=14, to_mem_bw=8, to_mem_l=12)
    if m == "tst":
        return _tst(src, sz)
    if m in ("clr", "neg", "negx", "not"):
        return _unary_rmw(src, sz)
    if m == "nbcd":
        if src == Mode.DREG:
            return _fixed(6)
        return _fixed(8 + ea_time(src, "b"), conf=Confidence.LOW)
    if m == "tas":
        if src == Mode.DREG:
            return _fixed(4)
        return _fixed(14 + ea_time(src, "b"), conf=Confidence.LOW)

    if m in ("asl", "asr", "lsl", "lsr", "rol", "ror", "roxl", "roxr"):
        return _shift(src, dst, sz, line)

    if m in ("btst", "bchg", "bclr", "bset"):
        return _bitop(m, src, dst)

    if m in ("bra", "bsr") or _is_bcc(m):
        return _branch(m, sz)
    if _is_dbcc(m):
        # Same prefetch-refill realignment as _branch: looping (taken) 10c -> 12c, counter-expired
        # (falls through, but still refills) 14c -> 16c. This is what makes the classic
        # `nop / dbra` pause loop cost exactly 16c an iteration.
        return Cost(12, 16, Confidence.VARIABLE,
                    "DBcc: 12 looping / 16 counter-expired")

    if m in ("mulu", "muls"):
        return Cost(38, 70, Confidence.VARIABLE, f"{m.upper()} 38..70, data-dependent")
    if m == "divu":
        return Cost(76, 140, Confidence.VARIABLE, "DIVU ~76..140, data-dependent")
    if m == "divs":
        return Cost(84, 158, Confidence.VARIABLE, "DIVS ~84..158, data-dependent")

    if m in ("trap", "trapv", "illegal", "stop", "chk"):
        # present in init code, not in cycle-counted sync regions
        return Cost(0, 0, Confidence.UNKNOWN, f"{m}: timing not modelled (not sync-path)")

    raise UnknownInstruction(f"no timing for {m!r} (line: {line.raw.strip()!r})")


# --- helpers ----------------------------------------------------------------------------

def _lookup(table, mode, what) -> int:
    if mode not in table:
        raise UnknownInstruction(f"unsupported {what} operand mode {mode}")
    return table[mode]


def _move_family(src, dst, sz) -> Cost:
    if src in (Mode.SR, Mode.CCR):  # MOVE from SR/CCR
        if dst == Mode.DREG:
            return _fixed(6)
        return _fixed(8 + ea_time(dst, "w"), "MOVE from SR/CCR to memory")
    if dst in (Mode.SR, Mode.CCR):  # MOVE to SR/CCR
        return _fixed(12 + ea_time(src, "w"), "MOVE to SR/CCR")
    if src == Mode.USP or dst == Mode.USP:
        return _fixed(4, "MOVE USP")
    if src is None or dst is None:
        raise UnknownInstruction("MOVE needs two operands")
    return _fixed(move_cycles(src, dst, sz))


def _movem(line: AsmLine, sz) -> Cost:
    # direction inferred from which operand is the register list
    ms = _modes(line)
    if ms and ms[0] == Mode.REGLIST:           # reg -> mem
        n = count_reglist(line.operands[0])
        mode = ms[1]
        base = _lookup(_MOVEM_R2M, mode, "MOVEM (R->M)")
        per = 8 if sz == "l" else 4
        return _fixed(base + per * n, f"MOVEM R->M, {n} regs")
    elif len(ms) > 1 and ms[1] == Mode.REGLIST:  # mem -> reg
        n = count_reglist(line.operands[1])
        mode = ms[0]
        base = _lookup(_MOVEM_M2R, mode, "MOVEM (M->R)")
        per = 8 if sz == "l" else 4
        return _fixed(base + per * n, f"MOVEM M->R, {n} regs")
    raise UnknownInstruction(f"cannot read MOVEM operands: {line.raw.strip()!r}")


def _add_sub(m, src, dst, sz, line) -> Cost:
    if src == Mode.IMM:
        return _imm_alu(dst, sz, to_dn_bw=8, to_dn_l=16, to_mem_bw=12, to_mem_l=20)
    if dst == Mode.AREG:
        return _adda_suba(src, sz)
    if dst == Mode.DREG:                         # <ea>,Dn
        return _alu_to_dn(src, sz)
    return _alu_to_mem(dst, sz)                   # Dn,<ea>


def _and_or(src, dst, sz) -> Cost:
    if src == Mode.IMM:
        return _imm_logic("andi", dst, sz)
    if dst == Mode.DREG:
        return _alu_to_dn(src, sz)
    return _alu_to_mem(dst, sz)


def _eor(src, dst, sz) -> Cost:
    if src == Mode.IMM:
        return _imm_logic("eori", dst, sz)
    if dst == Mode.DREG:                          # EOR Dn,Dn
        return _fixed(8 if sz == "l" else 4)
    return _alu_to_mem(dst, sz)                    # EOR Dn,<mem>


def _cmp(src, dst, sz) -> Cost:
    if dst == Mode.AREG:
        ea = ea_time(src, sz)
        return _fixed(6 + ea)
    return _alu_to_dn(src, sz, is_cmp=True)        # CMP <ea>,Dn


def _alu_to_dn(src, sz, is_cmp=False) -> Cost:
    ea = ea_time(src, sz)
    if sz == "l":
        base = 6
        if src in (Mode.DREG, Mode.AREG, Mode.IMM):
            base += 2                              # long, register/immediate source: +2
        return _fixed(base + ea)
    return _fixed(4 + ea)


def _alu_to_mem(dst, sz) -> Cost:
    ea = ea_time(dst, sz)
    return _fixed((12 if sz == "l" else 8) + ea)


def _adda_suba(src, sz) -> Cost:
    ea = ea_time(src, sz)
    if sz == "l":
        base = 6
        if src in (Mode.DREG, Mode.AREG, Mode.IMM):
            base += 2
        return _fixed(base + ea)
    return _fixed(8 + ea)                          # ADDA.W <ea>,An = 8 + EA


def _addq_subq(src, dst, sz) -> Cost:
    if dst == Mode.AREG:
        return _fixed(8)                           # ADDQ/SUBQ #,An always 8
    if dst == Mode.DREG:
        return _fixed(8 if sz == "l" else 4)
    return _fixed((12 if sz == "l" else 8) + ea_time(dst, sz))


def _imm_alu(dst, sz, to_dn_bw, to_dn_l, to_mem_bw, to_mem_l) -> Cost:
    if dst in (Mode.DREG, Mode.AREG):
        return _fixed(to_dn_l if sz == "l" else to_dn_bw)
    return _fixed((to_mem_l if sz == "l" else to_mem_bw) + ea_time(dst, sz))


def _imm_logic(m, dst, sz) -> Cost:
    if dst == Mode.SR:
        return _fixed(16, f"{m.upper()} #,SR")
    if dst == Mode.CCR:
        return _fixed(20, f"{m.upper()} #,CCR")
    return _imm_alu(dst, sz, to_dn_bw=8, to_dn_l=16, to_mem_bw=12, to_mem_l=20)


def _tst(src, sz) -> Cost:
    if src in (Mode.DREG, Mode.AREG):
        return _fixed(4)
    return _fixed(4 + ea_time(src, sz))


def _unary_rmw(src, sz) -> Cost:
    if src in (Mode.DREG, Mode.AREG):
        return _fixed(6 if sz == "l" else 4)
    return _fixed((12 if sz == "l" else 8) + ea_time(src, sz), conf=Confidence.LOW)


def _shift(src, dst, sz, line=None) -> Cost:
    # memory shift (by 1): single operand
    if dst is None:
        return _fixed(8 + ea_time(src, sz), "memory shift by 1", Confidence.LOW)
    if src == Mode.IMM:
        base = 6 if sz != "l" else 8
        # the count is right there in the immediate: resolve it (1..8; #0 encodes 8)
        if line is not None and line.operands:
            tok = line.operands[0].lstrip("#")
            try:
                n = int(tok[1:], 16) if tok.startswith("$") else int(tok, 0)
            except ValueError:
                n = None
            if n is not None and not 1 <= n <= 8:
                n = None            # 1..8 is the hardware range (#8 encodes as 0)
            if n is not None:
                return _fixed(base + 2 * n, f"shift #{n},Dn = {base}+2*{n}")
        return Cost(base + 2, base + 16, Confidence.VARIABLE,
                    f"shift #n,Dn = {base}+2n (immediate unresolved)")
    base = 6 if sz != "l" else 8
    return Cost(base, base + 2 * 63, Confidence.VARIABLE,
                f"shift Dn,Dn = {base}+2n, n=(count & 63)")


def _bitop(m, src, dst) -> Cost:
    to_dn = dst == Mode.DREG
    static = src == Mode.IMM
    if m == "btst":
        if static:
            return _fixed(10) if to_dn else _fixed(8 + ea_time(dst, "b"))
        return _fixed(6) if to_dn else _fixed(4 + ea_time(dst, "b"))
    # bchg/bclr/bset (read-modify-write)
    if static:
        if to_dn:
            return _fixed(14 if m == "bclr" else 12)
        return _fixed(12 + ea_time(dst, "b"))
    if to_dn:
        return _fixed(8)
    return _fixed(8 + ea_time(dst, "b"))


def _is_bcc(m: str) -> bool:
    return m in {
        "bhi", "bls", "bcc", "bcs", "bne", "beq", "bvc", "bvs",
        "bpl", "bmi", "bge", "blt", "bgt", "ble", "bhs", "blo",
    }


def _is_dbcc(m: str) -> bool:
    return m in {
        "dbra", "dbf", "dbt", "dbhi", "dbls", "dbcc", "dbcs", "dbne", "dbeq",
        "dbvc", "dbvs", "dbpl", "dbmi", "dbge", "dblt", "dbgt", "dble",
    }


def _branch(m: str, sz) -> Cost:
    """A TAKEN branch refills the prefetch queue, and that refill realigns the CPU to the 4-cycle
    bus: the 68000's raw 10c (BRA/Bcc) and 18c (BSR) land as 12c and 20c, and the next instruction
    starts on a fresh bus slot. The 2c never come back — unlike the sub-4 remainder an ordinary
    instruction leaves behind (see the phase model in cycles.py), which the *next* instruction does
    absorb. A NOT-taken Bcc does no refill and keeps its raw cost (8c short / 12c word, both already
    bus-aligned), which is why a Bcc.s is asymmetric by a full 4c and Bcc.w is not asymmetric at all.

    These are measured, not derived — see `test_branch_costs_match_hatari`. Getting them wrong is
    not academic: `@balance` sizes each arm's filler from exactly these numbers, and 4c is enough to
    push Aurora's 60/50 Hz top-border pulse off its scanline."""
    short = sz in ("s", "b") or sz is None
    if m == "bra":
        return _fixed(12)
    if m == "bsr":
        return _fixed(20)
    # Bcc
    if short:
        return Cost(8, 12, Confidence.VARIABLE, "Bcc.s: 12 taken / 8 not taken")
    return Cost(12, 12, Confidence.VARIABLE, "Bcc.w: 12 taken / 12 not taken")
