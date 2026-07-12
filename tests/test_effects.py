"""Tests for lockstep.effects (active-zone write lint + effect recipes).

The lint must flag absolute screen/RAM writes in active-zone code (they tear — DESIGN §1.5) while
ALLOWING the required absolute writes to the hardware registers (border switches, palette). The
recipes must generate active-zone-clean (register-indirect) code that the lint passes.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest                                                           # noqa: E402
from lockstep.effects import (active_zone_lint, assert_active_zone_clean,   # noqa: E402
                              band_writer, palette_split)


def test_absolute_screen_write_is_flagged():
    findings = active_zone_lint("    move.w  d0,$a8000")
    assert len(findings) == 1
    assert "$a8000" in findings[0].operand
    assert "tears" in findings[0].reason


def test_register_indirect_write_is_clean():
    assert active_zone_lint("    move.w  (a4)+,(a3)") == []
    assert active_zone_lint("    move.w  d0,(a3)") == []
    assert active_zone_lint("    move.w  d0,4(a3)") == []


def test_hardware_register_writes_allowed():
    # the border switches and palette are written absolute BY DESIGN — never flagged
    hw = ("    move.b  d3,$ffff8260\n"     # left-border resolution reg
          "    move.b  #2,$ffff820a\n"     # right-border sync reg
          "    move.w  d0,$ffff8240\n"     # palette entry 0
          "    clr.b   $ffff8260")
    assert active_zone_lint(hw) == []


def test_absolute_label_write_is_suspect():
    findings = active_zone_lint("    move.w  d0,__scrbuf")
    assert len(findings) == 1
    assert "__scrbuf" in findings[0].operand


def test_read_only_dest_not_flagged():
    # cmp/tst READ their (absolute) operand — not a tearing write
    assert active_zone_lint("    cmp.w   d0,$a8000") == []
    assert active_zone_lint("    tst.w   $a8000") == []


def test_rmw_absolute_write_flagged():
    # a read-modify-write to an absolute screen address still writes it -> tears
    findings = active_zone_lint("    eor.w   d0,$a8000")
    assert len(findings) == 1


def test_clr_absolute_screen_flagged_but_io_ok():
    assert len(active_zone_lint("    clr.w   $a8000")) == 1        # screen -> flagged
    assert active_zone_lint("    clr.b   $ffff8260") == []         # IO reg -> allowed


def test_assert_guard_raises_on_tear():
    with pytest.raises(AssertionError):
        assert_active_zone_clean("    move.w  d0,$a8000")
    assert_active_zone_clean("    move.w  (a4)+,(a3)")             # clean -> no raise


def test_band_writer_is_lint_clean():
    asm = band_writer(11, src="a4", dst="a2")
    assert asm.count("move.w (a4)+,(a2)+") == 11
    assert active_zone_lint(asm) == []                            # register-indirect -> clean


def test_band_writer_with_row_advance():
    asm = band_writer(4, advance_dst="    lea 230(a2),a2")
    assert "lea 230(a2),a2" in asm
    assert active_zone_lint(asm) == []


def test_palette_split_writes_io_and_is_clean():
    asm = palette_split(["d0", "d1", "d2"], first=0)
    # consecutive palette entries from $ffff8240, 2 bytes apart
    assert "move.w  d0,$ffff8240" in asm
    assert "move.w  d1,$ffff8242" in asm
    assert "move.w  d2,$ffff8244" in asm
    assert active_zone_lint(asm) == []                            # palette = IO reg -> allowed


if __name__ == "__main__":
    print(band_writer(4))
    print(palette_split(["d0", "d1"]))
    for f in active_zone_lint("    move.w d0,$a8000\n    move.w (a4)+,(a3)"):
        print(f)
