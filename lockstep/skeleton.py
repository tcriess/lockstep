"""Lockstep — the robust overscan frame as a toolkit primitive.

The single most fragile, most reused thing in the whole project — the once-per-frame `$8209`
MMU beam-lock (top-border removal + variable fine-sync shift), the all-borders line template,
the left stabiliser, and the **cross-boundary bottom bust** that opens the bottom border on
*every* wakestate — used to live hand-coded in `examples/bordopen/bordopen.py` and copied into
each demo that wanted it. This module promotes it into a first-class object: `OverscanFrame` owns the
four-border-open mechanism, proven all-wakestate (== `bordws.tos`, W2-certified), and the author
supplies only the effect WORK for the display bands. *The skeleton guarantees the borders.*

It is the counted, lock-once, pure-full-sync recipe (no HBL, no `stop`): one `$8209` beam-poll
per frame, then every scanline counted at exactly `line_len` (512c). Three ingredients make it
wakestate-robust (all learned the hard way — see `examples/bordopen/README.md`):
  1. `left_nops=1` — widen the left hi-res blip 8c→12c (the STABILISER covering ws2's left-border
     GLUE window);
  2. `cross=True` — the CROSS-BOUNDARY bottom bust: SET 60 Hz late on the bust line (no restore)
     and RESTORE 50 Hz early on the next line, so 60 Hz straddles the scanline edge where the
     bottom-border decision is made — every wakestate catches it (a within-line pulse = ws1/ws3
     only);
  3. `main_lines=227` — the bust line lands on the bottom-border scanline (a sharp resonance).

`emit_program` already encodes Aurora's `$70`-VBL-handler bootstrap (disable Timer C + all MFP
interrupts, install the frame as the handler, idle the main program); `OverscanFrame.build`
wraps this frame body in it. The screen fill / palette / video-base is the demo's `setup` — the
skeleton is content-agnostic (it never references a screen address), so an "empty" frame just
shows whatever the video base points at.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import LineTemplate, Peg, Segment, WorkStream
from .packer import pack_schedule
from .program import build_tos, emit_program

LINE_LEN = 512    # one PAL lo-res scanline, in CPU cycles


# --------------------------------------------------------------------------- line templates
def _allborders(left_nops: int = 0) -> LineTemplate:
    """The 3-peg all-borders line (opens top+left+right on every line, aurora.s:218-238).
    `left_nops` widens the left hi-res blip by that many nops (each 4c) — the STABILISER that
    covers more GLUE-check positions for the wakestate-fragile left border (ws2). 0 = Aurora's
    tight `move.b d3,(a1) / move.b d4,(a1)`. Border/shifter writes carry no wait state -> 8c each."""
    gap = "\n".join(["nop"] * left_nops)
    left = "move.b d3,(a1)\n" + (gap + "\n" if gap else "") + "move.b d4,(a1)"
    return LineTemplate([
        Peg(0,   left,                                  "left  (mono/lo-res)"),
        Peg(376, "move.b d4,(a0)\nmove.b d3,(a0)",      "right (60/50 Hz)"),
        Peg(444, "move.b d3,(a1)\nnop\nmove.b d4,(a1)", "extra (left flip)"),
    ])


def _bottombust(bust_at: int = 496, left_nops: int = 0, bot_nops: int = 0) -> LineTemplate:
    """The within-line bottom bust (a 60/50 Hz pulse late on the bust line) — opens the bottom on
    ws1/ws3 ONLY. `bot_nops` widens the 60 Hz hold by that many nops (each 4c); keep
    bust_at + 4*bot_nops + 16 <= line_len."""
    gap = "\n".join(["nop"] * bot_nops)
    bust = "move.b d4,(a0)\n" + (gap + "\n" if gap else "") + "move.b d3,(a0)"
    return LineTemplate(_allborders(left_nops).pegs + [
        Peg(bust_at, bust, "bottom-open (late 60/50 Hz)"),
    ])


# --------------------------------------------------------------------------- sync prelude
@dataclass(frozen=True)
class SyncConfig:
    """The VBL-entry beam-sync (the once-per-frame lock), with every hardware-calibration knob
    exposed. Defaults = the proven-stable `bordopen`/`bordws` sync.

      pause      — d0 for the VBL-entry pause loop; walks from VBL-entry toward the display top
                   before the sync poll.
      first_line — dcb.w count after the lock; sets the first line's budget (Aurora's DEBUG
                   border-only loop uses 85).
      fine       — 'aurora' = moveq #16 / lsl.w  (narrow ~28c window, the stable real-HW lock);
                   'wide'   = moveq #127 / lsr.l (DHS-style, wider — shifts the horizontal phase).
      coarse     — 'none' = the Aurora $8209 video-counter poll (USE THIS — stable, real-HW
                   confirmed); 'hbl' = DHS-style stop-on-HBL (FLICKERS — a diagnostic dead end;
                   needs an HBL handler at $68, which build() supplies).
      baseline   — re-assert 50 Hz / lo-res at handler entry. Aurora's my_70 does NOT (it shifts
                   pre-sync timing ~28c and lands the top metastably => period-2 flicker); the
                   bands self-establish 50 Hz / lo-res, so keep this False.
    """
    pause: int = 1064
    first_line: int = 85
    fine: str = "aurora"
    coarse: str = "none"
    baseline: bool = False

    @property
    def needs_hbl_handler(self) -> bool:
        return self.coarse == "hbl"

    @property
    def pause_budget(self) -> int:
        """Exact cost of the VBL-entry pause loop, in cycles (16 per iteration + 28 of setup and
        fall-through). This is the window that `pre` work has to fit in — see `_prelude`."""
        return 16 * self.pause + 28

    def _prelude(self, pre: str = "") -> str:
        """The dead time between VBL entry and the beam sync — and, optionally, your work in it.

        By default this is a `nop`/`dbra` loop that burns `pause_budget` cycles doing nothing while
        the beam walks down toward the display top. That is a lot of dead time: 17,052 cycles at the
        default `pause=1064`, more than twice the whole post-display tail.

        `pre` pours work into it. The work is costed and then padded back out to **exactly**
        `pause_budget`, because the pause is not slack — it is a measured distance. The 60/50 Hz
        toggle right after it is the top-border bust, and its scanline is fixed purely by how many
        cycles precede it. Come out of the pause 4 cycles early or late and the pulse lands on the
        wrong line and the top border stays shut. (This is where Aurora draws its two sprites, and
        why its author had to hand-balance every branch in that region to the cycle.)

        With `pre` empty the original loop is emitted verbatim, so existing binaries are unchanged.
        """
        base = ("    move.b  #2,$ffff820a        ; re-assert 50 Hz baseline\n"
                "    clr.b   $ffff8260           ; re-assert lo-res\n") if self.baseline else ""

        if not pre.strip():
            fill = (f"    move.w  #{self.pause},d0            ; [knob pause] VBL-entry -> toward "
                    f"display top\n.pause:\n    nop\n    dbra    d0,.pause\n")
        else:
            # Size the pause with the toolkit's own budget machinery rather than a linear cycle
            # sum. That matters: the pause is where the per-frame *logic* wants to live, and logic
            # has branches. A linear min..max over the text is meaningless for a branch (it adds up
            # both arms); `;@budget` + `;@balance` costs the real *paths*, equalises the arms, and
            # sizes the filler — which is exactly the hand-work Aurora's author did with a pencil.
            from st68k.preprocess import PreprocessError, expand
            budget = self.pause_budget
            spec = (f";@sync\n;@budget {budget}    ; the VBL-entry pause: a measured distance, "
                    f"not slack\n{pre.rstrip(chr(10))}\n;@fill\n;@end\n")
            try:
                fill, _ = expand(spec)
            except PreprocessError as e:
                raise ValueError(
                    f"pre-raster work does not fit the {budget}c VBL-entry pause: {e}\n"
                    f"That pause is the distance to the 60 Hz top-border pulse. Overrun it and the "
                    f"pulse lands past its scanline and the TOP BORDER WILL CLOSE. Cut the work, or "
                    f"raise `pause` (which moves the pulse — re-verify all four wakestates if you "
                    f"do). Branches must be wrapped in ;@balance so both paths cost the same."
                ) from None
            fill = fill.rstrip("\n") + "\n"

        return f"""\
{base}{fill}    eor.b   #2,$ffff820a        ; 60/50 Hz sync-toggle dance (aurora.s:736-743)
    rept 8
    nop
    endr
    eor.b   #2,$ffff820a        ; back to 50 Hz
