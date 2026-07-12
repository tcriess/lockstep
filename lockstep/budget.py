"""Lockstep — the frame-level cost model: the slack / VBL-jitter safety net.

`st68k` costs *lines*; the packer proves every scanline is 512c. But a full-sync demo is more
than its display bands: after the borders are busted, the VBL handler runs a **post-display tail**
(palette pointer fills, the sound replay, per-frame churn — the work a demo defers to "the VBL
after the display"), and that tail competes for the frame's *slack* — the cycles left
over after the skeleton. Nothing costed it, and nothing related growing it to the thing it breaks:
if the tail eats the slack, the handler overruns toward the next VBL, the eor-dance top-removal
lands past the wakestate margin, and **the top border silently closes**. That exact regression
(≈672c of added per-frame work) bit this project and was invisible to the toolkit — found only by
hand bisection. This module makes it a *build-time* number and warning, before Hatari is ever run.

The model (all static, per PAL frame = 160256c):

    frame_cycles = machine.cycles_per_frame                     # 160256 (313 lines x 512c)
    skeleton     = handler_wrap + prelude + bands               # the border mechanism's fixed cost
      handler_wrap : sr push/pop + movem save/restore + rte     (~300c)
      prelude      : the sync (pause loop 16N+28 + eor-dance + $8209 lock + first_line) + a bounded
                     beam-wait (the $8209 poll is runtime, <= one line; counted conservatively)
      bands        : n_lines x line_len                         (260 x 512 = 133120c, exact)
    slack_budget = frame_cycles - skeleton                      (~8600c for the standard frame)

The author's per-frame **tail** work is accounted against `slack_budget`. Warnings:
  - tail > slack            -> OVER: the handler overruns the frame; the borders WILL close;
  - tail > slack - margin   -> RISK: within the VBL-entry-jitter margin of closing the top border.

**Reserve data-dependent tails.** A tail whose cost varies frame-to-frame (a sound replay, a
conditional churn) must be budgeted at its WORST case, never left to vary — reuse
`sound.profile_play`'s `PlayEnvelope.reserve`. `FrameBudget.check(tail_cost=env.reserve)` accounts
the worst case; a tail that fits on its cheap frames but not its dear ones is exactly the
intermittent border flicker the emulator can only catch on the dear frame.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from st68k.annotate import block_cycles
from st68k.cycles import STF_PAL, CycleEngine, Machine

# The VBL-entry-jitter margin: below this much free slack the handler runs close enough to the
# next VBL that the wakestate margin (0-3c) + tail variability can shift the eor-dance top-removal
# off its line. ~20c flips the top border (TIMING.md); default to a conservative buffer above it.
DEFAULT_JITTER_MARGIN = 64

# A conservative upper bound for the runtime `$8209` beam-wait poll in the sync prelude (it waits
# for the video low byte to tick, at most ~one scanline). Counted into the skeleton so slack is
# not over-stated.
DEFAULT_BEAM_WAIT = 512

# The VBL-handler wrapper emit_program wraps every frame in: save sr, mask, movem.l d0-d7/a0-a6
# to/from the stack, restore sr, rte. Costed once (bus-phase accurate) as a fixed overhead.
_HANDLER_WRAP_ASM = """\
    move.w  sr,-(sp)
    or.w    #$0700,sr
    movem.l d0-d7/a0-a6,-(sp)
    movem.l (sp)+,d0-d7/a0-a6
    move.w  (sp)+,sr
    rte
