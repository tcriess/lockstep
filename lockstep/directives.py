"""Lockstep `;@`-directive front-end (DESIGN §7) — the second authoring surface.

It parses a *schedule spec* into the very same `LineTemplate` / `WorkStream` objects the
Python API builds, then calls `packer.pack()`. No placement or timing logic lives here:
the directive surface is pure sugar over the core.

Spec grammar (the `;@` lines are comments; the indented asm between markers is the literal
template / work code):

    ;@template <name> [<line_len=512>]
    ;@peg <offset> [label...]
        <instructions>            # belong to the peg above, until the next ;@peg/@endtemplate
    ;@peg <offset> [label...]
        <instructions>
    ;@endtemplate

    ;@work [split|atomic] [repeat=<n>] [beam=<lo>:<hi>]
        <instructions>           # beam=lo:hi pins it to a cycle window (DESIGN §1.3.2)
    ;@endwork                     # one or more; blocks append to the stream in order

  OR, for the step-budget solver (the move.l/move.w trick, DESIGN §7.2):

    ;@stepwork steps=<n>          # cover exactly <n> steps/line with the move menu below
    ;@move <steps>
        <instructions>           # one menu granularity (self-contained step)
    ;@move <steps>
        <instructions>
    ;@endstepwork

    ;@schedule <template> lines=<n>   # emit the packed, unrolled routine here

For a screen built of several different line templates (top/bottom-border lines differ from
mid-screen), name the works and list bands in a screen block:

    ;@work name=scroll repeat=39
        ...
    ;@endwork
    ;@screen
    ;@segment topborder lines=1                  # no work= -> border-only line
    ;@segment mid       work=scroll lines=199
    ;@segment botborder lines=1
    ;@endscreen                                  # packed as ONE phase-threaded routine

Unlike the @pad/@budget directives, a schedule spec is a *build input*, not drop-in asm:
the fragments are declarations the packer relocates, not code that runs where it is written.
"""

from __future__ import annotations

from dataclasses import dataclass

from st68k.cycles import CycleEngine
from st68k.parser import parse_line

from .model import LineTemplate, Move, Peg, StepWork, WorkBlock, WorkStream
from .packer import PackError, pack, pack_schedule


class ScheduleError(Exception):
    pass


def _directive(raw: str) -> tuple[str, list[str]] | None:
    """If `raw` is a standalone `;@<name> ...` line, return (name, args); else None."""
    line = parse_line(raw)
    if line.is_instruction:                 # a real asm line is content, not a directive
        return None
    c = (line.comment or "").strip()
    if not c.startswith("@"):
        return None
    toks = c[1:].split()
    return (toks[0].lower(), toks[1:]) if toks else None


def _int(tok: str, lineno: int, what: str) -> int:
    s = tok.strip()
    try:
        return int(s[1:], 16) if s.startswith("$") else int(s, 10)
    except ValueError:
        raise ScheduleError(f"line {lineno}: {what} expects an integer, got {tok!r}")


def _kw(args: list[str], key: str) -> str | None:
    """Pull a `key=value` argument out of a token list."""
    for a in args:
        if a.lower().startswith(key + "="):
            return a.split("=", 1)[1]
    return None


@dataclass
class ParsedSpec:
    templates: dict[str, LineTemplate]
    default_work: WorkStream | StepWork   # the unnamed ;@work/;@stepwork (for ;@schedule)
    works: dict[str, WorkStream | StepWork]   # named works (for ;@segment work=NAME)
    items: list                           # ('single', tname, nlines, lineno) or
                                          # ('screen', [(tname, wname|None, nlines)...], lineno)


