"""Capstone (visual) — see Lockstep's all-borders frame actually open the borders in Hatari.

The cycle verifier proved every line is 512c; this proves the timing *opens the borders*.
We wrap Lockstep's generated all-borders bands (which reproduce Aurora's `dcb.w 90/13/12`
exactly) in Aurora's real beam-sync entry (transcribed read-only from aurora.s:184-215),
point the border switches at the REAL shifter/sync registers, fill the screen with a colour
that renders white over a black border, and capture the frame with video on + borders shown.

Borders open  => the white display region spills into the overscan (a wider/taller bounding
box than a normal 320x200 display). `active_bbox` turns that into a number.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from examples.aurora.screen import allborders_screen   # noqa: E402
from lockstep.visual import active_bbox, capture        # noqa: E402

# one-time: palette (border black, colour 15 white), screen buffer filled, video base, regs.
SETUP = """\
    move.w  #$0000,$ffff8240    ; palette[0] = black  (this is the BORDER colour)
    move.w  #$0777,$ffff825e    ; palette[15] = white (the display fill)
    lea     $a8000,a2
    move.w  #$3fff,d0
.scrfill:
    move.l  #$ffffffff,(a2)+    ; fill 64KB with colour 15 (all four planes set)
    dbra    d0,.scrfill
    move.b  #$0a,$ffff8201      ; video base high  -> $0a8000
    move.b  #$80,$ffff8203      ; video base mid
    lea     $ffff8260,a1        ; a1 = resolution reg (left-border switch target)
    moveq   #2,d3               ; d3 = mono / 50 Hz value
    moveq   #0,d4               ; d4 = lo-res / 60 Hz value
"""

# per-frame: Aurora's beam sync (re-locks cycle 0), then the generated all-borders bands.
# Self-contained in registers (aurora.s:185-190) — this runs in the VBL handler, where the
# one-time SETUP's registers no longer survive; it must re-establish its own each frame.
SYNC = """\
    move.b  #2,$ffff820a        ; re-assert the 50 Hz baseline EmuTOS's VBL used to give us
    clr.b   $ffff8260           ; re-assert lo-res; our VBL replaced EmuTOS's, so we own this
    move.w  #1064,d0            ; [CALIBRATE] pause from VBL-entry down toward the display top
.pause:                         ;   (~17052c; aurora.s fills this with real per-frame work +
    nop                         ;   dcb.w 798). The exact budget is hardware-tuned -- it must
    dbra    d0,.pause           ;   land the wait-poll near the first visible line.
    eor.b   #2,$ffff820a        ; the 60/50 Hz sync-toggle DANCE (aurora.s:736-743) -- toggle to
    rept 8                      ;   60 Hz, hold 8 nops, back to 50 Hz. Stabilises the line for
    nop                         ;   the right-border switch; WITHOUT it the borders won't open.
    endr
    eor.b   #2,$ffff820a        ; back to 50 Hz
    move.w  #$8209,a0           ; a0 = video address low byte (aurora.s:746-751)
    lea     $ffff8260,a1        ; a1 = resolution reg (left-border switch target)
    moveq   #0,d0
    moveq   #16,d1
    moveq   #2,d3               ; d3 = mono / 50 Hz value
    moveq   #0,d4               ; d4 = lo-res / 60 Hz value
.wait:
    move.b  (a0),d0
    beq.s   .wait               ; wait for video address low byte != 0 (aurora.s:753-755)
    dcb.w   5,$4e71             ; 20c spacer (aurora.s:760)
    sub.w   d0,d1               ; fine-sync: d1 = 16 - d0, then ...
    lsl.w   d1,d0               ; ... lsl -> SYNC LOCKED here (aurora.s:763-764)
    dcb.w   5,$4e71             ; 20c spacer (aurora.s:771)
    move.w  #$820a,a0           ; a0 = sync-mode reg (right-border switch target). 58c since wait.
    dcb.w   77,$4e71            ; [CALIBRATE] first line after sync ~= 368c (aurora.s:794 uses 50,
                                ;   interleaving scroller setup we don't have).
"""

CLOSED = """\
    move.w  #$8209,a0
    moveq   #0,d0
.wait:
    move.b  (a0),d0
    beq.s   .wait
    move.w  #$820a,a0
"""   # sync only, no border switches -> a normal (borders-closed) display


def _open_body(lines=227):
    return SYNC + "\n" + allborders_screen(lines).asm


if __name__ == "__main__":
    from st68k.hatari import HatariError
    out = os.path.dirname(os.path.abspath(__file__))
    try:
        op = capture(_open_body(227), os.path.join(out, "bordopen.png"),
                     setup=SETUP, at_vbl=360, video_timing="ws3")
        cl = capture(CLOSED, os.path.join(out, "bordclos.png"),
                     setup=SETUP, at_vbl=360, video_timing="ws3")
    except HatariError as e:
        print("HATARI unavailable:", e)
        sys.exit(0)

    import numpy as np
    from PIL import Image

    def display_region(png):
        # the display fill renders near-white; the border is black. Measure the white region.
        a = np.asarray(Image.open(png).convert("RGB")).astype(np.int16)
        mask = a.min(axis=2) > 180                             # near-white = display pixels
        ys, xs = np.where(mask)
        return (int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1),
                100.0 * mask.mean())

    ow, oh, ocov = display_region(op.png)
    cw, ch, ccov = display_region(cl.png)
    print(f"canvas: {op.width} x {op.height}  (full PAL overscan, borders shown)")
    print(f"borders CLOSED — display {cw} x {ch}px, {ccov:.0f}% of canvas")
    print(f"borders OPEN   — display {ow} x {oh}px, {ocov:.0f}% of canvas")
    print(f"\nopened: +{ow - cw}px wide, +{oh - ch}px tall, +{ocov - ccov:.0f}% coverage")
    if ocov > ccov + 10:
        print("=> Lockstep's generated frame OPENS the borders: the display fills the overscan")
        print("   where a normal frame shows a black border. Capstone visual proof. ✅")
    else:
        print("=> no border opening detected — sync/offset/wakestate may need tuning.")
    print(f"\nPNGs: {op.png}\n      {cl.png}")