"""


def _pause_loop_cost(n: int) -> int:
    """The static VBL-entry pause loop `move.w #n,d0 / .p: nop / dbra d0,.p`: 16n+28 cycles
    (n+1 nops @4c, n taken dbra @12c + 1 expiring @16c, + the move.w @8c). ~17052c at n=1064."""
    return 16 * n + 28


# what block_cycles charges the 3 pause lines as a single straight-line pass (so we can replace it
# with the real looped cost); computed once at import.
_PAUSE_ONE_PASS = block_cycles("    move.w  #1,d0\n.p:\n    nop\n    dbra    d0,.p\n")[1]
_HANDLER_WRAP = block_cycles(_HANDLER_WRAP_ASM)[1]


def _prelude_cost(sync, *, beam_wait: int = DEFAULT_BEAM_WAIT, engine=None) -> int:
    """Static cost of the sync prelude (`SyncConfig.asm()`): its straight-line body (eor-dance,
    the `$8209` lock spacers, the `dcb.w first_line` fill) plus the real pause-loop cost and a
    bounded beam-wait. block_cycles counts the pause dbra as a single pass; swap in the loop."""
    straight = block_cycles(sync.asm(), engine)[1]
    return straight - _PAUSE_ONE_PASS + _pause_loop_cost(sync.pause) + beam_wait


@dataclass
class FrameBudget:
    """The per-frame cost account for an overscan frame. `skeleton` is the border mechanism's
    fixed cost (handler wrap + sync prelude + bands); `slack_budget` is what's left of the frame
    for the author's post-display tail. `check()` accounts a tail against it."""
    machine: Machine
    n_lines: int
    line_len: int
    handler_wrap: int
    prelude: int
    beam_wait: int
    jitter_margin: int
    tail_cost: int = 0
    tail_reserved: bool = True
    warnings: list[str] = field(default_factory=list)

    @property
    def bands(self) -> int:
        return self.n_lines * self.line_len

    @property
    def skeleton(self) -> int:
        return self.handler_wrap + self.prelude + self.bands

    @property
    def slack_budget(self) -> int:
        """Free cycles per frame after the skeleton — the budget for the post-display tail."""
        return self.machine.cycles_per_frame - self.skeleton

    @property
    def slack_after_tail(self) -> int:
        return self.slack_budget - self.tail_cost

    @property
    def ok(self) -> bool:
        return not self.warnings

    def check(self, *, tail_cost: int = 0, reserved: bool = True) -> "FrameBudget":
        """Account `tail_cost` cycles of per-frame post-display work against the slack, populating
        `warnings`. `reserved=False` flags a data-dependent tail that isn't worst-cased. Returns
        self so it chains."""
        self.tail_cost = tail_cost
        self.tail_reserved = reserved
        self.warnings = []
        slack, margin = self.slack_budget, self.jitter_margin
        if tail_cost > slack:
            self.warnings.append(
                f"OVER budget: post-display tail is {tail_cost}c but only {slack}c of frame slack "
                f"remains ({tail_cost - slack}c over) — the VBL handler overruns the frame and the "
                f"borders WILL close. Move work into the display bands, or cut {tail_cost - slack}c.")
        elif tail_cost > slack - margin:
            self.warnings.append(
                f"RISK: post-display tail is {tail_cost}c, within the {margin}c VBL-entry-jitter "
                f"margin of the {slack}c slack ({self.slack_after_tail}c free) — likely to shift the "
                f"eor-dance top-removal past the wakestate margin and close the TOP border. Verify "
                f"on all wakestates (lockstep.wakestate.verify_overscan) or cut it back.")
        if not reserved and tail_cost:
            self.warnings.append(
                f"UNRESERVED: this {tail_cost}c tail is data-dependent — budget its WORST case "
                f"(sound.profile_play(...).reserve), not a typical frame, or it will fit on cheap "
                f"frames and close the border on the dear one (intermittent flicker).")
        return self

    def report(self) -> str:
        f = self.machine.cycles_per_frame
        out = [f"frame budget ({self.machine.name}, {f}c/frame):",
               f"  skeleton     {self.skeleton:>7}c  = wrap {self.handler_wrap} + prelude "
               f"{self.prelude} + bands {self.bands} ({self.n_lines}x{self.line_len})",
               f"  slack budget {self.slack_budget:>7}c  (free for the post-display tail)"]
        if self.tail_cost:
            out.append(f"  tail         {self.tail_cost:>7}c  -> {self.slack_after_tail}c free "
                       f"after tail")
        for w in self.warnings:
            out.append(f"  !! {w}")
        if self.ok:
            out.append("  => within budget" + (f" ({self.slack_after_tail}c to spare)"
                                               if self.tail_cost else ""))
        return "\n".join(out)


def frame_budget(frame, *, machine: Machine = STF_PAL, beam_wait: int = DEFAULT_BEAM_WAIT,
                 jitter_margin: int = DEFAULT_JITTER_MARGIN, engine: CycleEngine | None = None,
                 tail: str = "", tail_cost: int | None = None, reserved: bool = True,
                 upper=None, lower=None) -> FrameBudget:
    """Build the per-frame cost account for an `OverscanFrame` (or any object exposing `.sync`,
    `.line_len`, and a `.bands(upper,lower)` whose result has `.n_lines`).

    `tail` is the post-display per-frame asm to account (costed with `block_cycles`); or pass
    `tail_cost` directly (e.g. `profile_play(...).reserve` for a sound replay). `reserved=False`
    flags a data-dependent tail. Returns a `FrameBudget` with `.slack_budget` and `.warnings`."""
    engine = engine or CycleEngine(machine=machine)
    res = frame.bands(upper=upper, lower=lower)
    prelude = _prelude_cost(frame.sync, beam_wait=beam_wait, engine=engine)
    fb = FrameBudget(machine=machine, n_lines=res.n_lines, line_len=frame.line_len,
                     handler_wrap=_HANDLER_WRAP, prelude=prelude, beam_wait=beam_wait,
                     jitter_margin=jitter_margin)
    if tail_cost is None:
        tail_cost = block_cycles(tail, engine)[1] if tail.strip() else 0
    return fb.check(tail_cost=tail_cost, reserved=reserved)


def assert_within_budget(frame, *, allow_risk: bool = False, **kw) -> FrameBudget:
    """Build-time / pytest guard: account a frame's tail and raise AssertionError (with the report)
    if it is OVER budget — or, unless `allow_risk`, within the VBL-entry-jitter margin. Mirrors
    `lockstep.wakestate.assert_overscan_open`; use it to fail a build the instant added per-frame
    work would close the borders, before Hatari is ever run."""
    fb = frame_budget(frame, **kw)
    fatal = [w for w in fb.warnings
             if allow_risk and w.startswith(("OVER", "UNRESERVED")) or not allow_risk]
    if fatal:
        raise AssertionError("frame over budget:\n" + fb.report())
    return fb