def parse(text: str) -> ParsedSpec:
    """Parse a schedule spec into templates, work(s), and schedule/screen items.

    Unnamed ;@work / ;@stepwork form the default work used by ;@schedule (one or the other).
    A ;@work name=X / ;@stepwork name=X is a *named* work referenced by ;@segment work=X
    inside a ;@screen … ;@endscreen multi-band block."""
    templates: dict[str, LineTemplate] = {}
    stream = WorkStream([])                     # default unnamed work
    stepwork: StepWork | None = None            # default unnamed stepwork
    works: dict[str, WorkStream | StepWork] = {}
    items: list = []

    tmpl_name: str | None = None
    tmpl_len = 512
    pegs: list[Peg] = []
    peg_off: int | None = None
    peg_label = ""
    peg_buf: list[str] = []

    in_work = False
    work_name: str | None = None
    work_split = False
    work_repeat = 1
    work_beam: tuple[int, int] | None = None
    work_buf: list[str] = []

    in_step = False
    step_name: str | None = None
    step_steps: int | None = None
    step_menu: list[Move] = []
    move_steps: int | None = None
    move_buf: list[str] = []

    in_screen = False
    screen_segs: list = []
    screen_lineno = 0

    def flush_peg():
        nonlocal peg_off, peg_buf
        if peg_off is not None:
            pegs.append(Peg(peg_off, "\n".join(peg_buf), peg_label))
        peg_off, peg_buf = None, []

    def flush_move():
        nonlocal move_steps, move_buf
        if move_steps is not None and "\n".join(move_buf).strip():
            step_menu.append(Move("\n".join(move_buf), move_steps))
        move_steps, move_buf = None, []

    for i, raw in enumerate(text.splitlines(), 1):
        d = _directive(raw)

        if d is None:                       # content line (asm or blank/comment)
            if tmpl_name is not None and peg_off is not None and raw.strip():
                peg_buf.append(raw.rstrip())
            elif in_work and raw.strip():
                work_buf.append(raw.rstrip())
            elif in_step and move_steps is not None and raw.strip():
                move_buf.append(raw.rstrip())
            continue

        name, args = d
        if name == "template":
            if tmpl_name is not None or in_work or in_step or in_screen:
                raise ScheduleError(f"line {i}: ;@template cannot nest")
            if not args:
                raise ScheduleError(f"line {i}: ;@template needs a name")
            tmpl_name = args[0]
            tmpl_len = _int(args[1], i, "line_len") if len(args) > 1 else 512
            pegs, peg_off, peg_buf = [], None, []

        elif name == "peg":
            if tmpl_name is None:
                raise ScheduleError(f"line {i}: ;@peg outside ;@template")
            if not args:
                raise ScheduleError(f"line {i}: ;@peg needs an offset")
            flush_peg()
            peg_off = _int(args[0], i, "peg offset")
            peg_label = " ".join(a for a in args[1:] if "=" not in a)

        elif name in ("endtemplate", "template_end"):
            if tmpl_name is None:
                raise ScheduleError(f"line {i}: ;@{name} without ;@template")
            flush_peg()
            if not pegs:
                raise ScheduleError(f"line {i}: template {tmpl_name!r} has no pegs")
            templates[tmpl_name] = LineTemplate(pegs, tmpl_len)
            tmpl_name = None

        elif name == "work":
            if in_work or in_step or tmpl_name is not None or in_screen:
                raise ScheduleError(f"line {i}: ;@work cannot nest")
            work_name = _kw(args, "name")
            if work_name is None and stepwork is not None:
                raise ScheduleError(f"line {i}: use either ;@work or ;@stepwork, not both")
            in_work = True
            work_split = "split" in (a.lower() for a in args)
            rep = _kw(args, "repeat")
            work_repeat = _int(rep, i, "repeat") if rep is not None else 1
            bm = _kw(args, "beam")                  # beam=lo:hi -> placement window
            if bm is not None:
                try:
                    lo, hi = (_int(x, i, "beam") for x in bm.split(":", 1))
                except ValueError:
                    raise ScheduleError(f"line {i}: ;@work beam= must be lo:hi, got {bm!r}")
                work_beam = (lo, hi)
            else:
                work_beam = None
            work_buf = []

        elif name in ("endwork", "work_end"):
            if not in_work:
                raise ScheduleError(f"line {i}: ;@{name} without ;@work")
            asm = "\n".join(work_buf)
            if asm.strip():
                if work_name is not None:
                    tgt = works.setdefault(work_name, WorkStream([]))
                    if not isinstance(tgt, WorkStream):
                        raise ScheduleError(f"line {i}: work {work_name!r} already a stepwork")
                else:
                    tgt = stream
                for _ in range(work_repeat):
                    tgt.blocks.append(WorkBlock(asm, work_split, beam=work_beam))
            in_work, work_name = False, None

        elif name == "stepwork":
            if in_work or in_step or tmpl_name is not None or in_screen:
                raise ScheduleError(f"line {i}: ;@stepwork cannot nest")
            step_name = _kw(args, "name")
            if step_name is None and (stepwork is not None or stream.blocks):
                raise ScheduleError(f"line {i}: use either ;@work or ;@stepwork, not both")
            st = _kw(args, "steps") or next((a for a in args if "=" not in a), None)
            if st is None:
                raise ScheduleError(f"line {i}: ;@stepwork needs steps=<n>")
            in_step = True
            step_steps = _int(st, i, "steps")
            step_menu, move_steps, move_buf = [], None, []

        elif name == "move":
            if not in_step:
                raise ScheduleError(f"line {i}: ;@move outside ;@stepwork")
            if not args:
                raise ScheduleError(f"line {i}: ;@move needs a step count")
            flush_move()
            move_steps = _int(args[0], i, "move steps")

        elif name in ("endstepwork", "stepwork_end"):
            if not in_step:
                raise ScheduleError(f"line {i}: ;@{name} without ;@stepwork")
            flush_move()
            if not step_menu:
                raise ScheduleError(f"line {i}: ;@stepwork has no ;@move entries")
            sw = StepWork(step_steps, step_menu)
            if step_name is not None:
                works[step_name] = sw
            else:
                stepwork = sw
            in_step, step_name = False, None

        elif name == "screen":
            if in_work or in_step or tmpl_name is not None or in_screen:
                raise ScheduleError(f"line {i}: ;@screen cannot nest")
            in_screen, screen_segs, screen_lineno = True, [], i

        elif name == "segment":
            if not in_screen:
                raise ScheduleError(f"line {i}: ;@segment outside ;@screen")
            if not args:
                raise ScheduleError(f"line {i}: ;@segment needs a template name")
            seg_lines = _kw(args, "lines")
            if seg_lines is None:
                raise ScheduleError(f"line {i}: ;@segment needs lines=<n>")
            screen_segs.append((args[0], _kw(args, "work"), _int(seg_lines, i, "lines")))

        elif name in ("endscreen", "screen_end"):
            if not in_screen:
                raise ScheduleError(f"line {i}: ;@{name} without ;@screen")
            if not screen_segs:
                raise ScheduleError(f"line {i}: ;@screen has no ;@segment entries")
            items.append(("screen", screen_segs, screen_lineno))
            in_screen = False

        elif name == "schedule":
            if tmpl_name is not None or in_work or in_step or in_screen:
                raise ScheduleError(f"line {i}: ;@schedule inside a block")
            if not args:
                raise ScheduleError(f"line {i}: ;@schedule needs a template name")
            nlines = _kw(args, "lines")
            if nlines is None:
                raise ScheduleError(f"line {i}: ;@schedule needs lines=<n>")
            items.append(("single", args[0], _int(nlines, i, "lines"), i))

        # unknown ;@names are ignored (forward-compat, matches preprocess.expand)

    if tmpl_name is not None:
        raise ScheduleError("unterminated ;@template (missing ;@endtemplate)")
    if in_work:
        raise ScheduleError("unterminated ;@work (missing ;@endwork)")
    if in_step:
        raise ScheduleError("unterminated ;@stepwork (missing ;@endstepwork)")
    if in_screen:
        raise ScheduleError("unterminated ;@screen (missing ;@endscreen)")
    return ParsedSpec(templates, stepwork if stepwork is not None else stream, works, items)


