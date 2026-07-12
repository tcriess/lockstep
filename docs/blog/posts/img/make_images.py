"""Generate the blog series' screenshots — real headless Hatari captures, no mockups.

    python docs/blog/posts/img/make_images.py

Produces, in this directory:
  borders-closed.png    a normal frame: green 320x200 display, black border all round
  borders-open.png      the same screen with all four borders open (ws3)
  wakestates.png        contact sheet: the naive lock on ws1..ws4 (ws2/ws4 lose borders)
  wakestates-fixed.png  contact sheet: the robust lock on ws1..ws4 (all four open)
  aurora.png            aurora.tos — the rebuilt demo: all four borders open, scroller running
                        in the opened bottom border

Every shot is a genuine cycle-exact Hatari render of an assembled .TOS. The aurora shot needs
`make aurora` (or `python examples/aurora/aurora.py`) to have built it first.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# docs/blog/posts/img -> repo root
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, ROOT)

from examples.bordopen.bordopen import _setup, build, build_robust  # noqa: E402
from lockstep.visual import capture, shoot_counter, shoot_tos  # noqa: E402

# sync only, no border switches -> a normal, borders-closed display (examples/aurora/visual.py:70)
CLOSED = """\
    move.w  #$8209,a0
    moveq   #0,d0
.wait:
    move.b  (a0),d0
    beq.s   .wait
    move.w  #$820a,a0
"""

WS = ("ws1", "ws2", "ws3", "ws4")


def contact_sheet(pngs, labels, out, cols=2, pad=12, label_h=26):
    """Tile per-wakestate shots into one labelled image."""
    from PIL import Image, ImageDraw

    ims = [Image.open(p).convert("RGB") for p in pngs]
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w + (cols + 1) * pad,
                              rows * (h + label_h) + (rows + 1) * pad), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    for i, (im, lab) in enumerate(zip(ims, labels)):
        r, c = divmod(i, cols)
        x = pad + c * (w + pad)
        y = pad + r * (h + label_h + pad)
        d.text((x + 2, y + 4), lab, fill=(230, 230, 235))
        sheet.paste(im, (x, y + label_h))
    sheet.save(out)
    print(f"  wrote {os.path.basename(out)}  {sheet.size[0]}x{sheet.size[1]}")
    return out


def main():
    print("building the .TOS variants ...")
    naive = build(os.path.join(HERE, "_naive.tos"))            # original lock: all-4 on ws1/ws3 only
    robust = build_robust(os.path.join(HERE, "_robust.tos"))   # stabiliser + cross-bust: all 4 WS

    print("shooting borders CLOSED (a normal frame) ...")
    cl = capture(CLOSED, os.path.join(HERE, "borders-closed.png"),
                 setup=_setup(), at_vbl=360, video_timing="ws3")
    print(f"  {cl.width}x{cl.height}")

    print("shooting borders OPEN (ws3) ...")
    op = shoot_tos(robust, os.path.join(HERE, "borders-open.png"), video_timing="ws3")
    print(f"  {op.width}x{op.height}")

    print("shooting the naive lock on all four wakestates ...")
    naive_shots = []
    for ws in WS:
        p = os.path.join(HERE, f"_naive_{ws}.png")
        shoot_tos(naive, p, video_timing=ws)
        naive_shots.append(p)
        print(f"  {ws} ok")

    print("shooting the robust lock on all four wakestates ...")
    robust_shots = []
    for ws in WS:
        p = os.path.join(HERE, f"_robust_{ws}.png")
        shoot_tos(robust, p, video_timing=ws)
        robust_shots.append(p)
        print(f"  {ws} ok")

    contact_sheet(naive_shots, [f"{w}  (same binary)" for w in WS],
                  os.path.join(HERE, "wakestates.png"))
    contact_sheet(robust_shots, [f"{w}  (all four open)" for w in WS],
                  os.path.join(HERE, "wakestates-fixed.png"))

    # The capstone, running inside the open borders: Aurora rebuilt by the toolkit. Shot late
    # enough (vbl 2000) that the scrolltext's leading spaces have passed and real glyphs are on
    # screen — the scroller lives in the OPENED BOTTOM BORDER, so a frame with letters in it is
    # also the proof that the bottom border is open.
    prog = os.path.join(ROOT, "examples", "aurora", "aurora.tos")
    if os.path.exists(prog):
        print("shooting aurora.tos (the rebuilt demo in full overscan) ...")
        d = shoot_tos(prog, os.path.join(HERE, "aurora.png"), at_vbl=2000,
                      video_timing="ws3", timeout=300)
        print(f"  {d.width}x{d.height}")
    else:
        print("skipping aurora.tos (not built — run `python examples/aurora/aurora.py`)")

    print("\ndone.")


if __name__ == "__main__":
    main()
