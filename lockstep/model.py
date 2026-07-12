"""Lockstep scheduler — the input data model (DESIGN §7.1).

These are pure *declarations of intent*: a `LineTemplate` nails the border events to
cycle offsets in the 512c grid, a `WorkStream` is the effect logic to pour into the gaps.
Cost is never stored here — it is derived on demand from the `st68k` engine, so the same
template/stream can be re-timed under a different machine profile without edits.

Both the Python front-end and the future `;@`-directive front-end build these objects and
hand them to `packer.pack()`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def _asm_lines(asm: str) -> list[str]:
    """Split an asm fragment into non-blank source lines (comments/labels kept verbatim)."""
    return [ln.rstrip() for ln in asm.splitlines() if ln.strip()]


@dataclass
class Peg:
    """A fixed hardware event nailed to a cycle within the line.

    `offset` is the CPU-execution cycle — the running count from the start of the line at
    which `asm` begins. The tool does not model the shifter latch; the author supplies the
    offset from the border idiom / TIMING.md (e.g. the right-border 60/50 Hz toggle at the
    cycle the shifter checks the right-edge stop). `asm` may be several instructions.
    """

    offset: int
    asm: str
    label: str = ""
    reserve: int | None = None
    """If set, the peg occupies exactly this many cycles in the layout — a worst-case budget
    for a variable-cost call (a sound replay, DESIGN §8; size it from
    `lockstep.sound.profile_play(...).reserve`). The packer reserves the slot and pours no
    work into the headroom. Runtime constancy (the call actually taking the full budget) is
    the author's: a worst-case-padded player, or a beam-wait to the slot end — Lockstep
    reserves the budget; it can't make a variable call constant-time for you."""

    def lines(self) -> list[str]:
        return _asm_lines(self.asm)


@dataclass
class LineTemplate:
    """The reusable 'all borders open' grid: pegs within a line of `line_len` cycles.

    The same template instance is reused across every scanline of a scheduled region; it
    is data, defined once per border idiom (DESIGN §7.1).
    """

    pegs: list[Peg]
    line_len: int = 512

    def sorted_pegs(self) -> list[Peg]:
        return sorted(self.pegs, key=lambda p: p.offset)


@dataclass
class WorkBlock:
    """One block of effect logic in the work stream.

    The stream is always splittable *between* blocks — that is the packer's main freedom.
    `splittable` controls splitting *within* a block: True means the block's instruction
    lines may be cut at any boundary (the author asserts no live timing dependency across
    the cut); False (default) means the block is atomic — placed whole or pushed to the
    next gap. A scroller *column* (`move.l 8(a6),(a6)+` / `addq #4,a6`) is one atomic
    block; the stream of columns splits freely between them.
    """

    asm: str
    splittable: bool = False
    label: str = ""
    beam: tuple[int, int] | None = None
    """Optional beam-race window `(lo, hi)` in line cycles (DESIGN §1.3.2, §7.1). The block
    writes something the shifter is about to display (a palette/screen word), so it produces
    correct pixels only when executed within this cycle window — a *placement* constraint, not
    a cost. The packer places the block only where it runs inside `[lo, hi]` (padding up to
    `lo` if needed) and errors if no gap can host it; `lo=0` is just a deadline `hi`. Verify
    with Hatari's beam counter (LineCycles)."""

    def lines(self) -> list[str]:
        return _asm_lines(self.asm)


@dataclass
class Segment:
    """One vertical band of a screen for `packer.pack_schedule`: `n_lines` scanlines of one
    `template`, fed by one `work` (a WorkStream, a StepWork, or an empty WorkStream for a
    border-only line). Bands with different templates model the top/bottom-border lines that
    differ from mid-screen (DESIGN §7.1)."""

    template: "LineTemplate"
    work: "WorkStream | StepWork"
    n_lines: int


@dataclass
class Move:
    """One granularity of a step-budgeted work menu (DESIGN §7.2, the move.l/move.w trick).

    `asm` is a self-contained step (it does its data op AND its own pointer advance, so the
    packer may emit any count in any order); `steps` is how much of the work budget it
    covers (e.g. bytes shifted); `cost` is its cycle cost — left None to derive from the
    `st68k` engine (the common case: don't hand-count). The solver currently requires
    phase-stable moves (cost a multiple of 4).
    """

    asm: str
    steps: int
    cost: int | None = None
    label: str = ""

    def lines(self) -> list[str]:
        return _asm_lines(self.asm)


@dataclass
class StepWork:
    """A fixed amount of work (`steps`) to cover with a menu of differently-sized `Move`s.

    The packer's exact-cover solver chooses how many of each move to emit so the total
    steps land EXACTLY on `steps` while every scanline closes to 512c — turning what a
    whole-unit pour would waste as `nop` filler into useful work (the move.l/move.w mix in
    aurora.s:850). `per_line` True (default) means `steps` is per scanline (the scroller
    case: shift the whole buffer every line); a global budget across lines is a follow-up.
    """

    steps: int
    menu: list[Move]
    per_line: bool = True


@dataclass
class WorkStream:
    """An ordered sequence of work blocks, consumed front-to-back by the packer."""

    blocks: list[WorkBlock] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.blocks)

    @classmethod
    def repeat(cls, asm: str, n: int, *, splittable: bool = False,
               label: str = "") -> "WorkStream":
        """`n` copies of one asm fragment as a stream of atomic blocks (the common case:
        a fixed per-iteration unit like a scroller column). Pass `splittable=True` only if
        the fragment itself may be cut mid-block."""
        return cls([
            WorkBlock(asm, splittable, f"{label}{i}" if label else "")
            for i in range(n)
        ])

    @classmethod
    def concat(cls, *streams: "WorkStream") -> "WorkStream":
        out: list[WorkBlock] = []
        for s in streams:
            out.extend(s.blocks)
        return cls(out)
