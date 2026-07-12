"""P2 — directive expansion. Turns intent into exact filler (DESIGN §2).

Pragmas are `;@`-prefixed comments, so the source still assembles under vanilla vasm.
This pass reads `foo.src.s` and emits `foo.s` with the directives replaced by real
`dcb.w n,$4e71` / nothing, or fails loudly when a region can't be made to fit.

Cycle origin: the running count is measured from the most recent `;@sync` (or file
start, or the start of a `;@budget` region). Counts are over the *literal* source lines
between markers — an enclosing `rept` repeats the already-sized body, so directive
sizing correctly ignores the repeat factor.

Directives implemented here:
    ;@sync              reset the origin (running count -> 0)
    ;@pad N             emit filler so the running count here == N
    ;@at  N             assert running count == N (emits nothing; fails the build if off)
    ;@budget N / ;@end  bracket a region that must total exactly N cycles
    ;@fill              inside a budget: the point that absorbs the remainder to hit N
"""

from __future__ import annotations

from dataclasses import dataclass

from .annotate import _intval, cost_of_line
from .cycles import CycleEngine
from .m68k_table import Confidence
from .parser import parse_line


class PreprocessError(Exception):
    pass


@dataclass
class Pragma:
    name: str
    arg: int | None        # second token as an int, if it is one
    word: str | None       # second token as a string (e.g. @balance alt)
    raw: str


def parse_pragma(comment: str | None) -> Pragma | None:
    if not comment:
        return None
    c = comment.strip()
    if not c.startswith("@"):
        return None
    toks = c[1:].split()
    if not toks:
        return None
    word = toks[1].lower() if len(toks) > 1 else None
    arg = _intval(toks[1]) if len(toks) > 1 else None
    return Pragma(toks[0].lower(), arg, word, c)


def _fill_lines(gap: int, phase: int, tag: str, lineno: int) -> tuple[list[str], int]:
    """Emit `dcb.w n,$4e71` filler of exactly `gap` cycles from bus `phase`.

    At phase 0 the filler is 4n (gap must be a multiple of 4). At phase 2 the first nop
    realigns (+6 -> phase 0), so the filler is 6+4k (gap must be 2 mod 4, >= 6). Returns
    (lines, new_phase)."""
    if gap == 0:
        return [f"    ; {tag}: already on target (+0c)"], phase
    if gap < 0:
        raise PreprocessError(
            f"line {lineno}: {tag} — region is {-gap}c OVER target (cannot remove code)")
    if phase == 2:
        if gap < 6 or gap % 4 != 2:
            raise PreprocessError(
                f"line {lineno}: {tag} — at bus phase 2, need {gap}c but nop filler can "
                f"only realign as 6+4k (>=6, 2 mod 4); odd-residue (DESIGN §5.3, parked)")
        n = 1 + (gap - 6) // 4
        return [f"    dcb.w {n},$4e71  ; {tag}: +{gap}c (phase-2 realign)"], 0
    if gap % 4 != 0:
        raise PreprocessError(
            f"line {lineno}: {tag} — need {gap}c of filler but only 4c nops are available "
            f"({gap} is not a multiple of 4; odd-residue filler is DESIGN §5.3, parked)")
    return [f"    dcb.w {gap // 4},$4e71  ; {tag}: +{gap}c"], 0


@dataclass
class _Region:
    n: int
    buf: list[str]
    fill_idx: int | None
    outer_run: int
    outer_ambig: bool
    fill_phase: int = 0


@dataclass
class _Balance:
    """Two-arm branch equalization (DESIGN §2.2). The conditional branch's not-taken
    cost belongs to arm 1 (fall-through), its taken cost to arm 2 (the target); the arms
    enter at different bus phases and must reconverge at equal total cycles."""
    start_phase: int
    arm: int = 1
    phase: int = 0
    branch_nt: int = 0
    branch_taken: int = 0
    arm1_cost: int = 0
    arm2_cost: int = 0
    fill_arm: int | None = None
    fill_idx: int | None = None
    fill_phase: int = 0


@dataclass
class Result:
    """One report line for `check`."""
    lineno: int
    kind: str          # 'pad' | 'budget' | 'at' | 'balance'
    detail: str
    ok: bool = True


