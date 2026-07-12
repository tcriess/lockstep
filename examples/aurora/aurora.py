"""Aurora, rebuilt through Lockstep — the capstone.

Aurora (tecer & ZoltarX, 2024) is a 4kb Atari ST intro: all four borders open, full-sync, VBL-only.
A light-grey field with a two-colour logo, a 64-line scroller in an 8x16 TOS font blown up to 64x64
with a per-line palette, two 16x16 mask-and-or sprites on a Lissajous path, and a dosound tune.

`orig/aurora.s` is the original, unedited. This file rebuilds the same demo **through the toolkit**:

    the CONTENT is Aurora's   — the same instructions, the same data, the same effects;
    the COUNTING is Lockstep's — every `dcb.w` magic number in the original is derived here.

That is the whole claim, and it is falsifiable: the original's hand-counted fillers (`dcb.w 90`,
`13`, `12` on a border line; `dcb.w 58`/`22`/`798` balancing the preamble) never appear below. They
come back out of the tool, and `verify` measures every line at 512c on cycle-exact silicon.

Where the work goes — a frame has exactly three places to put it, and Lockstep budgets all three:

    pre    the VBL-entry pause, 17,052c of dead time before the beam sync. Aurora draws its
           sprites and steps every sequence here. Padded back to EXACTLY the pause budget: the
           60 Hz pulse right after it is the top-border bust, and its scanline is fixed purely by
           how many cycles come first.
    post   the 340c window between the beam lock and band 0 — where the bands' registers get loaded.
    bands  the 260 display scanlines, poured into the gaps between the border switches.
    tail   the vertical blank, after the picture: the dosound replay.

    python examples/aurora/aurora.py        # -> aurora.tos
    hatari examples/aurora/aurora.tos
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lockstep import LineTemplate, Peg, Segment, StepWork, WorkBlock, WorkStream  # noqa: E402
from lockstep.packer import pack_schedule  # noqa: E402
from lockstep.program import build_tos, emit_program  # noqa: E402
from lockstep.skeleton import OverscanFrame  # noqa: E402


HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "orig")

BOT_LINES = 32
MAIN_LINES = 227          # the bust lands on the bottom-border scanline
SCROLL_LINES = 64         # the scroller is 64 lines tall...
SHIFT_LINES = 2 * SCROLL_LINES   # ...and needs 2 raster lines of byte-shifting each -> 128
FEED_LINES = 8            # the font feed: 8 raster lines x 8 scroller lines = 64
IDLE_LINES = MAIN_LINES - SHIFT_LINES - FEED_LINES - 1 - 31   # = 59 border-only lines


# --------------------------------------------------------------------------------------------
# Aurora's routines and data, verbatim. Everything from `prepare_sprite` to the end of the file:
# the sprite preshifter, the LINE-A font rip, the scrolltext builder, every table, and the BSS.
# The `include`s are inlined so the source is self-contained when vasm sees it in a temp dir.
# --------------------------------------------------------------------------------------------
def _orig(name: str) -> str:
    with open(os.path.join(ORIG, name)) as f:
        return f.read()


def aurora_support() -> str:
    src = _orig("aurora.s")
    start = src.index("prepare_sprite:")
    body = src[start:]
    # inline `include 'gen_x.s'`
    body = re.sub(r"^\s*include\s+'([^']+)'.*$",
                  lambda m: _orig(m.group(1)), body, flags=re.M)

    # only the equates the slice does NOT already carry (sprite_size_per_shift and
    # fontcharactersize are defined inside it)
    equates = ("mask_b    equ $fffffa15\n"
               f"bot_lines equ {BOT_LINES}\n"
               "DEBUG     equ 0\n")
    return equates + "\n" + body


# --------------------------------------------------------------------------------------------
# SETUP — runs once. Aurora's init (aurora.s:7-130), minus the parts `emit_program` already owns
# (supervisor, MFP mask, VBL install, restore/exit).
# --------------------------------------------------------------------------------------------
SETUP = """\
    jsr     prepare_font            ; rip the 8x16 system font out of TOS (LINE-A) and blow it up
    jsr     prepare_scrolltext      ; the text -> a list of font-block offsets

