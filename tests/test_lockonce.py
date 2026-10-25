"""Tests for lockstep.lockonce (sync once, then count).

Static: the loop from __band0 back to __band0 costs exactly one PAL frame, the tail budget is what
is left, and a tail that does not fit fails the build. Hatari-marked: the built example keeps
__band0 on the same frame cycle every frame, and opens all four borders on all four wakestates.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lockstep.lockonce import DANCE_TO_BAND0, FRAME_CYCLES, LockOnceFrame  # noqa: E402
from st68k.annotate import block_cycles                                   # noqa: E402

STD = dict(main_lines=227, bot_lines=32, left_nops=1, cross=True)


def _loop(body: str) -> str:
    """The text from __band0 to the loop's jump (inclusive)."""
    a = body.index("__band0:")
    m = re.compile(r"^\s*jmp\s+\(a2\)\s*$|^\s*jmp\s+__band0\s*$", re.M).search(body, a)
    return body[a:m.end()]


def _strip_pragmas(asm: str) -> str:
    return "\n".join(l for l in asm.splitlines() if not l.strip().startswith(";@"))


@pytest.mark.parametrize("exit_on_key,check", [(True, False), (False, False), (True, True),
                                                (False, True)])
def test_loop_is_one_frame(exit_on_key, check):
    f = LockOnceFrame(exit_on_key=exit_on_key, check=check, check_base="__lo_err" if check else None,
                      **STD)
    tail = "    addq.l  #1,$1000.w\n"
    loop = _loop(f.frame_body(tail=tail))
    assert block_cycles(_strip_pragmas(loop))[1] == FRAME_CYCLES


def test_tail_budget():
    f = LockOnceFrame(**STD)
    assert f.tail_budget() == FRAME_CYCLES - 260 * 512 - DANCE_TO_BAND0 == 26564


def test_tail_overrun_refused():
    f = LockOnceFrame(**STD)
    with pytest.raises(ValueError, match="does not fit"):
        f.frame_body(tail=f"    dcb.w   {f.tail_budget() // 4 + 1},$4e71\n")


def test_no_pre():
    with pytest.raises(ValueError):
        LockOnceFrame(pre="    nop\n", **STD)


@pytest.mark.hatari
def test_lockonce_example_certified(tmp_path):
    from lockstep.wakestate import verify_overscan
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    "examples", "lockonce"))
    import lockonce
    tos = lockonce.build(str(tmp_path / "LOCKONCE.TOS"))
    report = verify_overscan(tos, wakestates=(1, 2, 3, 4), frames=range(320, 323),
                             count_addr=lockonce.COUNTER)
    assert report.ok, report.matrix()