def expand(text: str, engine: CycleEngine | None = None) -> tuple[str, list[Result]]:
    """Expand directives. Returns (output_text, report). Raises PreprocessError on a
    region that cannot be satisfied (overflow, off-budget @at, ambiguous cost, etc.)."""
    engine = engine or CycleEngine()
    out: list[str] = []
    rept_stack: list[tuple[int, int, int]] = []   # (count, run_at_open, phase_at_open)
    region: _Region | None = None
    # A STACK, not a single block: real per-frame logic nests conditionals (Aurora's sprite-sequence
    # step has a `beq` inside a `bge` arm). An inner @balance is costed on its own, then its balanced
    # cost is folded into whichever arm of the enclosing @balance contains it.
    bstack: list[_Balance] = []
    expect_branch = False
    run = 0
    phase = 0                  # bus phase, threaded; reset at @sync
    ambiguous = False          # a variable-cost instruction since the origin?
    report: list[Result] = []

    def target() -> list[str]:
        return region.buf if region else out

    for i, raw in enumerate(text.splitlines(), 1):
        line = parse_line(raw)
        prag = parse_pragma(line.comment)

        # ---- @balance control directives ----
        if prag and prag.name == "balance":
            sub = prag.word
            if sub is None:                         # open (may nest)
                bstack.append(_Balance(start_phase=bstack[-1].phase if bstack else phase))
                expect_branch = True
                target().append(raw.rstrip("\n"))
                continue
            if not bstack:
                raise PreprocessError(f"line {i}: @balance {sub} without @balance")
            if sub == "alt":
                b = bstack[-1]
                b.arm = 2
                b.phase = (b.start_phase + b.branch_taken) % 4
                target().append(raw.rstrip("\n"))
                continue
            if sub == "end":
                target().append(raw.rstrip("\n"))
                b = bstack.pop()
                cost, newphase = _finish_balance(b, target(), i, report)
                if bstack:                          # nested: fold into the enclosing arm
                    outer = bstack[-1]
                    if outer.arm == 1:
                        outer.arm1_cost += cost
                    else:
                        outer.arm2_cost += cost
                    outer.phase = newphase
                else:
                    run += cost
                    phase = newphase
                continue
            raise PreprocessError(f"line {i}: unknown @balance '{sub}'")

        # ---- lines inside a @balance block ----
        if bstack:
            balance = bstack[-1]
            target().append(raw.rstrip("\n"))
            if expect_branch:
                if not line.is_instruction:
                    continue                        # comments/blanks before the branch
                lc, _ = cost_of_line(raw, i, engine, balance.start_phase)
                # A Bcc is VARIABLE (taken != not-taken) — except Bcc.w, whose two costs are BOTH
                # 12c, so it is variable-by-nature yet equal-by-cost. Gate on the confidence, not on
                # cmin != cmax, or a @balance around a word branch would be rejected out of hand.
                if lc.confidence is not Confidence.VARIABLE:
                    raise PreprocessError(
                        f"line {i}: @balance must be followed by a conditional branch "
                        f"(got a fixed-cost instruction)")
                balance.branch_nt, balance.branch_taken = lc.cmin, lc.cmax
                balance.phase = (balance.start_phase + balance.branch_nt) % 4
                expect_branch = False
                continue
            lc, balance.phase = cost_of_line(raw, i, engine, balance.phase)
            if lc.kind == "other" and lc.confidence == Confidence.UNKNOWN:
                raise PreprocessError(f"line {i}: {lc.note}")
            if prag and prag.name == "fill":
                if balance.fill_arm is not None:
                    raise PreprocessError(f"line {i}: only one @fill per @balance")
                balance.fill_arm = balance.arm
                balance.fill_idx = len(target())
                balance.fill_phase = balance.phase
                continue
            if lc.counts:
                if lc.cmin != lc.cmax:
                    raise PreprocessError(
                        f"line {i}: variable-cost instruction inside a @balance arm")
                if balance.arm == 1:
                    balance.arm1_cost += lc.cmax
                else:
                    balance.arm2_cost += lc.cmax
            continue

        # ---- normal handling ----
        lc, phase = cost_of_line(raw, i, engine, phase)
        if lc.kind == "other" and lc.confidence == Confidence.UNKNOWN:
            raise PreprocessError(f"line {i}: {lc.note}")

        if lc.kind == "rept":
            try:
                n = int(str(lc.note), 0)
            except (TypeError, ValueError):
                raise PreprocessError(
                    f"line {i}: cannot resolve the rept count {lc.note!r} in a sized region — "
                    f"filler cannot be sized without knowing how many times the body runs") from None
            rept_stack.append((n, run, phase))
            target().append(raw.rstrip("\n"))
            continue

        if lc.kind == "endr":
            if not rept_stack:
                raise PreprocessError(f"line {i}: `endr` without `rept`")
            n, run0, phase0 = rept_stack.pop()
            body = run - run0
            if body % 4:
                raise PreprocessError(
                    f"line {i}: the rept body costs {body}c, which is not a multiple of 4 — its "
                    f"cost would differ from one iteration to the next (the bus phase walks), so "
                    f"the region cannot be sized. Pad the body to a multiple of 4.")
            run = run0 + n * body            # the body runs N times, not once
            phase = (phase0 + n * body) % 4
            target().append(raw.rstrip("\n"))
            continue

        target().append(raw.rstrip("\n"))
        if lc.counts:
            run += lc.cmax
            if lc.cmin != lc.cmax:
                ambiguous = True

        if not prag:
            continue
        name = prag.name

        if name == "sync":
            if region:
                raise PreprocessError(f"line {i}: @sync inside a @budget region")
            run, ambiguous, phase = 0, False, 0

        elif name == "at":
            _need_arg(prag, i)
            _need_determinate(ambiguous, i, "@at")
            ok = run == prag.arg
            report.append(Result(i, "at", f"@at {prag.arg}: actual {run}c", ok))
            if not ok:
                raise PreprocessError(f"line {i}: @at {prag.arg} — actual {run}c")

        elif name == "pad":
            _need_arg(prag, i)
            _need_determinate(ambiguous, i, "@pad")
            gap = prag.arg - run
            fill, phase = _fill_lines(gap, phase, f"@pad {prag.arg}", i)
            target().extend(fill)
            report.append(Result(i, "pad", f"@pad {prag.arg}: +{max(gap,0)}c"))
            run = prag.arg

        elif name == "budget":
            _need_arg(prag, i)
            if region:
                raise PreprocessError(f"line {i}: nested @budget is not supported")
            region = _Region(prag.arg, [], None, run, ambiguous)
            run, ambiguous = 0, False

        elif name == "fill":
            if not region:
                raise PreprocessError(f"line {i}: @fill outside a @budget region")
            if region.fill_idx is not None:
                raise PreprocessError(f"line {i}: a @budget region may have only one @fill")
            region.fill_idx = len(region.buf)
            region.fill_phase = phase

        elif name == "end":
            if not region:
                raise PreprocessError(f"line {i}: @end without @budget")
            _need_determinate(ambiguous, i, "@end")
            total = run
            if region.fill_idx is not None:
                gap = region.n - total
                fill, _ = _fill_lines(gap, region.fill_phase,
                                      f"@fill -> budget {region.n}", i)
                region.buf[region.fill_idx:region.fill_idx] = fill
                report.append(Result(i, "budget",
                                     f"@budget {region.n}: {total}c code + {max(gap,0)}c fill"))
            else:
                ok = total == region.n
                report.append(Result(i, "budget",
                                     f"@budget {region.n}: total {total}c", ok))
                if not ok:
                    raise PreprocessError(
                        f"line {i}: @budget {region.n} — region totals {total}c "
                        f"and has no @fill to absorb the difference")
            out.extend(region.buf)
            run = region.outer_run + region.n
            ambiguous = region.outer_ambig
            region = None

        # unknown @names are left as-is (forward-compat)

    if region:
        raise PreprocessError("unterminated @budget (missing @end)")
    if rept_stack:
        raise PreprocessError("unterminated `rept` (missing `endr`)")
    if bstack:
        raise PreprocessError("unterminated @balance (missing @balance end)")
    return "\n".join(out) + "\n", report


