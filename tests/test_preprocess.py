"""P2 tests: @pad / @fill / @budget / @at / @sync expansion."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from st68k.annotate import block_cycles                       # noqa: E402
from st68k.preprocess import PreprocessError, expand          # noqa: E402


def test_pad_emits_exact_filler():
    src = """\
;@sync
    move.b d3,(a1)
;@pad 16
"""
    out, _ = expand(src)
    assert "dcb.w 2,$4e71" in out          # 16 - 8 = 8c = 2 nops
    # the region up to the pad is exactly 16c
    assert block_cycles(out) == (16, 16)


def test_budget_fill_border_line_512():
    # the DESIGN §2.1 worked example: a 512c scanline built from intent
    src = """\
;@budget 512
    move.b  d3,(a1)
    move.b  d4,(a1)
;@pad 376
    move.b  d4,(a0)
    move.b  d3,(a0)
;@pad 440
    move.b  d3,(a1)
    nop
    move.b  d4,(a1)
;@fill
;@end
"""
    out, report = expand(src)
    assert block_cycles(out) == (512, 512)
    # the @fill absorbed the remainder
    assert any(r.kind == "budget" and "512" in r.detail for r in report)


def test_at_pass_and_fail():
    ok = ";@sync\n    nop\n    nop\n;@at 8\n"
    expand(ok)                              # should not raise
    bad = ";@sync\n    nop\n;@at 8\n"        # nop = 4, asserting 8
    try:
        expand(bad)
        assert False, "expected PreprocessError"
    except PreprocessError as e:
        assert "@at 8" in str(e)


def test_overflow_is_an_error():
    # code already costs 12c, asking to pad to 8 -> over budget
    src = ";@sync\n    move.l (a3),d4\n;@pad 8\n"
    try:
        expand(src)
        assert False, "expected overflow error"
    except PreprocessError as e:
        assert "OVER" in str(e)


def test_non_multiple_of_4_is_an_error():
    src = ";@sync\n    nop\n;@pad 6\n"        # gap = 2, not fillable with 4c nops
    try:
        expand(src)
        assert False, "expected non-mult-4 error"
    except PreprocessError as e:
        assert "multiple of 4" in str(e)


def test_variable_cost_in_region_is_rejected():
    src = ";@sync\n    bge.s .x\n;@pad 16\n"   # bge.s is 8..12c, ambiguous
    try:
        expand(src)
        assert False, "expected ambiguity error"
    except PreprocessError as e:
        assert "variable-cost" in str(e)


def test_still_assembles_shape():
    # directives are comments; the expanded output is pure asm (no stray @)
    src = ";@budget 8\n    move.b d3,(a1)\n;@fill\n;@end\n"
    out, _ = expand(src)
    for line in out.splitlines():
        body = line.split(";", 1)[0]
        assert "@" not in body


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed")


if __name__ == "__main__":
    _run()
