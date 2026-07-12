"""Lockstep packer — pour the work stream into the gaps between pegs (DESIGN §7.2).

The packer is *pure placement*. It decides which work blocks land in which gap on which
line, then emits a directive-laden intermediate of the shape

    ;@budget 512
        <work poured into gap 0>
    ;@pad <peg0.offset>
        <peg0 asm>
        <work poured into gap 1>
    ;@pad <peg1.offset>
        <peg1 asm>
        ...
        <work poured into the final gap>
    ;@fill
    ;@end

and hands it to `st68k.preprocess.expand()`, which does the exact, bus-phase-aware filler
sizing, threads the bus phase through pegs/work/fillers, and raises the odd-residue error
when a gap cannot be nop-filled. So gap sizing and the timing model are *not* reimplemented
here — the packer only has to place work consistently with the same engine, and `expand()`
is the source of truth for the result.

Bus phase carries across scanlines for free: every line is exactly `line_len` cycles and
512 ≡ 0 (mod 4), so the phase entering each line equals the phase entering the first one
(0 from a `;@sync`'d origin).
"""

from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass, field

from st68k.annotate import block_cycles, cost_of_line
from st68k.cycles import CycleEngine
from st68k.preprocess import PreprocessError, Result, expand

# A placement unit: source lines that must be placed together (whole or not at all), plus an
# optional beam-race window. A splittable block explodes into one unit per line; an atomic
# block is one unit. `beam` is (lo, hi) line-cycles the unit must execute within, or None.
Unit = namedtuple("Unit", ["lines", "beam"])


class PackError(Exception):
    """The work stream cannot be packed into the template (too big a block, not enough
    lines, an over-full line, or an unfillable gap surfaced by expand())."""


@dataclass
class PackResult:
    asm: str                       # final assemblable source (directives expanded)
    intermediate: str              # the directive intermediate (for inspection/debug)
    report: list[Result]           # per-region budget report from expand()
    n_lines: int                   # scanlines emitted
    units_total: int               # work units in the stream
    units_placed: int              # work units actually placed
    placed_per_line: list[int]     # units placed on each line
    nop_cycles: int = 0            # total nop-filler cycles emitted (step solver: minimised)
    steps_per_line: int | None = None   # steps covered per line (step solver only)

    @property
    def complete(self) -> bool:
        return self.units_placed == self.units_total


def _explode(work) -> list[Unit]:
    """Flatten a WorkStream into placement units (DESIGN §7.1 atomic/splittable)."""
    units: list[Unit] = []
    for blk in work.blocks:
        lines = blk.lines()
        if not lines:
            continue
        beam = getattr(blk, "beam", None)
        if blk.splittable:
            units.extend(Unit([ln], beam) for ln in lines)   # cut anywhere -> per line
        else:
            units.append(Unit(lines, beam))                   # atomic -> one indivisible unit
    return units


def _indent(line: str) -> str:
    return line if line[:1] in (" ", "\t") else "    " + line


def _seq_cost(lines: list[str], engine: CycleEngine,
              phase: int) -> tuple[int, int, bool]:
    """(worst-case cycles, exit phase, is_fixed_cost) for a run of source lines from a
    given entry bus phase. `is_fixed_cost` is False if any line has a cycle range."""
    total, fixed = 0, True
    for ln in lines:
        lc, phase = cost_of_line(ln, 0, engine, phase)
        if lc.counts:
            total += lc.cmax
            fixed = fixed and (lc.cmin == lc.cmax)
    return total, phase, fixed


def _pour_into(units: list[Unit], cursor: int, run: int, target: int, phase: int,
               engine: CycleEngine, into: list[str]) -> tuple[int, int, int]:
    """Greedily place whole units while the next fits in [run, target], appending their
    (indented) lines to `into`. The stream is ordered, so a unit that doesn't fit stops the
    pour (it falls to the next gap) — exactly the hand behaviour in Aurora's display loop.

    A unit with a beam window (lo, hi) is placed only where it runs inside [lo, hi]: if the
    fill position is before lo, pad up to lo (an injected ;@pad); if it cannot complete by hi
    within this gap, stop the pour so the unit falls to the next gap (or surfaces as unplaced)."""
    while cursor < len(units):
        unit = units[cursor]
        cost, exit_phase, _ = _seq_cost(unit.lines, engine, phase)
        start = run
        if unit.beam is not None:
            lo, hi = unit.beam
            if start < lo:                       # pad up to the window's start
                if lo > target:
                    break                        # window opens past this gap -> next gap
                into.append(f";@pad {lo}")
                start, phase = lo, 0             # nop filler realigns the bus phase
            if start + cost > hi:                # cannot finish inside the window here
                if start != run:                 # we already padded; undo isn't possible ->
                    into.pop()                   # drop the pad and let it fall to next gap
                break
        if start + cost > target:
            break
        into.extend(_indent(ln) for ln in unit.lines)
        run, phase = start + cost, exit_phase
        cursor += 1
    return cursor, run, phase


