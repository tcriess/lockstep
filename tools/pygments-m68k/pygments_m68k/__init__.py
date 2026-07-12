"""A Pygments lexer for Motorola 68000 assembly — and, specifically, for Lockstep's dialect of it.

Pygments ships lexers for GAS, NASM, ca65 and TASM, but nothing for the 68000. The GAS lexer is a
passable stand-in (it gets `;` comments right), but it knows nothing about `move.b`, `d3`, `(a1)`,
`$ffff820a` or `dcb.w` — which is most of what a full-sync scanline consists of.

It also highlights the two things this codebase actually cares about:

  * `;@pad 376` / `;@peg` / `;@budget` — Lockstep's directives. They are *comments* to the assembler
    but *instructions* to the toolkit, so they get their own token (Comment.Preproc) and stand out
    from ordinary `; like this` commentary.
  * `dcb.w 90,$4e71` — the nop filler whose count is the whole point of the tool.

Registered two ways:
  * as a Pygments plugin (``pygments.lexers`` entry point), so ```m68k fences and
    ``pygmentize -l m68k`` work anywhere it's installed;
  * as a `fence()` function for pymdownx.superfences, so that ```asm fences in the docs get this
    lexer instead of GAS — letting the Markdown stay portable (GitHub highlights ```asm too).
"""

from __future__ import annotations

from pygments.lexer import RegexLexer, bygroups, words
from pygments.token import (Comment, Keyword, Name, Number, Operator, Punctuation, String, Text,
                            Whitespace)

__all__ = ["M68kLexer", "fence"]
__version__ = "0.1.0"

# The 68000 instruction set (sizes like .b/.w/.l are matched separately).
MNEMONICS = (
    "abcd", "add", "adda", "addi", "addq", "addx", "and", "andi", "asl", "asr",
    "bcc", "bcs", "beq", "bge", "bgt", "bhi", "bhs", "ble", "blo", "bls", "blt", "bmi", "bne",
    "bpl", "bvc", "bvs", "bchg", "bclr", "bra", "bset", "bsr", "btst",
    "chk", "clr", "cmp", "cmpa", "cmpi", "cmpm",
    "dbcc", "dbcs", "dbeq", "dbf", "dbge", "dbgt", "dbhi", "dble", "dblt", "dbmi", "dbne", "dbpl",
    "dbra", "dbt", "dbvc", "dbvs", "divs", "divu",
    "eor", "eori", "exg", "ext",
    "illegal", "jmp", "jsr", "lea", "link", "lsl", "lsr",
    "move", "movea", "movem", "movep", "moveq", "muls", "mulu",
    "nbcd", "neg", "negx", "nop", "not", "or", "ori",
    "pea", "reset", "rol", "ror", "roxl", "roxr", "rte", "rtr", "rts",
    "sbcd", "scc", "scs", "seq", "sf", "sge", "sgt", "shi", "sle", "slo", "sls", "slt", "smi",
    "sne", "spl", "st", "stop", "sub", "suba", "subi", "subq", "subx", "swap",
    "tas", "trap", "trapv", "tst", "unlk",
)

# Assembler directives (vasm/devpac flavour) — dcb.w is the one that matters most here.
DIRECTIVES = (
    "align", "bss", "cnop", "data", "dc", "dcb", "ds", "else", "end", "endc", "endif", "endm",
    "endr", "equ", "equr", "even", "extern", "fail", "globl", "global", "ifeq", "ifne", "incbin",
    "include", "list", "macro", "nolist", "org", "public", "rept", "rs", "rsreset", "section",
    "set", "text", "xdef", "xref",
)


class M68kLexer(RegexLexer):
    """Motorola 68000 assembly, as written for the Atari ST (vasm/devpac syntax)."""

    name = "Motorola 68000 Assembly"
    aliases = ["m68k", "68k", "m68000"]
    filenames = ["*.s", "*.68k", "*.x68"]
    mimetypes = ["text/x-m68k"]
    url = "https://en.wikipedia.org/wiki/Motorola_68000"

    tokens = {
        "root": [
            (r"\s+", Whitespace),

            # Lockstep directives: comments to the assembler, instructions to the toolkit.
            (r";@[^\n]*", Comment.Preproc),
            # Ordinary comments.
            (r"[;*][^\n]*", Comment.Single),

            # Labels: `__band0:`, `.loop:`, `__lock:` (with or without the colon at line start).
            (r"^([.\w$]+)(:)", bygroups(Name.Label, Punctuation)),
            (r"^([.\w$]+)(?=\s)", Name.Label),

            # Directives, with an optional size suffix: dcb.w, dc.b, ds.l
            (words(DIRECTIVES, prefix=r"(?i)\b", suffix=r"(?:\.[bwlsq])?\b"), Name.Builtin),

            # Instructions, with an optional size/condition suffix: move.b, bra.s, lsl.w
            (words(MNEMONICS, prefix=r"(?i)\b", suffix=r"(?:\.[bwlsq])?\b"), Keyword),

            # Registers.
            (r"(?i)\b(?:d[0-7]|a[0-7]|sp|usp|ssp|pc|sr|ccr)\b", Name.Variable),

            # A local label used as a branch target: `dbra d0,.loop`, `bmi.s .done`.
            (r"\.[A-Za-z_]\w*", Name.Label),

            # Numbers: $hex, %binary, decimal. The immediate `#` is an operator.
            (r"\$[0-9a-fA-F]+", Number.Hex),
            (r"%[01]+", Number.Bin),
            (r"@[0-7]+", Number.Oct),
            (r"\d+", Number.Integer),

            (r'"[^"\n]*"', String.Double),
            (r"'[^'\n]*'", String.Single),

            (r"[#+\-*/<>=&|^!~]", Operator),
            (r"[()\[\],.:]", Punctuation),

            (r"[\w$]+", Name),
        ],
    }


def fence(source, language, css_class, options, md, **kwargs):
    """A pymdownx.superfences custom fence, so ```asm blocks use M68kLexer instead of GAS.

    Emits the same `.highlight` wrapper Material expects, so its theming, dark mode and copy
    button all keep working.
    """
    from pygments import highlight
    from pygments.formatters import HtmlFormatter

    formatter = HtmlFormatter(cssclass=css_class or "highlight", wrapcode=True)
    return highlight(source, M68kLexer(), formatter)
