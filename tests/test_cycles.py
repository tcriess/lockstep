"""P1 acceptance tests: reproduce the DESIGN §1.1 table and the Aurora 512c border line.

Runnable with pytest, or directly: `python tests/test_cycles.py`.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from st68k.annotate import block_cycles                       # noqa: E402
from st68k.cycles import CycleEngine                          # noqa: E402
from st68k.parser import Mode, classify_operand, parse_line   # noqa: E402

ENG = CycleEngine()


def st(src: str) -> tuple[int, int]:
    sc, _ = ENG.cost(parse_line(src))
    return sc.st_min, sc.st_max


# --- DESIGN §1.1 validation table (against Aurora's own hand counts) --------------------

def test_table_fixed():
    cases = {
        "    nop": 4,
        "    movem.l (a5)+,d0-d3": 44,
        "    movem.l d0-d3,(a6)": 40,
        "    movea.l 0(a0,d0.w),a0": 20,        # 18 nominal -> 20 ST  (the '20 c?' line)
        "    lea 230(a6),a6": 8,
        "    move.l (a3)+,d4": 12,
        "    move.b d3,(a1)": 8,
        "    move.b d4,(a0)": 8,
        "    and.l d4,d0": 8,
        "    or.l d4,d0": 8,
        "    tst.l d4": 4,
        "    subq #1,d2": 4,
        "    moveq #16,d1": 4,
        "    add.w d3,a4": 8,                    # ADDA.W Dn,An
        "    movem.l d0-d7/a0-a6,-(sp)": 128,    # 8 + 8*15
        "    movem.l (sp)+,d0-d7/a0-a6": 132,    # 12 + 8*15
    }
    for src, want in cases.items():
        lo, hi = st(src)
        assert lo == hi == want, f"{src!r}: got {lo}..{hi}, want {want}"


def test_table_variable():
    # A TAKEN branch refills the prefetch queue, and that refill realigns the CPU to the 4-cycle
    # bus — so the 68000's raw 10c lands as 12c and the 2c never come back. Only the NOT-taken Bcc
    # keeps its raw 8c. All four numbers are measured against Hatari in
    # test_hatari.test_branch_costs_match_hatari; do not "correct" them back to the 68000 manual.
    assert st("    dbra d0,pause") == (12, 16)     # 12 looping / 16 expiring
    assert st("    bge.s .ok") == (8, 12)          # 8 not-taken / 12 taken
    assert st("    beq.s .wait") == (8, 12)
    assert st("    bra.s .x") == (12, 12)
    assert st("    bsr.s sub") == (20, 20)


def test_bus_phase_model():
    # oracle-validated sequences (see TIMING.md). block_cycles threads the bus phase.
    cases = {
        "    exg d0,d1": 6,                                          # phase 0
        "    exg d0,d1\n    exg d2,d3": 14,                          # 6 + 8 (realign)
        "    exg d0,d1\n    exg d2,d3\n    exg d4,d5\n    exg d6,d7": 30,
        "    exg d0,d1\n    nop": 12,                                # nop realigns at phase 2
        "    nop\n    exg d0,d1": 10,
        "    exg d0,d1\n    movea.l 0(a0,d0.w),a5": 24,              # odd-EA self-aligns
        "    nop\n    nop\n    nop\n    nop": 16,                    # clean 4c, no phase effect
    }
    for src, want in cases.items():
        lo, hi = block_cycles(src)
        assert lo == hi == want, f"{src!r}: got {lo}..{hi}, want {want}"


def test_round4_model_still_available():
    from st68k.cycles import CycleEngine, FirstOrderRound4
    r4 = CycleEngine(wait_model=FirstOrderRound4())
    sc, _ = r4.cost(parse_line("    exg d0,d1"))
    assert sc.st_min == 8          # round-to-4 over-counts exg (real is 6)


# --- the Aurora 512c border scanline ----------------------------------------------------

AURORA_BORDER_BODY = """\
    move.b  d3,(a1)
    move.b  d4,(a1)
    dcb.w   90,$4e71
    move.b  d4,(a0)
    move.b  d3,(a0)
    dcb.w   13,$4e71
    move.b  d3,(a1)
    nop
    move.b  d4,(a1)
    dcb.w   12,$4e71
"""


def test_io_access_penalties():
    # P0: PSG/MFP add +4 (verified vs oracle); shifter/palette regs add nothing.
    assert st("    move.b d0,$ffff8800.w") == (16, 16)   # PSG: 12 + 4
    assert st("    move.b d0,$fffffa01.w") == (16, 16)   # MFP: 12 + 4
    assert st("    move.w d0,$ffff8240.w") == (12, 12)   # palette: no penalty
    assert st("    move.b d3,(a1)") == (8, 8)            # register-indirect: not seen (ok)
    lo, hi = st("    move.b d0,$fffc00.w")               # ACIA: 6 + E-clock (variable)
    assert lo == 12 + 6 and hi == 12 + 15


def test_aurora_border_line_is_512():
    lo, hi = block_cycles(AURORA_BORDER_BODY)
    assert lo == hi == 512, f"border line should be 512c, got {lo}..{hi}"


def test_rept_multiplies():
    text = "    rept 227\n" + AURORA_BORDER_BODY + "    endr\n"
    lo, hi = block_cycles(text)
    assert lo == hi == 512 * 227


# --- parser sanity (label vs instruction disambiguation) --------------------------------

def test_parser_labels():
    assert parse_line("my_70:").label == "my_70"
    eq = parse_line("linesdeb   equ     227")
    assert eq.label == "linesdeb" and eq.mnemonic == "equ"
    instr = parse_line("    move.b  d3,(a1)")
    assert instr.label is None and instr.mnemonic == "move" and instr.size == "b"
    lab_instr = parse_line("clsloop:    move.l  d1,(a0)+")
    assert lab_instr.label == "clsloop" and lab_instr.mnemonic == "move"


def test_classify_operand():
    assert classify_operand("d3") == Mode.DREG
    assert classify_operand("(a1)") == Mode.AIND
    assert classify_operand("(a5)+") == Mode.AINC
    assert classify_operand("-(sp)") == Mode.ADEC
    assert classify_operand("230(a6)") == Mode.ADISP
    assert classify_operand("0(a0,d0.w)") == Mode.AINDEX
    assert classify_operand("$ffff820a.w") == Mode.ABSW
    assert classify_operand("$120") == Mode.ABSL
    assert classify_operand("#$700") == Mode.IMM
    assert classify_operand("d0-d7/a0-a6") == Mode.REGLIST


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed")


if __name__ == "__main__":
    _run()
