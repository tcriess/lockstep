"""P2b tests: @balance branch-arm equalization (DESIGN §2.2)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from st68k.preprocess import PreprocessError, expand    # noqa: E402

# The arms are costed with the TAKEN branch at 12c and the not-taken one at 8c (a taken branch
# refills the prefetch queue, which realigns the CPU to the 4-cycle bus — see m68k_table._branch).
# So an empty fall-through arm is 8 + bra.s(12) = 20c, and one 8c register op on the target arm
# balances it exactly.
NO_FILL = """\
;@balance
    bge.s .alt
    bra.s .end
;@balance alt
.alt:
    add.l d1,d2
;@balance end
.end:
"""

WITH_FILL = """\
;@balance
    bge.s .alt
;@fill
    bra.s .end
;@balance alt
.alt:
    add.l d1,d2
    add.l d1,d2
;@balance end
.end:
"""

# The target arm ends 2c short of the fall-through one, and `exg` (6c) has left the bus at phase 2,
# where nop filler can only add 6+4k. 2c is unreachable — a 4c nop cannot bridge a 2c residue, and
# there is nothing smaller. Reaching this case at all needs an odd-cost instruction: taken branches
# realign to the bus, so any arm ending in one lands back on a 4c boundary.
RESIDUE = """\
;@balance
    bge.s .alt
    bra.s .end
;@balance alt
.alt:
    exg d4,d5
;@fill
;@balance end
.end:
"""

MISMATCH = """\
;@balance
    bge.s .alt
    move.l (a0),d0
    bra.s .end
;@balance alt
.alt:
    move.w (a0),d1
;@balance end
.end:
"""


def test_balance_no_fill_equal_arms():
    out, rep = expand(NO_FILL)
    assert "dcb.w" not in out                     # arms already equal, no filler
    assert rep[-1].kind == "balance"
    assert "20c / taken 20c -> 20c" in rep[-1].detail


def test_balance_emits_fill_to_equalize():
    out, rep = expand(WITH_FILL)
    assert "dcb.w 2,$4e71" in out                 # +8c pads the fall-through arm
    assert "-> 28c" in rep[-1].detail


def test_balance_two_cycle_residue_errors():
    try:
        expand(RESIDUE)
        assert False, "expected a 2c-residue PreprocessError"
    except PreprocessError as e:
        assert "odd-residue" in str(e) or "multiple of 4" in str(e)


def test_balance_mismatch_without_fill_errors():
    try:
        expand(MISMATCH)
        assert False, "expected arms-differ PreprocessError"
    except PreprocessError as e:
        assert "differ" in str(e)


def test_balance_requires_conditional_branch():
    src = ";@balance\n    nop\n;@balance alt\n;@balance end\n"
    try:
        expand(src)
        assert False, "expected 'must be followed by a conditional branch'"
    except PreprocessError as e:
        assert "conditional branch" in str(e)


def test_unterminated_balance_errors():
    try:
        expand(";@balance\n    bge.s .x\n")
        assert False, "expected unterminated @balance"
    except PreprocessError as e:
        assert "unterminated @balance" in str(e)


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed")


if __name__ == "__main__":
    _run()
