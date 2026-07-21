"""`stcyc annotate` — per-line + running cycle counts for a source region.

Read-only for now: it prints a report rather than rewriting the file (DESIGN §5.1 leans
generated-file; in-place rewrite comes with the directive pass). It already understands
`dcb.w n,$4e71` nop-filler (4n cycles) and `rept`/`endr` (body x N), plus the `;@sync`
pragma as a running-total reset, so it reproduces the bookkeeping done by hand today.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .cycles import CycleEngine
from .m68k_table import Confidence, UnknownInstruction
from .parser import AsmLine, parse_line

# dcb.w <n>,$4e71  -> n nop words = 4n executable cycles. Any other dcb is data.
_DCB_NOP = re.compile(r"^dcb\.w\s+(\d+)\s*,\s*\$4e71\s*$", re.I)
_REPT = re.compile(r"^rept\s+(\S+)", re.I)


def _intval(s: str) -> int | None:
    s = s.strip()
    try:
        if s.startswith("$"):
            return int(s[1:], 16)
        if s.startswith("%"):
            return int(s[1:], 2)
        return int(s, 10)
    except ValueError:
        return None


def collect_equs(text: str) -> dict[str, int]:
    """Map simple `name equ <int>` / `name = <int>` constants (for rept counts)."""
    equs: dict[str, int] = {}
    for raw in text.splitlines():
        line = parse_line(raw)
        if line.label and line.mnemonic in ("equ", "set", "=") and line.operands:
            v = _intval(line.operands[0])
            if v is not None:
                equs[line.label] = v
    return equs


def _resolve_count(tok: str, equs: dict[str, int]) -> int | None:
    v = _intval(tok)
    return v if v is not None else equs.get(tok)


@dataclass
class LineCost:
    line: AsmLine
    lineno: int
    cmin: int          # cycles, min
    cmax: int          # cycles, max
    kind: str          # 'instr' | 'filler' | 'rept' | 'endr' | 'other'
    note: str = ""
    confidence: Confidence | None = None
    approximate: bool = False

    @property
    def counts(self) -> bool:
        return self.kind in ("instr", "filler")


_STALL = re.compile(r";@stall\s+(\d+)\b")


def cost_of_line(raw: str, lineno: int, engine: CycleEngine,
                 phase: int = 0) -> tuple[LineCost, int]:
    """Phase-aware cost of one source line. Returns (LineCost, new_bus_phase)."""
    if (m := _STALL.search(raw)):
        # ;@stall N — the CPU is bus-stalled N extra cycles here (a started blitter owns the
        # bus; deterministic on the 4-cycle grid, so it costs like filler). The author owns
        # the number — the Hatari oracle is the check. Assembles as a plain comment.
        n = int(m.group(1))
        if n % 4 != 0:
            raise ValueError(f"line {lineno}: ;@stall {n} — stalls must be 4-cycle aligned")
        line = parse_line(raw)
        return LineCost(line, lineno, n, n, "filler", f"declared bus stall ({n}c)"), phase
    line = parse_line(raw)

    if line.mnemonic == "dcb":
        m = _DCB_NOP.match(_collapse(line))
        if m:
            n = int(m.group(1))
            # n nops threaded through the bus phase: at phase 2 the first nop realigns
            # (+2), then 4 each; result is phase 0. At phase 0: 4n, stays phase 0.
            cost = 4 * n + (2 if (phase == 2 and n > 0) else 0)
            nph = 0 if n > 0 else phase
            return LineCost(line, lineno, cost, cost, "filler", f"{n} x nop"), nph
        return LineCost(line, lineno, 0, 0, "other", "dcb data (not executable)"), phase

    if (m := _REPT.match(_collapse(line))):
        return LineCost(line, lineno, 0, 0, "rept", m.group(1)), phase
    if line.mnemonic == "endr":
        return LineCost(line, lineno, 0, 0, "endr"), phase

    if line.is_instruction:
        try:
            sc, nph = engine.cost(line, phase)
        except UnknownInstruction as e:
            return LineCost(line, lineno, 0, 0, "other", f"UNKNOWN: {e}",
                            Confidence.UNKNOWN), phase
        return (LineCost(line, lineno, sc.st_min, sc.st_max, "instr", sc.note,
                         sc.confidence, sc.approximate), nph)

    return LineCost(line, lineno, 0, 0, "other"), phase


def _collapse(line: AsmLine) -> str:
    """Reassemble mnemonic + operands lower-cased for directive matching."""
    if not line.mnemonic:
        return ""
    s = line.mnemonic + ("." + line.size if line.size else "")
    if line.operands:
        s += " " + ",".join(line.operands)
    return s.lower()


def _find_endr(lines: list[str], start: int) -> int:
    """Index of the `endr` matching the `rept` at `start` (handles nesting)."""
    depth = 0
    for j in range(start, len(lines)):
        line = parse_line(lines[j])
        if _REPT.match(_collapse(line)):
            depth += 1
        elif line.mnemonic == "endr":
            depth -= 1
            if depth == 0:
                return j
    raise ValueError("unterminated `rept` (missing `endr`)")


def _sum_lines(lines: list[str], engine: CycleEngine, equs: dict[str, int],
               phase: int) -> tuple[int, int, int]:
    """(min, max, end_phase) for a list of source lines, threading the bus phase.

    A `rept` body is summed once; if it is phase-neutral (end phase == entry phase) the
    cost is multiplied by N, otherwise the body's two phase variants alternate and both
    are summed (phase is in {0,2}, so the period is at most 2)."""
    cmin = cmax = 0
    i = 0
    while i < len(lines):
        lc, nph = cost_of_line(lines[i], i + 1, engine, phase)
        if lc.kind == "rept":
            n = _resolve_count(lc.note, equs)
            if n is None:
                raise ValueError(f"line {i + 1}: cannot resolve rept count {lc.note!r}")
            j = _find_endr(lines, i)
            body = lines[i + 1:j]
            b1min, b1max, p1 = _sum_lines(body, engine, equs, phase)
            if p1 == phase or n == 1:
                cmin += b1min * n
                cmax += b1max * n
                phase = p1
            else:                            # oscillating body: two alternating variants
                b2min, b2max, _ = _sum_lines(body, engine, equs, p1)
                pairs, rem = divmod(n, 2)
                cmin += (b1min + b2min) * pairs + (b1min if rem else 0)
                cmax += (b1max + b2max) * pairs + (b1max if rem else 0)
                phase = phase if rem == 0 else p1
            i = j + 1
        elif lc.kind == "endr":
            i += 1
        else:
            if lc.kind == "other" and lc.confidence == Confidence.UNKNOWN:
                raise UnknownInstruction(f"line {i + 1}: {lc.note}")
            cmin += lc.cmin
            cmax += lc.cmax
            phase = nph
            i += 1
    return cmin, cmax, phase


def block_cycles(text: str, engine: CycleEngine | None = None) -> tuple[int, int]:
    """Total (min, max) ST cycles of a straight-line / rept block, bus-phase accurate.

    Honours `dcb.w n,$4e71` fillers and nested `rept N`/`endr`, threading the bus phase
    from an aligned origin (phase 0). Raises on an instruction with no known timing.
    """
    engine = engine or CycleEngine()
    equs = collect_equs(text)
    cmin, cmax, _ = _sum_lines(text.splitlines(), engine, equs, 0)
    return cmin, cmax


def annotate_report(text: str, engine: CycleEngine | None = None) -> str:
    """A human-readable per-line report with running totals (reset at `;@sync`)."""
    engine = engine or CycleEngine()
    equs = collect_equs(text)
    out: list[str] = []
    run_stack = [0]                      # running total per rept frame
    rep_counts = [1]
    approx_seen = False
    phase = 0                            # bus phase, threaded; reset at @sync

    for i, raw in enumerate(text.splitlines(), 1):
        lc, phase = cost_of_line(raw, i, engine, phase)
        pragma = (lc.line.comment or "").strip()
        if pragma.startswith("@sync"):
            run_stack[-1] = 0
            phase = 0

        if lc.kind == "rept":
            n = _resolve_count(lc.note, equs)
            run_stack.append(0)
            rep_counts.append(n if n is not None else 1)
            shown = lc.note if n is None else n
            out.append(f"{i:5}  {'':>10}  {raw.rstrip()}   ; >>> rept x{shown}"
                       + ("  (unresolved -> counted x1)" if n is None else ""))
            continue
        if lc.kind == "endr":
            if len(run_stack) == 1:
                out.append(f"{i:5}  {'':>10}  {raw.rstrip()}   ; (stray endr)")
                continue
            body = run_stack.pop()
            n = rep_counts.pop()
            run_stack[-1] += body * n
            out.append(f"{i:5}  {'':>10}  {raw.rstrip()}   "
                       f"; <<< body={body}c x{n} = {body * n}c  run={run_stack[-1]}c")
            continue

        if lc.counts:
            run_stack[-1] += lc.cmax
            approx_seen = approx_seen or lc.approximate
            cyc = f"{lc.cmin}c" if lc.cmin == lc.cmax else f"{lc.cmin}..{lc.cmax}c"
            tag = ""
            if lc.confidence == Confidence.VARIABLE:
                tag = "  ~var"
            out.append(f"{i:5}  {cyc:>10}  {raw.rstrip()}   "
                       f"; run={run_stack[-1]}c{tag}")
        else:
            out.append(f"{i:5}  {'':>10}  {raw.rstrip()}")

    header = [
        f"# cycle model: {engine.wm.name}",
        f"# machine: {engine.machine.name}  ({engine.machine.cycles_per_line}c/line, "
        f"{engine.machine.cycles_per_frame}c/frame)",
    ]
    if approx_seen:
        header.append("# NOTE: counts are first-order approximations; verify in Hatari "
                      "(DESIGN §1.1, §3).")
    return "\n".join(header + [""] + out)
