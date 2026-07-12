"""`python -m st68k` / `stcyc` CLI.

P1 ships `annotate`. `check`, `build`, `verify` (DESIGN §4) land in later phases.
"""

from __future__ import annotations

import argparse
import sys

from .annotate import annotate_report, block_cycles
from .cycles import STF_NTSC, STF_PAL, CycleEngine, FirstOrderRound4
from .preprocess import PreprocessError, expand


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="stcyc", description="Atari ST cycle tooling")
    ap.add_argument("--ntsc", action="store_true", help="use STF/NTSC (default PAL)")
    ap.add_argument("--round4", action="store_true",
                    help="use the phase-blind round-to-4 model (default: bus-phase)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("annotate", help="per-line + running cycle counts")
    a.add_argument("file", help="source .s file (or - for stdin)")

    t = sub.add_parser("total", help="print total cycles of a region (min..max)")
    t.add_argument("file", help="source .s file (or - for stdin)")

    b = sub.add_parser("build", help="expand @-directives -> assemblable source")
    b.add_argument("file", help="source .src.s file (or - for stdin)")
    b.add_argument("-o", "--output", help="output file (default: stdout)")

    c = sub.add_parser("check", help="verify all @budget/@at/@pad regions (no output)")
    c.add_argument("file", help="source .src.s file (or - for stdin)")

    m = sub.add_parser("measure", help="measure a chunk's REAL cycles in Hatari (oracle)")
    m.add_argument("file", help="asm chunk file (or - for stdin)")
    m.add_argument("--setup", help="asm file run before the measured region (regs etc.)")

    args = ap.parse_args(argv)
    engine = CycleEngine(wait_model=FirstOrderRound4() if args.round4 else None,
                         machine=STF_NTSC if args.ntsc else STF_PAL)

    text = sys.stdin.read() if args.file == "-" else open(args.file).read()

    if args.cmd == "annotate":
        print(annotate_report(text, engine))
    elif args.cmd == "total":
        cmin, cmax = block_cycles(text, engine)
        print(f"{cmin}c" if cmin == cmax else f"{cmin}..{cmax}c")
    elif args.cmd == "build":
        try:
            result, _ = expand(text, engine)
        except PreprocessError as e:
            print(f"stcyc build: {e}", file=sys.stderr)
            return 1
        if args.output:
            with open(args.output, "w") as f:
                f.write(result)
        else:
            sys.stdout.write(result)
    elif args.cmd == "check":
        try:
            _, report = expand(text, engine)
        except PreprocessError as e:
            print(f"FAIL  {e}", file=sys.stderr)
            return 1
        for r in report:
            print(f"{'ok  ' if r.ok else 'FAIL'}  L{r.lineno}: {r.detail}")
        print(f"\n{len(report)} region(s) checked, all on budget.")
    elif args.cmd == "measure":
        from .hatari import HatariError, measure
        setup = open(args.setup).read() if args.setup else ""
        try:
            m = measure(text, setup=setup)
        except HatariError as e:
            print(f"stcyc measure: {e}", file=sys.stderr)
            return 1
        # compare against the static estimate
        s_lo, s_hi = block_cycles(text, engine)
        static = f"{s_lo}c" if s_lo == s_hi else f"{s_lo}..{s_hi}c"
        verdict = "MATCH" if s_lo <= m.cycles <= s_hi else "DIFFERS (real vs round-4)"
        print(f"Hatari (cycle-exact): {m.cycles}c")
        print(f"static estimate:      {static}   -> {verdict}")
        print(f"beam:                 {m.beam}")
        if m.spans_vbl:
            print("note: chunk spans a VBL boundary (cycles use PAL frame length)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