def _peg_footprint(peg, engine: CycleEngine, phase: int) -> tuple[int, int]:
    """(cycles the peg occupies, exit phase). A peg with `reserve` set occupies exactly that
    budget (worst-case sound slot, DESIGN §8) and exits at phase 0 (the headroom is nops);
    otherwise it costs its instructions."""
    if getattr(peg, "reserve", None) is not None:
        return peg.reserve, 0
    cost, ph, _ = _seq_cost(peg.lines(), engine, phase)
    return cost, ph


def _pour_line(units: list[Unit], cursor: int, pegs, L: int,
               engine: CycleEngine, start_phase: int) -> tuple[list[list[str]], int]:
    """Pour units into one line's gaps. Returns (gap_contents, new_cursor) where
    gap_contents has len(pegs)+1 entries — the work for the gap before each peg, then the
    final gap before `;@fill` — with lines already indented. Re-anchors the bus phase at
    line start (every line is L cycles, L % 4 == 0)."""
    gap_contents: list[list[str]] = []
    run, phase = 0, start_phase
    for peg in pegs:
        placed: list[str] = []
        cursor, run, phase = _pour_into(units, cursor, run, peg.offset, phase, engine, placed)
        gap_contents.append(placed)
        if peg.offset > run:                 # nop filler to the peg realigns phase to 0
            phase = 0
        run = peg.offset
        fp, phase = _peg_footprint(peg, engine, phase)
        run += fp                            # for a reserved peg, fp == its budget
    placed = []
    cursor, run, phase = _pour_into(units, cursor, run, L, phase, engine, placed)
    gap_contents.append(placed)
    return gap_contents, cursor


def _gap_capacities(template, engine: CycleEngine, phase: int) -> list[int]:
    """Capacity of each gap (between pegs, and the final gap to line_len) at `phase`.
    Used only for friendly pre-flight diagnostics; expand() is the real validator."""
    caps, prev_end = [], 0
    for peg in template.sorted_pegs():
        caps.append(peg.offset - prev_end)
        fp, phase = _peg_footprint(peg, engine, phase)
        prev_end = peg.offset + fp
    caps.append(template.line_len - prev_end)
    return caps


def _check_pegs(pegs, L: int, engine: CycleEngine, start_phase: int) -> None:
    """Pegs must not overlap and must fit the line (clearer than the raw expand() error)."""
    prev_end = 0
    for peg in pegs:
        if peg.offset < prev_end:
            raise PackError(
                f"peg '{peg.label or peg.offset}' at offset {peg.offset} overlaps the "
                f"previous peg, which ends at {prev_end}c")
        fp, _ = _peg_footprint(peg, engine, start_phase)
        prev_end = peg.offset + fp
    if prev_end > L:
        raise PackError(f"pegs overrun the line: last peg ends at {prev_end}c > {L}c")


def _emit_line(out: list[str], L: int, li: int, pegs, gap_contents: list[list[str]]) -> None:
    """Emit one scanline's directive intermediate from pre-decided per-gap contents
    (`gap_contents[i]` are the already-indented work lines for the gap before peg i; the
    last entry is the final gap before `;@fill`)."""
    out.append(f";@budget {L}    ; --- scanline {li} ---")
    for gi, peg in enumerate(pegs):
        out.extend(gap_contents[gi])
        if peg.label:
            out.append(f"    ; peg @ {peg.offset}c: {peg.label}")
        out.append(f";@pad {peg.offset}")
        out.extend(_indent(ln) for ln in peg.lines())
        if getattr(peg, "reserve", None) is not None:
            # reserve the worst-case sound budget (DESIGN §8): no work goes here; on real
            # hardware replace this headroom with a beam-wait to the slot end if the player
            # is not worst-case-padded.
            out.append(f"    ; --- reserved sound budget: {peg.reserve}c "
                       f"(worst-case replay; runtime constancy is the player's) ---")
            out.append(f";@pad {peg.offset + peg.reserve}")
    out.extend(gap_contents[-1])
    out.append(";@fill")
    out.append(";@end")


