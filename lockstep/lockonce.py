"""Lockstep — lock once, then count: an overscan frame with no interrupts after the first VBL.

`OverscanFrame.build` runs every frame as a VBL handler that re-locks to the beam (the `$8209`
poll). `LockOnceFrame` locks once, in the first VBL, masks every interrupt for good (`sr=$2700`,
never an `rte`) and then runs one endless loop that costs exactly one frame:

    __band0:  the bands: n_lines x line_len            (border switches + your band work)
              the tail: everything else, padded        (your per-frame work, `tail`)
              the top-border dance                     (60/50 Hz, same instructions as VBL mode)
              the post region: `post`, border-register reload, exit test, jmp __band0

Every frame is the previous one shifted by exactly `FRAME_CYCLES`, so the beam position of every
instruction is fixed for the life of the program. Consequences:

  * No VBL-entry jitter, no lock poll, no handler wrap: the tail gets ~26.5k cycles per frame,
    padded to the cycle, where VBL mode has ~8.6k of tail plus a 17k pause.
  * The video base can move every frame (STE hardware scroll) without disturbing the sync: there
    is no per-frame lock to be fooled by the base's low byte (see `SyncConfig.base_aware`).
  * The cost: EVERYTHING in the loop must be constant-cost, as `pre` already had to be (branches
    in `;@balance`, no data-dependent instructions). One cycle of error per frame accumulates
    for ever; the build refuses a tail that does not fit. No interrupt-driven code anywhere:
    music must be a constant-cost YM engine in the bands or the tail.
  * No ACIA access in the loop: its E-clock sync makes the cost vary frame to frame. The exit test
    reads the MFP's GPIP bit 4 instead (the keyboard ACIA's interrupt line, low while a byte waits;
    a fixed +4c MFP access): any key, mouse or joystick byte ends the program.

Placement is measured, not derived. In VBL mode (Hatari 2.6.1, ST and STE, `DEFAULT_SYNC`, the
standard band stack) `__band0` starts at frame cycle 17916 every frame, and the first dance `eor`
at 17340..17348 (STE) / 17336..17344 (ST), moving with the 0..8c VBL-entry jitter. The loop puts
the dance `DANCE_TO_BAND0` = 572 cycles before `__band0`: inside both machines' working sets.
Tolerance, measured on the STE (dance swept in 4c steps, 200-frame border census): every
placement from 544 to 596 cycles before band 0 opens the borders, 540 and 600 lose every frame.
572 sits 28c from one edge and 24c from the other. Re-measure if the sync config or the band
stack changes (`examples/lockonce`: LOCKONCE_D2B).
"""

from __future__ import annotations

from st68k.annotate import block_cycles

from .model import WorkStream
from .program import build_tos, emit_program
from .skeleton import DEFAULT_SYNC, OverscanFrame, SyncConfig

FRAME_CYCLES = 313 * 512          # one PAL 50 Hz frame: 160256
DANCE_TO_BAND0 = 572              # see the module docstring

# Border switch registers the bands expect (set by the lock in frame 1; reloaded every frame).
_RELOAD = """\
    lea     $ffff8260,a1        ; a1 = resolution reg (left-border switch)
    move.w  #$820a,a0           ; a0 = sync-mode reg (right-border switch)
    moveq   #2,d3
    moveq   #0,d4
"""

# Exit test: MFP GPIP bit 4 is the keyboard ACIA's interrupt line (active low: a byte waits).
# Branchless: pick the jump target from a table, constant cost.
_EXIT_SELECT = """\
    moveq   #0,d0
    move.b  $fffffa01,d0        ; MFP GPIP (+4c): bit 4 low = the keyboard ACIA holds a byte
    and.w   #$10,d0
    lsr.w   #2,d0               ; 0 = a byte waits -> exit, 4 = carry on
    lea     __lo_next,a2
    move.l  (a2,d0.w),a2
"""

# Setup prefix: remember the main program's stack (the exit path returns to it), and, with the
# exit test on, drain the keyboard ACIA until it has been quiet for ~0.25 s, so the release of the
# key that launched the program does not end it at once. Untimed: runs before the VBL is armed.
_SETUP_SP = "    move.l  sp,__lo_sp          ; the exit path returns to this stack\n"
_SETUP_QUIET = """\
    lea     $fffffc00,a0        ; drain the keyboard ACIA until it is quiet for ~0.25 s
    move.l  #40000,d1
__lo_q:
    btst    #0,(a0)
    beq.s   __lo_nq
    move.b  2(a0),d0            ; discard
    move.l  #40000,d1
__lo_nq:
    subq.l  #1,d1
    bne.s   __lo_q
"""

# main: idle in `stop` until the first VBL; the frame never returns.
_MAIN = """\
__lo_idle:
    stop    #$2300               ; the first VBL enters the frame, which never returns
    bra.s   __lo_idle"""

_EXIT = """\
__lo_exit:                       ; leave the loop: back on main's stack, TOS's VBL, interrupts on
    move.l  __lo_sp,sp
    move.l  __oldvbl,$70.w
    move.w  #$2300,sr
    jmp     __exit
    even
__lo_next:
    dc.l    __lo_exit,__band0
__lo_sp:
    dc.l    0
"""