"""

    def _lock_mmu(self) -> str:
        if self.fine == "wide":
            finecode = ("    moveq   #127,d1\n"
                        "    sub.b   d0,d1               ; d1 = 127 - d0  (DHS wide window)\n"
                        "    lsr.l   d1,d1               ; variable shift 8+2n, n up to ~127\n")
            fineinit = "    moveq   #0,d0\n"
        elif self.fine == "aurora":
            finecode = ("    sub.w   d0,d1               ; d1 = 16 - d0  (Aurora narrow window)\n"
                        "    lsl.w   d1,d0               ; variable shift 6+2n\n")
            fineinit = "    moveq   #0,d0\n    moveq   #16,d1\n"
        else:
            raise ValueError(f"unknown fine-sync style {self.fine!r}")
        return f"""\
    move.w  #$8209,a0           ; video address low byte (MMU counter)
    lea     $ffff8260,a1        ; a1 = resolution reg (left-border switch)
{fineinit}    moveq   #2,d3
    moveq   #0,d4
.wait:
    move.b  (a0),d0
    beq.s   .wait               ; wait for video low byte != 0
    dcb.w   5,$4e71             ; 20c spacer (aurora.s:760)
{finecode}__lock:                             ; <- beam probe: SYNC LOCKED here (zero bytes)
    dcb.w   5,$4e71             ; 20c spacer (aurora.s:771)
    move.w  #$820a,a0           ; a0 = sync-mode reg (right-border switch)