def _move_cost(move, engine: CycleEngine) -> int:
    """Cycle cost of a menu move (engine-derived unless given); must be phase-stable."""
    if move.cost is not None:
        c = move.cost
    else:
        c, _, fixed = _seq_cost(move.lines(), engine, 0)
        if not fixed:
            raise PackError(f"menu move {move.label or move.asm!r} has a variable cost")
    if c <= 0:
        raise PackError(f"menu move {move.label or move.asm!r} has non-positive cost {c}c")
    if c % 4 != 0:
        raise PackError(
            f"menu move {move.label or move.asm!r} costs {c}c; the step solver requires "
            f"phase-stable moves (cost a multiple of 4) for now")
    return c


def _enumerate_fills(gap: int, costs: list[int]) -> list[tuple[tuple[int, ...], int]]:
    """All (counts, cycles_used) with sum(counts[i]*costs[i]) <= gap and a nop-fillable
    (multiple-of-4) remainder. `counts` is a per-menu-move tuple."""
    n = len(costs)
    out: list[tuple[tuple[int, ...], int]] = []

    def rec(i: int, remaining: int, counts: list[int]) -> None:
        if i == n:
            used = gap - remaining
            if (gap - used) % 4 == 0:
                out.append((tuple(counts), used))
            return
        k = 0
        while k * costs[i] <= remaining:
            counts.append(k)
            rec(i + 1, remaining - k * costs[i], counts)
            counts.pop()
            k += 1

    rec(0, gap, [])
    return out


def _solve_line(gaps: list[int], costs: list[int], steps: list[int],
                target: int) -> tuple[list[tuple[int, ...]], int] | None:
    """Choose menu-move counts per gap so the line covers EXACTLY `target` steps while each
    gap fills (remainder -> nops), minimising total nop cycles. DP over gaps with the
    running step count as state. Returns (plan, total_nops) or None if infeasible."""
    dp: dict[int, tuple[int, list[tuple[int, ...]]]] = {0: (0, [])}
    for gap in gaps:
        fills = _enumerate_fills(gap, costs)
        ndp: dict[int, tuple[int, list[tuple[int, ...]]]] = {}
        for used_steps, (acc_nops, plan) in dp.items():
            for counts, used_cyc in fills:
                ns = used_steps + sum(counts[j] * steps[j] for j in range(len(costs)))
                if ns > target:
                    continue
                tot = acc_nops + (gap - used_cyc)
                cur = ndp.get(ns)
                if cur is None or tot < cur[0]:
                    ndp[ns] = (tot, plan + [counts])
        dp = ndp
        if not dp:
            return None
    best = dp.get(target)
    return (best[1], best[0]) if best else None


def _emit_stream_segment(out, placed_per_line, idx, template, work, n,
                         li, engine, start_phase):
    """Append one WorkStream band's lines. Work pours continuously across the band's `n`
    lines (cursor persists), then the band's work must be exhausted. Returns
    (units_total, units_placed, next_li)."""
    units = _explode(work)
    pegs = template.sorted_pegs()
    L = template.line_len
    _check_pegs(pegs, L, engine, start_phase)

    caps = _gap_capacities(template, engine, start_phase)
    max_gap = max(caps) if caps else 0
    for u in units:
        cost, _, _ = _seq_cost(u.lines, engine, start_phase)
        if cost > max_gap:
            raise PackError(
                f"segment {idx}: atomic work unit {u.lines!r} costs {cost}c, larger than the "
                f"biggest gap ({max_gap}c) — split it or widen the template")
        if u.beam is not None:
            lo, hi = u.beam
            if hi - lo < cost:
                raise PackError(
                    f"segment {idx}: beam window {u.beam} is only {hi - lo}c, too small for "
                    f"the {cost}c block {u.lines!r}")

    cursor = 0
    for _ in range(n):
        before = cursor
        gap_contents, cursor = _pour_line(units, cursor, pegs, L, engine, start_phase)
        _emit_line(out, L, li, pegs, gap_contents)
        placed_per_line.append(cursor - before)
        li += 1
    if cursor < len(units):
        raise PackError(
            f"segment {idx}: work stream did not fit — {len(units) - cursor} of "
            f"{len(units)} units unplaced after {n} lines; add lines or trim the work")
    return len(units), cursor, li


