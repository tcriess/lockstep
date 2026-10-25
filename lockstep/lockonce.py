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

# The loop's last instructions pick where to go: band 0, the exit, or (debug check) the halt.
# Branchless, constant cost. d0 = table index, d6 = the check's error mask (-1 = drifted).
_KEY_INDEX = """\
    moveq   #0,d0
    move.b  $fffffa01,d0        ; MFP GPIP (+4c): bit 4 low = the keyboard ACIA holds a byte
    and.w   #$10,d0
    lsr.w   #2,d0               ; 0 = a byte waits -> exit, 4 = carry on
"""
_ERR_INDEX = """\
    move.w  d6,d1               ; a failed check wins: index 8, the halt
    and.w   #8,d1
    not.w   d6
    and.w   d6,d0
    or.w    d1,d0
"""
_JUMP = """\
    lea     __lo_next,a2
    move.l  (a2,d0.w),a2
    jmp     (a2)
"""


def _check(base_low: str | None) -> str:
    """Debug check: the video counter's low byte at the same cycle of every frame must equal the
    first frame's. `base_low` (a RAM mirror of the base low byte, or $ffff820d on an STE) is
    subtracted, so a moving base does not trip it. Leaves the sticky error mask in d6."""
    sub = (f"    moveq   #0,d5\n    move.b  {base_low},d5\n    sub.w   d5,d6\n    and.w   #$ff,d6\n"
           if base_low else "")
    return f"""\
    moveq   #0,d6
    move.b  $ffff8209,d6        ; video counter low byte, at the same cycle every frame
{sub}    move.w  __lo_ref,d1         ; -1 until the first frame has stored its value
    move.w  d1,d2
    add.w   d2,d2
    subx.w  d2,d2               ; -1 while unset
    move.w  d1,d5
    eor.w   d6,d5
    and.w   d2,d5
    eor.w   d5,d1               ; ref = unset ? this frame's value : ref
    move.w  d1,__lo_ref
    sub.w   d6,d1
    neg.w   d1
    subx.w  d1,d1               ; -1 iff this frame differs
    or.w    __lo_err,d1
    move.w  d1,__lo_err         ; sticky
    move.w  d1,d6
"""


def _ikbd(cmds: list[int], tag: str) -> str:
    """Send IKBD commands (untimed: setup and exit only)."""
    out = []
    for i, c in enumerate(cmds):
        out.append(f"__lo_tx{tag}{i}:\n    btst    #1,$fffffc00\n    beq.s   __lo_tx{tag}{i}\n"
                   f"    move.b  #${c:02x},$fffffc02")
    return "\n".join(out) + "\n"


IKBD_QUIET = [0x12, 0x1a]       # mouse off, joystick off: only keys reach the ACIA
IKBD_RESTORE = [0x14, 0x08]     # joystick event reporting, THEN relative mouse: a joystick mode
                                #   takes port 0 from the mouse, a mouse mode gives it back (TOS order)

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


def _exit_code(ikbd: bool) -> str:
    return f"""\
__lo_exit:                       ; leave the loop: back on main's stack, TOS's VBL, interrupts on
    move.l  __lo_sp,sp
{_ikbd(IKBD_RESTORE, "x") if ikbd else ""}\
    move.l  __oldvbl,$70.w
    move.w  #$2300,sr
    jmp     __exit
__lo_halt:                       ; the debug check failed: red border, no more counting; a key exits
    move.w  #$700,$ffff8240
    btst    #4,$fffffa01
    bne.s   __lo_halt
    jmp     __lo_exit
    even
__lo_next:
    dc.l    __lo_exit,__band0,__lo_halt
__lo_sp:
    dc.l    0
__lo_ref:
    dc.w    -1
__lo_err:
    dc.w    0
"""


def _expand(region: str, budget: int, what: str) -> str:
    from st68k.preprocess import PreprocessError, expand
    spec = f";@sync\n;@budget {budget}\n{region.rstrip(chr(10))}\n;@end\n"
    try:
        out, _ = expand(spec)
    except PreprocessError as e:
        raise ValueError(f"{what} does not fit its {budget}c: {e}\nEvery frame of a lock-once "
                         f"loop must cost exactly one frame; branches must be wrapped in "
                         f";@balance.") from None
    return out.rstrip("\n") + "\n"