def _expand(region: str, budget: int, what: str) -> str:
    from st68k.preprocess import PreprocessError, expand
    spec = f";@sync\n;@budget {budget}\n{region.rstrip(chr(10))}\n;@end\n"
    try:
        out, _ = expand(spec)
    except PreprocessError as e:
        raise ValueError(f"{what} does not fit its {budget}c: {e}\nEvery frame of a lock-once "
                         f"loop must cost exactly {FRAME_CYCLES}c; branches must be wrapped in "
                         f";@balance.") from None
    return out.rstrip("\n") + "\n"


class LockOnceFrame(OverscanFrame):
    """An `OverscanFrame` that syncs once and then counts (see the module docstring). Takes the
    same band arguments; `pre` is not available (there is no pause region: use `tail`).

    `dance_to_band0` places the top-border dance (cycles from its first `eor` to `__band0`);
    `exit_on_key` adds the MFP-based exit test to every frame."""

    def __init__(self, *, dance_to_band0: int = DANCE_TO_BAND0, exit_on_key: bool = True,
                 sync: SyncConfig = DEFAULT_SYNC, **kw):
        if kw.get("pre"):
            raise ValueError("LockOnceFrame has no pause region: put per-frame work in `tail`")
        if sync.coarse != "none":
            raise ValueError("LockOnceFrame needs the $8209 lock (coarse='none')")
        super().__init__(sync=sync, **kw)
        if dance_to_band0 % 4:
            raise ValueError("dance_to_band0 must be a multiple of 4 cycles")
        self.dance_to_band0 = dance_to_band0
        self.exit_on_key = exit_on_key

    @property
    def dance(self) -> str:
        """The top-border 60/50 Hz dance, as in `SyncConfig._prelude`."""
        g = self.sync.dance_gap
        return ("__lo_dance:\n"
                "    eor.b   #2,$ffff820a        ; 60 Hz: the top-border pulse\n"
                f"    rept {g}\n    nop\n    endr\n"
                "    eor.b   #2,$ffff820a        ; back to 50 Hz\n")

    @property
    def dance_cycles(self) -> int:
        return block_cycles(self.dance)[1]

    def n_lines(self, upper: WorkStream | None = None, lower: WorkStream | None = None) -> int:
        return self.bands(upper=upper, lower=lower).n_lines

    def tail_budget(self, upper: WorkStream | None = None,
                    lower: WorkStream | None = None) -> int:
        """Cycles per frame for `tail`: the frame minus the bands and the dance-to-band0 run."""
        return FRAME_CYCLES - self.n_lines(upper, lower) * self.line_len - self.dance_to_band0

    def frame_body(self, *, upper: WorkStream | None = None, lower: WorkStream | None = None,
                   tail: str = "", pre: str | None = None, post: str | None = None) -> str:
        if pre:
            raise ValueError("LockOnceFrame has no pause region: put per-frame work in `tail`")
        post = self.post if post is None else post
        bands = self.bands(upper=upper, lower=lower)
        lines = bands.n_lines * self.line_len
        tail_budget = FRAME_CYCLES - lines - self.dance_to_band0
        post_budget = self.dance_to_band0 - self.dance_cycles
        loop_post = (post.rstrip("\n") + "\n" if post.strip() else "") + _RELOAD
        if self.exit_on_key:
            loop_post += _EXIT_SELECT + ";@fill\n    jmp     (a2)\n"
        else:
            loop_post += ";@fill\n    jmp     __band0\n"
        return (
            # frame 1: the VBL-mode prelude and lock, entered from the VBL (emit_program's
            # handler prologue is the same as VBL mode's, so the frame-1 dance lands as usual)
            self.sync.asm("", post)
            + "\n" + bands.asm
            + "* ---- lock-once loop: the tail, padded to the cycle ----\n"
            + _expand((tail.rstrip("\n") + "\n" if tail.strip() else "") + ";@fill\n",
                      tail_budget, "the lock-once tail")
            + self.dance
            + "* ---- post: band registers, exit test, back to band 0 ----\n"
            + _expand(loop_post, post_budget, "the lock-once post region"))

    def build(self, out_path: str, *, setup: str = "", extra: str = "",
              upper: WorkStream | None = None, lower: WorkStream | None = None,
              tail: str = "", pre: str | None = None, post: str | None = None,
              exit_on_key: bool | None = None, **emit_kw) -> str:
        """Assemble a standalone lock-once `.TOS`. `setup` runs once with interrupts on (MFP
        masked, as in VBL mode); `extra` is appended after the program."""
        if exit_on_key is not None:
            self.exit_on_key = exit_on_key
        for k in ("main", "idle", "mask"):
            if k in emit_kw:
                raise ValueError(f"LockOnceFrame.build owns `{k}`")
        body = self.frame_body(upper=upper, lower=lower, tail=tail, pre=pre, post=post)
        prefix = _SETUP_SP + (_SETUP_QUIET if self.exit_on_key else "")
        src = emit_program(body, setup=prefix + setup, extra=_EXIT + extra, main=_MAIN,
                           mask=True, **emit_kw)
        return build_tos(src, out_path)
