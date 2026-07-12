"""Lockstep — active-zone write lint + effect recipes.

Two things that were tribal knowledge, made first-class:

1. **The active-zone absolute-write lint.** During the active display the CPU and the video
   shifter share the bus; a screen write via ABSOLUTE addressing (`move.w d0,$a8000`) holds the
   bus differently from a register-indirect one (`move.w d0,(a3)`) of the same cycle cost and it
   TEARS (DESIGN §1.5, Hatari-proven). This was a note in tecer's head; `active_zone_lint` enforces
   it — flagging absolute-addressed writes to display/RAM inside active-zone work, while allowing
   the required absolute writes to the hardware registers ($ff8xxx / $ffff8xxx: the border/shifter
   switches and the palette).

2. **Effect recipes** that were re-derived per demo, generalized to lint-clean generators: a
   register-indirect beam-raced band writer (the see-through scroller idiom) and a per-scanline
   palette-split write (Aurora's late-line 16-colour trick — preload the colours to registers, then
   write the shifter in the free window around the pegs). These are recipes that pass W2, not new
   mechanisms; pair them with `beamrace.BandGeometry` (W4) for the band, and the budget model (W3).
"""

from __future__ import annotations

from dataclasses import dataclass

from st68k.parser import Mode, classify_operand, parse_line

_ABS_MODES = {Mode.ABSW, Mode.ABSL}

# Instructions whose destination operand is READ, not written — an absolute there is not a
# tearing write (cmp/tst/btst read; branches/jumps/pea/lea don't write memory dests).
_READ_ONLY_DEST = {
    "cmp", "cmpa", "cmpi", "cmpm", "tst", "btst", "jmp", "jsr", "pea", "lea", "movea",
    "bra", "bsr", "bhi", "bls", "bcc", "bcs", "bne", "beq", "bvc", "bvs", "bpl", "bmi",
    "bge", "blt", "bgt", "ble", "bhs", "blo", "dbra", "dbf",
}


def _abs_value(operand: str) -> int | None:
    """The numeric address of an absolute operand, or None if it is a label/expression. Strips a
    `.w`/`.l` size suffix; accepts `$hex` or decimal."""
    op = operand.strip()
    for suf in (".w", ".l", ".W", ".L"):
        if op.endswith(suf):
            op = op[:-2]
            break
    op = op.strip()
    try:
        return int(op[1:], 16) if op.startswith("$") else int(op)
    except ValueError:
        return None


def _is_io_register(operand: str) -> bool:
    """True if an absolute operand targets the ST IO/hardware register area ($ff8000-$ffffff or
    its $ffffxxxx image) — the border/shifter/palette registers, which MUST be written absolute."""
    v = _abs_value(operand)
    return v is not None and (v & 0xFFFFFF) >= 0xFF8000


@dataclass(frozen=True)
class LintFinding:
    lineno: int
    text: str
    operand: str
    reason: str

    def __str__(self) -> str:
        return f"line {self.lineno}: {self.text.strip()}  -> {self.reason}"


def active_zone_lint(asm: str) -> list[LintFinding]:
    """Flag absolute-addressed WRITES to display/RAM inside active-zone code — the tearing pattern
    (DESIGN §1.5). Writes to the hardware registers ($ff8xxx/$ffff8xxx) are allowed (the border
    switches and palette). A numeric non-IO address is a definite screen tear; a label/expression
    destination is flagged as suspect (it may be a screen buffer written absolute — use
    register-indirect, or move it out of the active zone)."""
    findings: list[LintFinding] = []
    for i, raw in enumerate(asm.splitlines(), 1):
        line = parse_line(raw)
        if not line.is_instruction or not line.operands:
            continue
        if line.mnemonic in _READ_ONLY_DEST:
            continue
        dest = line.operands[-1]
        if classify_operand(dest) not in _ABS_MODES:
            continue
        if _is_io_register(dest):
            continue
        if _abs_value(dest) is not None:
            reason = (f"absolute screen/RAM write to {dest} in the active zone — tears (the CPU "
                      f"steals the shifter's bus slot). Use register-indirect: point an An at it "
                      f"and write `(An)` / `(An)+`.")
        else:
            reason = (f"absolute write to {dest!r} in the active zone — if this is a screen buffer "
                      f"it tears; write it register-indirect, or move it to the VBL tail.")
        findings.append(LintFinding(i, raw, dest, reason))
    return findings


def assert_active_zone_clean(asm: str) -> None:
    """Raise AssertionError listing every active-zone absolute write (tear risk). Build/pytest
    guard mirroring `wakestate.assert_overscan_open` / `budget.assert_within_budget`."""
    findings = active_zone_lint(asm)
    if findings:
        raise AssertionError("active-zone absolute writes (tear risk):\n"
                             + "\n".join(f"  {f}" for f in findings))


# --------------------------------------------------------------------------- effect recipes
def band_writer(cols: int, *, src="a4", dst="a2", size="w", advance_dst=None) -> str:
    """A register-indirect beam-raced band writer: `cols` columns of `move.<size> (src)+,(dst)+`
    (the see-through plane-3 scroller idiom). Register-indirect by construction, so it is
    active-zone-clean (passes `active_zone_lint`) and races the beam when placed in a `beam=` window
    (pair with `beamrace.BandGeometry` for the vertical geometry). `advance_dst` (an `adda`/`lea`)
    steps `dst` to the next row after the columns, if given."""
    step = advance_dst + "\n" if advance_dst else ""
    body = "\n".join([f"    move.{size} ({src})+,({dst})+" for _ in range(cols)])
    return body + "\n" + step if step else body


def palette_split(regs: list[str], *, first: int = 0, base: int = 0xFFFF8240) -> str:
    """Aurora's late-line palette write: emit `move.w <reg>,$ffff824X` for each preloaded colour
    register into consecutive palette entries from index `first`. The colours are loaded to
    registers earlier (in the slack / setup); this is the tight write done in the free window
    around the pegs. Palette-register writes are absolute-to-IO — allowed by the lint."""
    lines = [f"    move.w  {r},${base + 2 * (first + i):x}" for i, r in enumerate(regs)]
    return "\n".join(lines)