class LockOnceFrame(OverscanFrame):
    """An `OverscanFrame` that syncs once and then counts (see the module docstring). Takes the
    same band arguments; `pre` is not available (there is no pause region: use `tail`).

    `dance_to_band0`  where the top-border dance sits (cycles from its first `eor` to `__band0`).
    `exit_on_key`     test MFP GPIP bit 4 every frame; a waiting IKBD byte ends the program.
    `ikbd_quiet`      with the exit test: mouse and joystick reporting off for the loop (only keys
                      exit), restored on exit.
    `check`           debug build: compare the video counter at a fixed cycle every frame with the
                      first frame's; on a mismatch, halt with a red border (a key still exits).
    `check_base`      a byte holding the video base's low byte, subtracted before comparing (a RAM
                      mirror; `$ffff820d` on an STE-only program). None = the base never moves.
    `frame_cycles`    the loop length. Anything but 160256 drifts: it exists to test `check`."""

    def __init__(self, *, dance_to_band0: int = DANCE_TO_BAND0, exit_on_key: bool = True,
                 ikbd_quiet: bool = True, check: bool = False, check_base: str | None = None,
                 frame_cycles: int = FRAME_CYCLES, sync: SyncConfig = DEFAULT_SYNC, **kw):
        if kw.get("pre"):
            raise ValueError("LockOnceFrame has no pause region: put per-frame work in `tail`")
        if sync.coarse != "none":
            raise ValueError("LockOnceFrame needs the $8209 lock (coarse='none')")
        super().__init__(sync=sync, **kw)
        if dance_to_band0 % 4 or frame_cycles % 4:
            raise ValueError("dance_to_band0 and frame_cycles must be multiples of 4 cycles")
        self.dance_to_band0 = dance_to_band0
        self.exit_on_key = exit_on_key
        self.ikbd_quiet = ikbd_quiet
        self.check = check
        self.check_base = check_base
        self.frame_cycles = frame_cycles

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
        return self.frame_cycles - self.n_lines(upper, lower) * self.line_len - self.dance_to_band0

    def expand_tail(self, tail: str, budget: int | None = None) -> str:
        """Pad `tail` to the tail budget (ValueError if it does not fit): a fit test for callers
        that size their per-frame work."""
        return _expand((tail.rstrip("\n") + "\n" if tail.strip() else "") + ";@fill\n",
                       self.tail_budget() if budget is None else budget, "the lock-once tail")

    def _post(self, post: str) -> str:
        """Band registers, then (after the fill, so at a fixed cycle) the check and the jump."""
        text = (post.rstrip("\n") + "\n" if post.strip() else "") + _RELOAD + ";@fill\n"
        if not (self.exit_on_key or self.check):
            return text + "    jmp     __band0\n"
        if self.check:
            text += _check(self.check_base)
        text += _KEY_INDEX if self.exit_on_key else "    moveq   #4,d0\n"
        if self.check:
            text += _ERR_INDEX
        return text + _JUMP

    def frame_body(self, *, upper: WorkStream | None = None, lower: WorkStream | None = None,
                   tail: str = "", pre: str | None = None, post: str | None = None) -> str:
        if pre:
            raise ValueError("LockOnceFrame has no pause region: put per-frame work in `tail`")
        post = self.post if post is None else post
        bands = self.bands(upper=upper, lower=lower)
        tail_budget = self.frame_cycles - bands.n_lines * self.line_len - self.dance_to_band0
        post_budget = self.dance_to_band0 - self.dance_cycles
        return (
            # frame 1: the VBL-mode prelude and lock, entered from the VBL (emit_program's
            # handler prologue is the same as VBL mode's, so the frame-1 dance lands as usual)
            self.sync.asm("", post)
            + "\n" + bands.asm
            + "* ---- lock-once loop: the tail, padded to the cycle ----\n"
            + self.expand_tail(tail, tail_budget)
            + self.dance
            + "* ---- post: band registers, check, exit test, back to band 0 ----\n"
            + _expand(self._post(post), post_budget, "the lock-once post region"))

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
        ikbd = self.exit_on_key and self.ikbd_quiet
        prefix = (_SETUP_SP + (_ikbd(IKBD_QUIET, "q") if ikbd else "")
                  + (_SETUP_QUIET if self.exit_on_key else ""))
        src = emit_program(body, setup=prefix + setup, extra=_exit_code(ikbd) + extra,
                           main=_MAIN, mask=True, **emit_kw)
        return build_tos(src, out_path)