def _finish_balance(b: _Balance, out: list[str], lineno: int,
                    report: list[Result]) -> tuple[int, int]:
    """Equalize the two arms by sizing the @fill; return (balanced_cost, new_phase)."""
    path1 = b.branch_nt + b.arm1_cost          # fall-through (branch not taken)
    path2 = b.branch_taken + b.arm2_cost       # target (branch taken)
    if b.fill_arm == 1:
        gap = path2 - path1
        fill, _ = _fill_lines(gap, b.fill_phase, "@balance fill (arm1)", lineno)
        out[b.fill_idx:b.fill_idx] = fill
        balanced = path2
    elif b.fill_arm == 2:
        gap = path1 - path2
        fill, _ = _fill_lines(gap, b.fill_phase, "@balance fill (arm2)", lineno)
        out[b.fill_idx:b.fill_idx] = fill
        balanced = path1
    else:
        if path1 != path2:
            raise PreprocessError(
                f"line {lineno}: @balance arms differ (fall-through {path1}c vs taken "
                f"{path2}c) and there is no @fill to equalize them")
        balanced = path1
    report.append(Result(lineno, "balance",
                         f"@balance: fall-through {path1}c / taken {path2}c -> {balanced}c"))
    return balanced, (b.start_phase + balanced) % 4


def _need_arg(prag: Pragma, lineno: int) -> None:
    if prag.arg is None:
        raise PreprocessError(f"line {lineno}: @{prag.name} needs an integer argument")


def _need_determinate(ambiguous: bool, lineno: int, what: str) -> None:
    if ambiguous:
        raise PreprocessError(
            f"line {lineno}: {what} follows a variable-cost instruction (range, not a "
            f"single cycle count) since the origin — filler cannot be sized "
            f"deterministically. Use a fixed path or @balance the branch.")