; --- screen 2 ---
    move.l  #scrn2,d0
    add.l   #255,d0
    clr.b   d0                      ; 256-align: the video base has no low byte on the ST
    move.l  d0,d1
    lsr.l   #8,d1
    move.w  d1,hw_screen2
    move.w  d1,hw_screen
    add.l   #160,d0                 ; skip the crippled first line of the opened top border
    move.l  d0,screen2
    move.l  d0,d1
    add.l   #230*(28+200+bot_lines-64),d1
    addq.l  #4,d1                   ; the scroller lives in planes 3+4
    move.l  d1,scrollscraddr2
    move.l  d1,scrollscraddr

    movem.l pal_start,d0-d7         ; the global palette
    movem.l d0-d7,$ffff8240.w

; --- screen 1 ---
    move.l  #scrn,d0
    add.l   #255,d0
    clr.b   d0
    move.l  d0,d1
    lsr.l   #8,d1
    move.w  d1,hw_screen1
    add.l   #160,d0
    move.l  d0,screen1
    move.l  d0,screen
    move.l  d0,a6
    move.l  d0,d1
    add.l   #230*(28+200+bot_lines-64),d1
    addq.l  #4,d1
    move.l  d1,scrollscraddr1

; --- the logo: the same 13 longs blitted twice, 2 bytes apart, so it lands in plane 0 AND
;     plane 1 -> two side-by-side copies in colours 1 and 2. Each source line is drawn twice.
    lea     230*51(a6),a6
    lea     logo_data,a5
    move.w  #50-1,d0
.logoloop:
    rept 13
    move.l  (a5)+,(a6)+
    move.l  #0,(a6)+                ; ...and zero planes 2+3, so the scroller has clean paper
    endr
    lea     -13*4(a5),a5
    addq    #2,a6
    rept 13
    move.l  (a5)+,(a6)+
    move.l  #0,(a6)+
    endr
    lea     20(a6),a6
    lea     -13*4(a5),a5
    rept 13
    move.l  (a5)+,(a6)+
    move.l  #0,(a6)+
    endr
    lea     -13*4(a5),a5
    addq    #2,a6
    rept 13
    move.l  (a5)+,(a6)+
    move.l  #0,(a6)+
    endr
    lea     20(a6),a6
    dbra    d0,.logoloop

; --- screen 2 is a copy of screen 1 ---
    move.l  screen1,a6
    move.l  screen2,a5
    move.w  #(230*28+230*200+230*bot_lines)/4-1,d7
.cpyscr:
    move.l  (a6)+,(a5)+
    dbra    d7,.cpyscr

; --- preshift the six sprites (16 copies each, reordered into screen planes) ---
    lea     raw_spr_cursor,a0
    lea     spr_cursor,a1
    jsr     prepare_sprite
    lea     raw_spr_empty,a0
    lea     spr_empty,a1
    jsr     prepare_sprite
    lea     raw_spr_butterfly_0,a0
    lea     spr_butterfly_0,a1
    jsr     prepare_sprite
    lea     raw_spr_butterfly_1,a0
    lea     spr_butterfly_1,a1
    jsr     prepare_sprite
    lea     raw_spr_qm1,a0
    lea     spr_qm1,a1
    jsr     prepare_sprite
    lea     raw_spr_qm3,a0
    lea     spr_qm3,a1
    jsr     prepare_sprite
    jsr     init_sprite

; --- point the video at screen 1 ---
    clr.b   $ffff8260               ; lo-res
    move.w  hw_screen1,d0
    move.b  d0,$ffff8203
    lsr.w   #8,d0
    move.b  d0,$ffff8201
