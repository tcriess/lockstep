"""`python -m lockstep` — the full-sync scheduler CLI (DESIGN §7, P5).

    lockstep schedule foo.src.s -o foo.s     expand a ;@template/@work/@schedule spec
                                              into the packed, unrolled, 512c-per-line VBL

The cost model, directive expansion, and Hatari oracle live in the sibling `st68k` package
and its `stcyc` CLI; `lockstep` is the product layer on top.
"""

from __future__ import annotations

import argparse
import sys

from st68k.cycles import STF_NTSC, STF_PAL, CycleEngine, FirstOrderRound4

from .directives import ScheduleError, expand_schedule


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="lockstep",
                                 description="Atari ST full-sync scheduler")
    ap.add_argument("--ntsc", action="store_true", help="use STF/NTSC (default PAL)")
    ap.add_argument("--round4", action="store_true",
                    help="use the phase-blind round-to-4 model (default: bus-phase)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("schedule", help="pack a ;@template/@work/@schedule spec into asm")
    s.add_argument("file", help="schedule spec (.src.s) or - for stdin")
    s.add_argument("-o", "--output", help="output file (default: stdout)")

    v = sub.add_parser("verify", help="pack a spec and confirm each line is 512c in Hatari")
    v.add_argument("file", help="schedule spec (.src.s) or - for stdin")
    v.add_argument("--run-vbls", type=int, default=400,
                   help="Hatari boot budget in VBLs (raise if markers don't fire)")

    args = ap.parse_args(argv)
    engine = CycleEngine(wait_model=FirstOrderRound4() if args.round4 else None,
                         machine=STF_NTSC if args.ntsc else STF_PAL)

    text = sys.stdin.read() if args.file == "-" else open(args.file).read()

    if args.cmd == "schedule":
        try:
            out = expand_schedule(text, engine)
        except ScheduleError as e:
            print(f"lockstep schedule: {e}", file=sys.stderr)
            return 1
        if args.output:
            with open(args.output, "w") as f:
                f.write(out)
        else:
            sys.stdout.write(out)
    elif args.cmd == "verify":
        from st68k.hatari import HatariError

        from .packer import PackError
        from .verify import verify_spec
        try:
            results = verify_spec(text, engine=engine, run_vbls=args.run_vbls)
        except (ScheduleError, PackError, HatariError) as e:
            print(f"lockstep verify: {e}", file=sys.stderr)
            return 1
        all_ok = True
        for tname, nlines, vr in results:
            print(f"# template {tname} x{nlines}")
            print(vr.report())
            all_ok = all_ok and vr.ok
        return 0 if all_ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
