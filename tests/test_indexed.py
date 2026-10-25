"""Indexed addressing in the cycle model, pinned to Hatari measurements.

Indexed operands without a displacement, (an,xn), and PC-indexed operands used to parse as abs.L;
indexed LEA/PEA missed their realignment at bus phase 0. The lock-once loop exposed both: one
frame came out 8c long. Each cost below was measured in Hatari (cycle-exact): the instruction
followed by a nop, at bus phase 0 and (after an exg) at phase 2.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.parametrize("op,mode", [
    ("(a3,d0.w)", "AINDEX"), ("(a3,d0.l)", "AINDEX"), ("0(a3,d0.w)", "AINDEX"),
    ("(4,a3,d0.w)", "AINDEX"), ("lbl(pc,d0.w)", "PCINDEX"), ("(4,pc,d0.w)", "PCINDEX"),
    ("lbl(pc)", "PCDISP"), ("$ffff8240", "ABSL"),
])
def test_indexed_operands_classify(op, mode):
    from st68k.parser import Mode, classify_operand
    assert classify_operand(op) == getattr(Mode, mode)


@pytest.mark.parametrize("ins,at0,at2", [
    ("lea     0(a3,d0.w),a3", 20, 18), ("lea     (a3,d0.l),a3", 20, 18),
    ("lea     lbl(pc,d0.w),a3", 20, 18), ("pea     (a3,d0.w)", 28, 26),
    ("move.l  (a3,d0.w),d1", 24, 22), ("move.w  (a3,d0.w),$ffff825e", 32, 30),
    ("move.w  lbl(pc,d0.w),d1", 20, 18), ("move.b  d1,(a3,d0.w)", 20, 18),
])
def test_indexed_costs_match_hatari(ins, at0, at2):
    from st68k.annotate import block_cycles
    exg = block_cycles("    exg     d1,d2\n")[1]
    assert block_cycles(f"    {ins}\n    nop\n")[1] == at0
    assert block_cycles(f"    exg     d1,d2\n    {ins}\n    nop\n")[1] - exg == at2