"""


# --------------------------------------------------------------------------------------------
# POST — the 340c window between the beam lock and band 0. Load the registers the bands walk.
# May not touch a0/a1/d3/d4: those ARE the border switches.
# --------------------------------------------------------------------------------------------
POST = """\
    movea.l scrollscraddr,a6        ; a6 walks the scroller buffer through band A
    move.l  font_addr1,a3           ; a3/a4: the two preshifted font copies (the 8-px step)
    add.w   fontoffset1,a3
    move.l  font_addr2,a4
    add.w   fontoffset2,a4
    movea.l scrollscraddr,a5
    lea     216(a5),a5              ; a5: the rightmost group, where new character data is fed in
"""


# --------------------------------------------------------------------------------------------
# THE BANDS. Aurora's line template, at its real offsets. Lockstep sizes every gap.
# --------------------------------------------------------------------------------------------
def per_line(make, n: int) -> WorkStream:
    """A `WorkStream` is poured ACROSS a segment's lines, not repeated on each one. So when a band
    wants the SAME work on every one of its N lines, the stream has to carry it N times over. (Get
    this wrong and the packer happily spreads one line's worth of work across the whole band — the
    lines still close at 512c, so nothing complains; you just get 1/8th of a scroller.)"""
    blocks = []
    for _ in range(n):
        blocks.extend(make().blocks)
    return WorkStream(blocks)


COL = "move.l 8(a6),(a6)+\naddq #4,a6"          # one scroller column: 24 + 8 = 32c

# NB: the gap before the right switch is 356c here, not the original's 360c. The wakestate-robust
# left blip carries one extra `nop` (the stabiliser that keeps ws2's left border open), which costs
# 4 cycles out of the line. So each of Aurora's leading nop-pairs gives one nop back. This is the
# kind of edit that used to mean re-deriving every filler count on the line by hand; here the packer
# just re-sizes the gaps and `verify` confirms all 260 lines are still 512c.


def band_shift_line1() -> WorkStream:
    """First raster line of a scroller-shift pair: 11 columns before the right switch, then a
    column and a half, then the other half. The half-longwords are not an accident — the switch
    falls in the middle of a 32-bit copy, so the copy is cut in two around it."""
    return WorkStream([
        WorkBlock("nop"),                                          # 4c
        *[WorkBlock(COL) for _ in range(11)],                     # 11 x 32c   -> gap1 = 356c
        WorkBlock(COL),                                           # 32c  \
        WorkBlock("move.w 8(a6),(a6)+"),                          # 16c   > gap2 = 52c
        WorkBlock("nop"),                                         #  4c  /
        WorkBlock("move.w 8(a6),(a6)+\naddq #4,a6"),              # 24c  \  gap3 = 48c
        WorkBlock("move.l 8(a6),(a6)+"),                          # 24c  /
    ])


def band_shift_line2() -> WorkStream:
    """Second raster line of the pair. `a6` ends exactly 230 bytes on — one scroller line."""
    return WorkStream([
        WorkBlock("addq #4,a6"),                                  # the adjust deferred from line 1
        *[WorkBlock(COL) for _ in range(10)],                     # 8 + 10*32 = 328
        WorkBlock("move.l 8(a6),(a6)+"),                          # 24c
        WorkBlock("nop"),                                         # 4c         -> gap1 = 356c
        WorkBlock("addq #4,a6\nmove.l 8(a6),(a6)+\naddq #4,a6"),  # 40c  \
        WorkBlock("nop\nnop\nnop"),                               # 12c   > gap2 = 52c
        WorkBlock("move.l 8(a6),(a6)+"),                          # 24c  \
        WorkBlock("lea 18(a6),a6"),                               #  8c   > gap3 = 48c
        WorkBlock("nop\nnop\nnop\nnop"),                          # 16c  /
    ])


# The font feed: 8 scroller lines per raster line. a3 = the shifted previous character, a4 = the
# shifted new one; OR them together and that IS the 8-pixel step.
FEED_ROW = "move.l (a3)+,d0\nor.l (a4)+,d0\nmove.l d0,{off}(a5)"


def band_feed_line() -> WorkStream:
    """One raster line feeds EIGHT scroller lines. All of it belongs in the 356c gap before the
    right-border switch — the beam window says so.

    Without the window the packer does what it is told and fills the whole line: it pours 11 of
    these blocks into a line instead of 9, spilling the 9th and 10th into the gaps *after* the
    switches. Every line still closes at 512c, so nothing complains — but `a5` then advances at the
    wrong moments and 63 of the 64 scroller lines never get written. The window is not decoration;
    it is the constraint that makes the band mean what it says."""
    rows = [WorkBlock(FEED_ROW.format(off=f"{i*230}" if i else ""), beam=(0, 376), label=f"row{i}")
            for i in range(8)]
    rows[0] = WorkBlock("move.l (a3)+,d0\nor.l (a4)+,d0\nmove.l d0,(a5)", beam=(0, 376))
    return WorkStream(rows + [WorkBlock("lea 8*230(a5),a5", beam=(0, 376))])     # 40 + 7*44 + 8 = 356c


# One line's palette: load 16 colours into registers before the right switch, then write them out
# after it, so they take effect on the NEXT scanline. The beam windows pin each block to its side
# of the switch — without them the packer would (correctly, but uselessly) put everything in the
# 360c gap and the colours would land a line early.
PAL_LOAD = "move.l (a5)+,a2\nmove.w #$8240,a6\nmovem.l (a2),d0-d2/d5-d7/a3-a4"   # 12+8+76 = 96c
PAL_HI = "move.l d7,20(a6)\nmove.l a3,24(a6)\nmove.l a4,28(a6)"                  # colours 10..15
PAL_LO = "movem.l d0-d2/d5-d6,(a6)"                                              # colours 0..9


def band_palette_line() -> WorkStream:
    return WorkStream([
        WorkBlock(PAL_LOAD, beam=(0, 376)),        # before the right switch
        WorkBlock(PAL_HI, beam=(392, 444)),        # after it
        WorkBlock(PAL_LO, beam=(464, 512)),        # and after the extra flip
    ])


def band_palette_first() -> WorkStream:
    """The FIRST palette line has to pick up the pointer: `a5` walks a 64-entry window into the
    scroller-palette table, one entry per line, and it is loaded here and then carried across the
    next 63 lines (through four different band templates). Aurora calls this its band D."""
    return WorkStream([
        WorkBlock("move.l current_scrollerpal_sequence_struct+2,a5\n" + PAL_LOAD, beam=(0, 376)),
        WorkBlock(PAL_HI, beam=(392, 444)),
        WorkBlock(PAL_LO, beam=(464, 512)),
    ])


def band_palette_bust() -> WorkStream:
    """The bust line carries a palette too — but the 60 Hz set at cycle 500 eats into the last gap
    (48c -> 36c), so the 48c `movem` no longer fits there. Two of the colour longs move up into the
    big gap and the last write shrinks to 32c. Aurora does exactly this, for exactly this reason."""
    return WorkStream([
        WorkBlock(PAL_LOAD + "\nmove.l d5,12(a6)\nmove.l d6,16(a6)", beam=(0, 376)),
        WorkBlock(PAL_HI, beam=(392, 444)),
        WorkBlock("movem.l d0-d2,(a6)", beam=(464, 500)),      # 32c, not 48c
    ])


def band_palette_last() -> WorkStream:
    """The last line restores the GLOBAL palette instead of pulling the next scroller one."""
    return WorkStream([
        WorkBlock("move.l current_pal_sequence_struct+2,a2\nmove.w #$8240,a6\n"
                  "movem.l (a2),d0-d2/d5-d7/a3-a4", beam=(0, 376)),
        WorkBlock(PAL_HI, beam=(392, 444)),
        WorkBlock(PAL_LO, beam=(464, 512)),
    ])


# --------------------------------------------------------------------------------------------
# PRE — the VBL-entry pause. Aurora's whole per-frame logic lives here: step the four sequences
# (sprite, animation, palette, sound, scroller-palette) and draw the two sprites.
#
# In the original every conditional in this region is balanced BY HAND: each `bge` is followed by
# a `dcb.w 58,$4e71` / `dcb.w 22,$4e71` on the other arm to make both paths cost the same, and the
# whole region is padded with a final `dcb.w 798,$4e71` so that the 60 Hz pulse after it lands on
# the right scanline. Ten magic numbers, each one re-derived by hand whenever anything moved.
#
# We take that code VERBATIM and delete every one of those numbers, replacing them with `;@balance`
# (equalise the arms) and letting `pre`'s `;@budget` size the rest. The tool puts the numbers back.
# --------------------------------------------------------------------------------------------
_BRANCH = re.compile(r"^\s+(bge|beq|bne|blt)\.s\s+(\.[\w]+)\s*(;.*)?$")
_LABEL = re.compile(r"^(\.[\w]+):")
_BALANCE_FILL = re.compile(r"^\s+dcb\.w\s+\d+,\$4e71.*$")
_CONVERGE = re.compile(r"^\s+bra\.s\s+(\.[\w]+)\s*(;.*)?$")


def balanced(text: str) -> str:
    """Aurora's hand-balanced conditionals -> Lockstep `;@balance` blocks.

    Recognises the one construct the original uses, everywhere:

        bge.s .ok            ;@balance
        <inner code>   =>        bge.s .ok
        bra.s .cont              <inner code>
    .ok:                         bra.s .cont
        dcb.w 58,$4e71       ;@balance alt
        nop                  .ok:
        nop                  ;@fill
    .cont:                       nop          <- the 2c Bcc taken/not-taken asymmetry a nop
                                 nop             cannot bridge; Aurora's own evening-out pair
                             ;@balance end
                             .cont:

    The `dcb.w` count is dropped on the floor. That number is the tool's job now.
    """
    lines = text.splitlines()
    out: list[str] = []
    stack: list[tuple[str, str]] = []      # (target_label, convergence_label)
    pending_fill: str | None = None

    for i, ln in enumerate(lines):
        m = _BRANCH.match(ln)
        if m:
            # The convergence point is the target of the LAST `bra.s` before this branch's own
            # target label — not the first. Aurora nests (a `beq` inside a `bge` arm), and the
            # first `bra.s` you meet belongs to the INNER construct.
            target = m.group(2)
            conv = None
            for nxt in lines[i + 1:]:
                lm = _LABEL.match(nxt)
                if lm and lm.group(1) == target:
                    break
                c = _CONVERGE.match(nxt)
                if c:
                    conv = c.group(1)
            if conv:
                out.append(";@balance")
                out.append(ln)
                stack.append((target, conv))
                continue

        lab = _LABEL.match(ln)
        if lab and stack and lab.group(1) == stack[-1][0]:
            out.append(";@balance alt")
            out.append(ln)
            pending_fill = stack[-1][0]
            continue

        if pending_fill and _BALANCE_FILL.match(ln):
            out.append(";@fill")           # <- the hand-counted dcb.w, deleted
            pending_fill = None
            continue

        if lab and stack and lab.group(1) == stack[-1][1]:
            out.append(";@balance end")
            out.append(ln)
            stack.pop()
            pending_fill = None
            continue

        out.append(ln)

    if stack:
        raise RuntimeError(f"unclosed balance construct(s): {stack}")
    return "\n".join(out) + "\n"


def aurora_pre() -> str:
    """Aurora's preamble (aurora.s: sections A-J), with its hand-counted balance filler and its
    trailing `dcb.w 798,$4e71` removed. Lockstep re-derives both."""
    src = _orig("aurora.s").splitlines()
    # from "; first, toggle the screen addresses" up to (not including) the final pad
    start = next(i for i, l in enumerate(src) if "first, toggle the screen addresses" in l)
    end = next(i for i, l in enumerate(src) if "dcb.w 798,$4e71" in l)
    body = "\n".join(src[start:end])
    return balanced(body)


# --------------------------------------------------------------------------------------------
# TAIL — the vertical blank, after the last scanline. Aurora's dosound replay (an XBIOS-compatible
# register-event stream) plus the screen flip. Data-dependent cost, so `frame_budget` wants the
# worst case; it is small next to the ~8.6kc of slack.
# --------------------------------------------------------------------------------------------
def aurora_tail() -> str:
    src = _orig("aurora.s").splitlines()
    start = next(i for i, l in enumerate(src) if "adapted code of the original dosound" in l)
    end = next(i for i, l in enumerate(src) if l.startswith("exit_vbi:"))
    body = "\n".join(src[start:end])
    # the original ends the handler by writing the new video base; keep that, drop its rte/movem
    # (emit_program's handler wrapper owns those).
    body = "\n".join(l for l in body.splitlines()
                     if not l.strip().startswith(("movem.l (sp)+", "move.w  (a7)+", "rte")))
    return body + "\n"


# --------------------------------------------------------------------------------------------
# THE BAND STACK — Aurora's frame, as Lockstep segments. This is the whole picture, top to bottom.
# --------------------------------------------------------------------------------------------
def bands():
    from lockstep.skeleton import _allborders

    allb = _allborders(left_nops=1)                 # + the left stabiliser (ws2)
    # the cross-boundary bottom bust: 60 Hz set late here, restored early on the next line, so it
    # straddles the scanline edge where the frame-end decision is made -> all four wakestates.
    bust = LineTemplate(allb.pegs + [Peg(500, "move.b d4,(a0)", "60Hz set (cross)")])
    firstbot = LineTemplate([allb.pegs[0], Peg(20, "move.b d3,(a0)", "50Hz restore (cross)"),
                             allb.pegs[1], allb.pegs[2]])

    segs: list[Segment] = []
    # A — 64 scroller lines, two raster lines of byte-shifting each
    for _ in range(SCROLL_LINES):
        segs.append(Segment(allb, band_shift_line1(), 1))
        segs.append(Segment(allb, band_shift_line2(), 1))
    # B — feed one 64-line-tall character column in from the right
    segs.append(Segment(allb, per_line(band_feed_line, FEED_LINES), FEED_LINES))
    # C — nothing to do but hold the borders open
    segs.append(Segment(allb, WorkStream([]), IDLE_LINES))
    # D — the first palette line loads the table pointer...
    segs.append(Segment(allb, band_palette_first(), 1))
    # E — ...and the next 31 just walk it
    segs.append(Segment(allb, per_line(band_palette_line, 31), 31))
    # F — the bust line, still carrying a palette
    segs.append(Segment(bust, band_palette_bust(), 1))
    # the restore line
    segs.append(Segment(firstbot, band_palette_line(), 1))
    # G — the opened bottom border, still carrying a palette
    segs.append(Segment(allb, per_line(band_palette_line, BOT_LINES - 2), BOT_LINES - 2))
    # H — the last line puts the global palette back
    segs.append(Segment(allb, band_palette_last(), 1))
    return pack_schedule(segs)


def aurora_source() -> str:
    from lockstep.skeleton import SyncConfig
    sync = SyncConfig()
    frame = sync.asm(aurora_pre(), POST) + "\n" + bands().asm + "\n" + aurora_tail()
    return emit_program(frame, setup=SETUP, extra=aurora_support(), exit_on_key=True)


def build(out_path: str) -> str:
    return build_tos(aurora_source(), out_path)


if __name__ == "__main__":
    res = bands()
    print(f"bands: {res.n_lines} lines, {res.units_placed}/{res.units_total} work units, "
          f"{res.nop_cycles}c of nop filler")
    out = build(os.path.join(HERE, "aurora.tos"))
    print(f"built {out} ({os.path.getsize(out)} bytes)")
