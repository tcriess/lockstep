"""Minimal vasm Motorola-syntax line parser, sufficient for cycle timing.

This is deliberately *not* a full assembler (see DESIGN §4.1). It recognises a single
line well enough to: find the mnemonic + size, split operands, classify each operand's
68000 addressing mode, and count a register list. That is everything m68k_table needs to
look up a nominal cycle cost.

Anything the timing engine cannot recognise should surface loudly rather than be guessed
— cycle-exactness is the whole point.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class Mode(Enum):
    """68000 addressing modes (plus a few special operand tokens)."""

    DREG = "Dn"          # d0..d7
    AREG = "An"          # a0..a7 / sp
    AIND = "(An)"        # (a0)
    AINC = "(An)+"       # (a0)+
    ADEC = "-(An)"       # -(a0)
    ADISP = "d16(An)"    # 4(a0)  or (4,a0)
    AINDEX = "d8(An,Xn)" # 4(a0,d1.w) or (4,a0,d1)
    ABSW = "abs.W"       # $ffff820a.w
    ABSL = "abs.L"       # $120 / label / sym+2  (default for bare absolute, -no-opt)
    PCDISP = "d16(PC)"   # label(pc)
    PCINDEX = "d8(PC,Xn)"
    IMM = "#imm"         # #$700
    REGLIST = "reglist"  # d0-d7/a0-a6
    SR = "sr"
    CCR = "ccr"
    USP = "usp"
    UNKNOWN = "?"


# A memory-touching mode (matters for the wait-state / contention layer later).
MEMORY_MODES = {
    Mode.AIND, Mode.AINC, Mode.ADEC, Mode.ADISP, Mode.AINDEX,
    Mode.ABSW, Mode.ABSL, Mode.PCDISP, Mode.PCINDEX,
}

_AREG = r"(?:a[0-7]|sp)"
_XREG = r"[da][0-7](?:\.[wl])?"
_DISP = r"[^(),]+"  # permissive: numbers, symbols, expressions like -230*16


@dataclass
class AsmLine:
    raw: str
    label: str | None = None
    mnemonic: str | None = None     # lower-case, no size suffix, e.g. "move"
    size: str | None = None         # 'b' | 'w' | 'l' | 's' | None
    operands: list[str] = field(default_factory=list)
    comment: str | None = None      # text after ';' (incl. leading ';@' pragmas)

    @property
    def is_instruction(self) -> bool:
        return self.mnemonic is not None and not self.is_directive

    @property
    def is_directive(self) -> bool:
        return self.mnemonic in _DIRECTIVES


_DIRECTIVES = {
    "dc", "dcb", "ds", "even", "align", "equ", "set", "rs", "rsset", "rsreset",
    "rept", "endr", "if", "ifeq", "ifne", "ifd", "ifnd", "else", "endif", "endc",
    "macro", "endm", "include", "incbin", "section", "text", "data", "bss",
    "org", "cnop", "end", "xdef", "xref", "global", "public", "opt",
}

# Instruction mnemonics the timing engine recognises (used only to disambiguate a
# column-1 token: label vs instruction). Sizes are stripped before lookup.
_INSTR_MNEMONICS = {
    "move", "movea", "movem", "movep", "moveq", "lea", "pea", "jmp", "jsr", "nop", "rts",
    "rte", "rtr", "swap", "exg", "ext", "unlk", "link", "reset",
    "add", "sub", "adda", "suba", "addq", "subq", "addi", "subi",
    "and", "or", "eor", "andi", "ori", "eori", "cmp", "cmpa", "cmpi",
    "tst", "clr", "neg", "negx", "not", "nbcd", "tas",
    "asl", "asr", "lsl", "lsr", "rol", "ror", "roxl", "roxr",
    "btst", "bchg", "bclr", "bset", "bra", "bsr",
    "mulu", "muls", "divu", "divs", "trap", "trapv", "illegal", "stop", "chk",
    "bhi", "bls", "bcc", "bcs", "bne", "beq", "bvc", "bvs",
    "bpl", "bmi", "bge", "blt", "bgt", "ble", "bhs", "blo",
    "dbra", "dbf", "dbt", "dbhi", "dbls", "dbcc", "dbcs", "dbne", "dbeq",
    "dbvc", "dbvs", "dbpl", "dbmi", "dbge", "dblt", "dbgt", "dble",
}
KNOWN_MNEMONICS = _INSTR_MNEMONICS | _DIRECTIVES


def _split_comment(line: str) -> tuple[str, str | None]:
    """Split off a trailing ';' comment, ignoring ';' inside strings."""
    in_str = None
    for i, ch in enumerate(line):
        if in_str:
            if ch == in_str:
                in_str = None
        elif ch in "\"'":
            in_str = ch
        elif ch == ";":
            return line[:i], line[i + 1:].strip()
    # vasm also treats a '*' in column 1 as a full-line comment
    if line[:1] == "*":
        return "", line[1:].strip()
    return line, None


def parse_line(raw: str) -> AsmLine:
    """Parse one source line into an AsmLine."""
    body, comment = _split_comment(raw.rstrip("\n"))

    label = None
    # vasm convention: labels start in column 1, instructions are indented. A
    # 'name:' (colon-terminated) is always a label, even indented (a labelled
    # instruction like `    foo:  move.w ...` is valid); a column-1 token without
    # ':' is a label only if it is not a known mnemonic/directive (so a col-1
    # instruction parses). An optionally-labelled instruction may follow on the same line.
    m = re.match(r"^[ \t]*([A-Za-z_.][\w.$]*)(:?)", body)
    if m:
        indent, tok, colon = body[:m.start(1)], m.group(1), m.group(2)
        base = tok.split(".")[0].lower()
        if colon == ":" or (indent == "" and base not in KNOWN_MNEMONICS):
            label = tok
            body = body[m.end():]

    body = body.strip()
    if not body:
        return AsmLine(raw=raw, label=label, comment=comment)

    parts = body.split(None, 1)
    op = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""

    mnemonic, size = _split_size(op)
    operands = _split_operands(rest) if rest else []

    return AsmLine(
        raw=raw, label=label, mnemonic=mnemonic, size=size,
        operands=operands, comment=comment,
    )


def _split_size(op: str) -> tuple[str, str | None]:
    if "." in op:
        base, _, suf = op.rpartition(".")
        if suf in ("b", "w", "l", "s") and base:
            return base, suf
    return op, None


def _split_operands(rest: str) -> list[str]:
    """Split on commas that are not inside parentheses."""
    out, depth, cur = [], 0, ""
    for ch in rest:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def classify_operand(op: str) -> Mode:
    s = op.strip()
    low = s.lower()

    if low in ("sr",):
        return Mode.SR
    if low in ("ccr",):
        return Mode.CCR
    if low in ("usp",):
        return Mode.USP
    if re.fullmatch(r"d[0-7]", low):
        return Mode.DREG
    if re.fullmatch(_AREG, low):
        return Mode.AREG
    if s.startswith("#"):
        return Mode.IMM
    if "/" in s or re.fullmatch(r"[da][0-7]-[da]?[0-7]", low):
        return Mode.REGLIST  # d0-d7, d0-d3, and the d0-7 shorthand

    # PC-relative
    if re.fullmatch(rf"\(?{_DISP},?pc\)", low) or re.search(r",pc\)$|\(pc\)$", low):
        if re.search(r",pc,", low) or re.search(rf"pc,{_XREG}\)$", low):
            return Mode.PCINDEX
        return Mode.PCDISP

    # Register-indirect family, old-style disp(an[,xn]) and new-style (disp,an[,xn])
    if re.fullmatch(rf"\({_AREG}\)", low):
        return Mode.AIND
    if re.fullmatch(rf"\({_AREG}\)\+", low):
        return Mode.AINC
    if re.fullmatch(rf"-\({_AREG}\)", low):
        return Mode.ADEC
    # indexed: old  d(an,xn)   new (d,an,xn)
    if re.fullmatch(rf"{_DISP}\({_AREG},{_XREG}\)", low) or \
       re.fullmatch(rf"\({_DISP},{_AREG},{_XREG}\)", low):
        return Mode.AINDEX
    # displacement: old d(an)   new (d,an)
    if re.fullmatch(rf"{_DISP}\({_AREG}\)", low) or \
       re.fullmatch(rf"\({_DISP},{_AREG}\)", low):
        return Mode.ADISP

    # Absolute: explicit .w suffix -> abs.W, else abs.L (matches vasm -no-opt default)
    if low.endswith(".w"):
        return Mode.ABSW
    if low.endswith(".l"):
        return Mode.ABSL
    # bare number / symbol / expression -> absolute long
    return Mode.ABSL


def count_reglist(op: str) -> int:
    """Count registers named by a movem list like 'd0-d7/a0-a6' or 'd0-d3'."""
    total = 0
    for grp in op.lower().split("/"):
        grp = grp.strip()
        if not grp:
            continue
        if "-" in grp:
            a, b = (x.strip() for x in grp.split("-", 1))
            if b[:1] not in ("d", "a"):       # shorthand 'd0-7' -> 'd0-d7'
                b = a[0] + b
            total += _regnum(b) - _regnum(a) + 1
        else:
            total += 1
    return total


def _regnum(r: str) -> int:
    r = r.strip()
    base = 0 if r[0] == "d" else 8  # d0..d7 = 0..7, a0..a7 = 8..15
    return base + int(r[1])