def _resolve_segments(spec: ParsedSpec, segs, lineno) -> list:
    """Resolve ('template-name', 'work-name'|None, n_lines) into (LineTemplate, work, n)."""
    out = []
    for tname, wname, n in segs:
        if tname not in spec.templates:
            raise ScheduleError(f"line {lineno}: ;@segment of unknown template {tname!r}")
        if wname is None:
            work = WorkStream([])                       # border-only line
        elif wname in spec.works:
            work = spec.works[wname]
        else:
            raise ScheduleError(f"line {lineno}: ;@segment references unknown work {wname!r}")
        out.append((spec.templates[tname], work, n))
    return out


def expand_schedule(text: str, engine: CycleEngine | None = None) -> str:
    """Parse a spec and emit the packed routine(s) — the directive front-end's output."""
    engine = engine or CycleEngine()
    spec = parse(text)
    if not spec.items:
        raise ScheduleError("no ;@schedule or ;@screen directive — nothing to emit")

    out: list[str] = []
    for item in spec.items:
        if item[0] == "single":
            _, tname, nlines, lineno = item
            if tname not in spec.templates:
                raise ScheduleError(f"line {lineno}: ;@schedule of unknown template {tname!r}")
            try:
                res = pack(spec.templates[tname], spec.default_work, nlines, engine=engine)
            except PackError as e:
                raise ScheduleError(f"line {lineno}: {e}") from e
            out.append(f"; === lockstep: {tname} x{nlines} lines "
                       f"({res.units_placed}/{res.units_total} work units) ===")
        else:
            _, segs, lineno = item
            segments = _resolve_segments(spec, segs, lineno)
            try:
                res = pack_schedule(segments, engine=engine)
            except PackError as e:
                raise ScheduleError(f"line {lineno}: {e}") from e
            out.append(f"; === lockstep screen: {len(segments)} segment(s), "
                       f"{res.n_lines} lines ===")
        out.append(res.asm.rstrip("\n"))
    return "\n".join(out) + "\n"