def _emit_steps_segment(out, placed_per_line, idx, template, work, n,
                        li, engine, start_phase):
    """Append one StepWork band's lines via the exact-cover solver (DESIGN §7.2). Returns
    (units_total, units_placed, nop_cycles, steps_per_line, next_li)."""
    if not work.per_line:
        raise PackError("global step budget (per_line=False) is not yet supported — set "
                        "per_line=True (steps counted per scanline)")
    if start_phase != 0:
        raise PackError("the step solver requires start_phase 0 (phase-stable moves)")
    if not work.menu:
        raise PackError(f"segment {idx}: StepWork has an empty move menu")

    pegs = template.sorted_pegs()
    L = template.line_len
    _check_pegs(pegs, L, engine, start_phase)

    costs = [_move_cost(m, engine) for m in work.menu]
    steps = [m.steps for m in work.menu]
    for m, s in zip(work.menu, steps):
        if s <= 0:
            raise PackError(f"segment {idx}: menu move {m.label or m.asm!r} must advance "
                            f"steps > 0")

    gaps = _gap_capacities(template, engine, start_phase)
    solved = _solve_line(gaps, costs, steps, work.steps)
    if solved is None:
        menu_desc = ", ".join(f"{m.label or m.asm.splitlines()[0]!r}={c}c/{s}st"
                              for m, c, s in zip(work.menu, costs, steps))
        raise PackError(
            f"segment {idx}: cannot cover exactly {work.steps} steps/line: gaps {gaps}c, "
            f"menu [{menu_desc}] — adjust steps, the menu, or the template")
    plan, nops = solved

    gap_contents: list[list[str]] = []
    for counts in plan:
        lines: list[str] = []
        for j, k in enumerate(counts):
            for _ in range(k):
                lines.extend(_indent(ln) for ln in work.menu[j].lines())
        gap_contents.append(lines)

    moves = sum(sum(c) for c in plan)
    for _ in range(n):
        _emit_line(out, L, li, pegs, gap_contents)
        placed_per_line.append(moves)
        li += 1
    return moves * n, moves * n, nops * n, work.steps, li


def _as_segment(s) -> tuple:
    """Normalise a Segment object or a (template, work, n_lines) tuple."""
    if hasattr(s, "template") and hasattr(s, "work") and hasattr(s, "n_lines"):
        return s.template, s.work, s.n_lines
    template, work, n = s
    return template, work, n


def pack_schedule(segments, *, engine: CycleEngine | None = None,
                  start_phase: int = 0) -> PackResult:
    """Pack a sequence of bands into one phase-threaded routine (DESIGN §7.1, multi-variant
    templates). Each segment is a `Segment(template, work, n_lines)` or a
    `(template, work, n_lines)` tuple — its own line template AND its own work (a WorkStream,
    a StepWork, or an empty WorkStream for a border-only line). Scanlines are numbered
    globally; the bus phase carries across band boundaries (every line is line_len ≡ 0 mod 4)."""
    engine = engine or CycleEngine()
    segs = [_as_segment(s) for s in segments]

    out: list[str] = []
    placed_per_line: list[int] = []
    li = units_total = units_placed = nop_cycles = 0
    step_targets: set[int] = set()
    any_stream = False

    for idx, (template, work, n) in enumerate(segs):
        if hasattr(work, "menu"):                   # StepWork band
            ut, up, nops, spl, li = _emit_steps_segment(
                out, placed_per_line, idx, template, work, n, li, engine, start_phase)
            nop_cycles += nops
            step_targets.add(spl)
        else:                                       # WorkStream band
            ut, up, li = _emit_stream_segment(
                out, placed_per_line, idx, template, work, n, li, engine, start_phase)
            any_stream = True
        units_total += ut
        units_placed += up

    intermediate = "\n".join(out) + "\n"
    try:
        asm, report = expand(intermediate, engine)
    except PreprocessError as e:
        raise PackError(f"gap could not be sized exactly: {e}") from e

    steps_per_line = step_targets.pop() if (len(step_targets) == 1 and not any_stream) else None
    return PackResult(
        asm=asm, intermediate=intermediate, report=report, n_lines=li,
        units_total=units_total, units_placed=units_placed,
        placed_per_line=placed_per_line, nop_cycles=nop_cycles,
        steps_per_line=steps_per_line,
    )


def pack(template, work, n_lines: int, *, engine: CycleEngine | None = None,
         start_phase: int = 0) -> PackResult:
    """Pack `work` into `n_lines` copies of one `template`, every line closed to line_len.

    `work` is a WorkStream (atomic/splittable blocks poured into the gaps) or a StepWork
    (a step budget covered by an exact-cover long/word-style move mix, DESIGN §7.2). For a
    screen made of several different line templates (top/bottom border vs mid-screen), use
    `pack_schedule`. Raises PackError on an over/under-constrained template, a unit larger
    than the biggest gap, work that doesn't fit, or an unfillable gap (from expand())."""
    return pack_schedule([(template, work, n_lines)], engine=engine, start_phase=start_phase)