"""

    def _lock_glue(self) -> str:
        return """\
    move.w  #$2100,sr           ; admit level-2 HBL (GLUE); keep the rest of the frame masked
    stop    #$2100              ; halt until the next HBL -> GLUE-locked, jitter-free
    move.w  #$2700,sr           ; re-mask the frame
__lock:                             ; <- beam probe: GLUE-locked here (zero bytes)
    lea     $ffff8260,a1        ; a1 = resolution reg (left-border switch)
    move.w  #$820a,a0           ; a0 = sync-mode reg (right-border switch, sign-extended)
    moveq   #2,d3
    moveq   #0,d4
"""

    @property
    def post_lock_budget(self) -> int:
        """Cycles between the fine-sync lock and the first band line (the `first_line` window).
        Work placed here (`post`) is padded back to exactly this."""
        return 4 * self.first_line

    def asm(self, pre: str = "", post: str = "") -> str:
        """The VBL-entry sync prelude, ending at `__band0` with a0/a1/d3/d4 set for the band
        switches (a0=$ffff820a, a1=$ffff8260, d3=2, d4=0).

        Two places to put work, both padded back to exactly the length they replace:

          `pre`  — the VBL-entry pause, BEFORE the sync. 17,052c of dead time. Free to use any
                   register: the sync loads everything it needs afterwards.
          `post` — the window between the lock and the first band line (340c). This is where you
                   load the registers your bands are going to walk (screen pointers, font
                   pointers). It must NOT touch a0/a1/d3/d4 — those are the border switches.
        """
        if self.coarse == "hbl":
            lock = self._lock_glue()
        elif self.coarse == "none":
            lock = self._lock_mmu()
        else:
            raise ValueError(f"unknown coarse-sync style {self.coarse!r}")

        if not post.strip():
            first = (f"    dcb.w   {self.first_line},$4e71            ; [knob first_line] first "
                     f"line after lock\n")
        else:
            from st68k.preprocess import PreprocessError, expand
            budget = self.post_lock_budget
            spec = (f";@sync\n;@budget {budget}    ; the post-lock window, before band 0\n"
                    f"{post.rstrip(chr(10))}\n;@fill\n;@end\n")
            try:
                first, _ = expand(spec)
            except PreprocessError as e:
                raise ValueError(
                    f"post-lock work does not fit the {budget}c window before the first band "
                    f"line: {e}\nRaise `first_line` (which moves band 0 down the screen — "
                    f"re-verify all four wakestates), or move the work into `pre`."
                ) from None
            first = first.rstrip("\n") + "\n"

        return (self._prelude(pre) + lock + first +
                "__band0:                            ; <- beam probe: first band "
                "line starts here\n")


DEFAULT_SYNC = SyncConfig()

# A bare HBL handler for the stop-on-HBL re-sync (coarse='hbl'): just return.
HBL_HANDLER = "__hbl:\n    rte\n"


# --------------------------------------------------------------------------- the frame object
class OverscanFrame:
    """A robust, all-four-borders-open, full-sync frame. Owns the border mechanism (the `$8209`
    lock + the all-borders template + the left stabiliser + the cross-boundary bottom bust); the
    author supplies effect WORK for the display bands and the `setup` (screen/palette/video base).

    Band structure (top->bottom), with work insertion points:
      - the SYNC prelude removes the TOP border and locks the frame (structural, not a work band);
      - `upper` — the main display band (`main_lines` scanlines of the all-borders template);
      - the CROSS-BUST + RESTORE lines open the bottom border (structural);
      - `lower` — the post-bust band (`bot_lines-1` scanlines) filling the opened bottom.
    `upper`/`lower` are `WorkStream`s poured into the gaps between the border pegs (empty =>
    nop-filled). Defaults reproduce `bordws.tos` exactly.

    Set `bust=False` for a top+left+right frame (no bottom); `cross=False` for the within-line
    bottom bust (ws1/ws3 only)."""

    def __init__(self, *, main_lines: int = 227, bot_lines: int = 32, left_nops: int = 1,
                 bot_nops: int = 0, bust: bool = True, cross: bool = True,
                 bust_at: int = 496, set_off: int = 500, restore_off: int = 20,
                 pre: str = "", post: str = "", sync: SyncConfig = DEFAULT_SYNC,
                 line_len: int = LINE_LEN):
        self.pre = pre
        self.post = post
        self.main_lines = main_lines
        self.bot_lines = bot_lines
        self.left_nops = left_nops
        self.bot_nops = bot_nops
        self.bust = bust
        self.cross = cross
        self.bust_at = bust_at
        self.set_off = set_off
        self.restore_off = restore_off
        self.sync = sync
        self.line_len = line_len

    # -- the band stack (pure placement; every line closes to line_len) --
    def _segments(self, upper: WorkStream, lower: WorkStream) -> list[Segment]:
        allb = _allborders(self.left_nops)
        if not self.bust:
            return [Segment(allb, upper, self.main_lines + self.bot_lines)]
        if self.cross:
            # CROSS-BOUNDARY bust: 60 Hz set late on the bust line, restored early on the next.
            bust = LineTemplate(allb.pegs + [
                Peg(self.set_off, "move.b d4,(a0)", "60Hz set (cross-boundary)")])
            firstbot = LineTemplate([allb.pegs[0],
                                     Peg(self.restore_off, "move.b d3,(a0)", "50Hz restore (cross-boundary)"),
                                     allb.pegs[1], allb.pegs[2]])
            return [
                Segment(allb,     upper,           self.main_lines),
                Segment(bust,     WorkStream([]),  1),
                Segment(firstbot, WorkStream([]),  1),
                Segment(allb,     lower,           self.bot_lines - 1),
            ]
        return [
            Segment(allb, upper, self.main_lines),
            Segment(_bottombust(self.bust_at, self.left_nops, self.bot_nops), WorkStream([]), 1),
            Segment(allb, lower, self.bot_lines),
        ]

    def bands(self, *, upper: WorkStream | None = None, lower: WorkStream | None = None):
        """Pack the band stack into one phase-threaded routine (a `PackResult`); `.asm` is the
        band code. Every line is `line_len` (512c); the borders open, all four wakestates."""
        upper = upper if upper is not None else WorkStream([])
        lower = lower if lower is not None else WorkStream([])
        return pack_schedule(self._segments(upper, lower))

    def frame_body(self, *, upper: WorkStream | None = None, lower: WorkStream | None = None,
                   tail: str = "", pre: str | None = None, post: str | None = None) -> str:
        """The full VBL frame body, in the three places a frame has room:

            pre    -> the VBL-entry pause, BEFORE the beam sync (padded back to exactly the pause
                      budget; this is where Aurora draws its sprites)
            upper/ -> the display bands, poured into the gaps between the border switches
            lower
            tail   -> after the last scanline, in the vertical blank (the music replay, counters)

        Hand the result to `emit_program` as the `$70` handler, or use `build()`.
        """
        pre = self.pre if pre is None else pre
        post = self.post if post is None else post
        body = self.sync.asm(pre, post) + "\n" + self.bands(upper=upper, lower=lower).asm
        return body + tail

    def build(self, out_path: str, *, setup: str = "", extra: str = "",
              upper: WorkStream | None = None, lower: WorkStream | None = None,
              tail: str = "", pre: str | None = None, post: str | None = None,
              exit_on_key: bool = False, **emit_kw) -> str:
        """Assemble a standalone `.TOS` of this overscan frame. `setup` runs once (screen fill /
        palette / video base — the skeleton is content-agnostic); `extra` is appended after the
        program. A `coarse='hbl'` sync auto-installs the bare HBL handler. Extra `emit_program`
        kwargs (pool_bytes/pool_origin/main/mask) pass through."""
        if self.sync.needs_hbl_handler:
            extra = HBL_HANDLER + extra
        src = emit_program(self.frame_body(upper=upper, lower=lower, tail=tail, pre=pre,
                                           post=post),
                           setup=setup, extra=extra, exit_on_key=exit_on_key, **emit_kw)
        return build_tos(src, out_path)


# --------------------------------------------------------------------------- free-function API
# The wakestate-robust skeleton pieces, for demos that weave their own schedule rather than
# instantiate an OverscanFrame. Kept byte-identical to the historical bordopen names.
def robust_sync(sync: SyncConfig = DEFAULT_SYNC) -> str:
    """The wakestate-robust beam-lock (Aurora `$8209` MMU poll, pure full-sync). Pair with
    `robust_bands()`. Sets a0=$ffff820a, a1=$ffff8260, d3=2, d4=0 for the band switches."""
    return sync.asm()


def robust_bands(main_lines: int = 227, bot_lines: int = 32, left_nops: int = 1):
    """The all-4-borders-open band stack (left stabiliser + cross-boundary bottom bust), as a
    `PackResult` — `.asm` is the band code. Opens all four borders, flicker-free, all 4 WS. The
    displayed screen is whatever the video base points at (fill it yourself)."""
    return OverscanFrame(main_lines=main_lines, bot_lines=bot_lines, left_nops=left_nops,
                         bust=True, cross=True).bands()
