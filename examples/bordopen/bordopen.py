"""Reproducible builder for the all-borders-open test demo (`bordopen.tos` / `bordws.tos`).

The minimal standalone full-sync demo: NO drawing, NO sound — just the robust beam-sync entry
followed by the all-borders bands, on a flat GREEN screen so an open border is visible (green
spilling into the overscan). It exists to calibrate/exercise the VBL-entry beam-sync in isolation
(once it opens reliably, a real demo is the same skeleton + effects).

**The robust skeleton now lives in the toolkit** (`lockstep.skeleton.OverscanFrame`, W1) — this
file is a thin demo shell over it: it supplies the green `_setup` (screen fill / palette / video
base) and drives `OverscanFrame` for the two builds:
  - `build_robust()` -> `bordws.tos`: all four borders open on all four wakestates, flicker-free,
    pure lock-once full-sync (stable MMU lock + left stabiliser + cross-boundary bottom bust);
  - plain `build()` -> `bordopen.tos`: the original Aurora lock (all-4 on ws1/ws3 only).

Certify with the W2 tool: `python -m pytest tests/test_wakestate.py` (bordws => all 4 WS; bordopen
=> ws2/ws4 fail), or `lockstep.wakestate.verify_overscan(prog)`. Shoot a single frame with
`lockstep.visual.shoot_tos` / `shoot_counter`. See `README.md` for the wakestate lore.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# The robust skeleton is a first-class toolkit object now; re-export the pieces demos use.
from lockstep.skeleton import (DEFAULT_SYNC, HBL_HANDLER, OverscanFrame,   # noqa: E402,F401
                               SyncConfig, _allborders, robust_bands, robust_sync)

SyncCfg = SyncConfig          # historical name kept for back-compat
ROBUST = DEFAULT_SYNC         # the stable Aurora MMU lock-once — pure full-sync (no HBL/stop)

SCREEN = 0xA8000              # white screen buffer base (aligned, low byte 0)
PROBE = 0x1000               # post-bands frame counter for capturing bottom-OPEN frames (which
                             # stall Hatari's nVBLs). Placed AFTER all border switches so it can't
                             # perturb the sync/border timing. Low addr => parse-valid for a Hatari
                             # memory-condition breakpoint (shoot_counter).


def _setup(cfg: SyncConfig = DEFAULT_SYNC) -> str:
    # one-time: palette (border black / colour 15 green), fill the screen white at SCREEN, point
    # the video base there, init the border-switch registers. For the HBL-locked sync, also install
    # a bare HBL handler ($68) so `stop #$2100` has somewhere to return from.
    hbl = ("    move.l  #__hbl,$68.w        ; HBL handler for the stop-on-HBL re-sync\n"
           if cfg.coarse == "hbl" else "")
    return f"""\
{hbl}    move.w  #$0000,$ffff8240    ; palette[0] = black  (the BORDER colour)
    move.w  #$0070,$ffff825e    ; palette[15] = GREEN (display fill — distinct from the grey
                                ;   EmuTOS desktop, so a screenshot can't mistake a failed
                                ;   launch for an open border)
    move.l  #${SCREEN:x},a2
    move.w  #$3fff,d0
.scrfill:
    move.l  #$ffffffff,(a2)+    ; fill 64KB white (all four planes set)
    dbra    d0,.scrfill
    move.b  #${(SCREEN >> 16) & 0xff:02x},$ffff8201   ; video base high
    move.b  #${(SCREEN >> 8) & 0xff:02x},$ffff8203   ; video base mid
    lea     $ffff8260,a1
    moveq   #2,d3
    moveq   #0,d4
"""


def build(out_path: str, cfg: SyncConfig = DEFAULT_SYNC, *, main_lines: int = 227,
          bot_lines: int = 32, bust: bool = True, bust_at: int = 496, probe: bool = False,
          left_nops: int = 0, bot_nops: int = 0, cross: bool = False, set_off: int = 500,
          restore_off: int = 20) -> str:
    """Assemble a bordopen `.TOS` with the given sync config via `OverscanFrame`. Returns the path.

    DEFAULT = all four borders open — Aurora's exact 227/1/32 band stack (original lock: all-4 on
    ws1/ws3 only; the wakestate frontier is closed by `build_robust`). `bust=False` = the simpler
    top+left+right open. A bottom-OPEN frame stalls Hatari's nVBLs — capture it with `probe=True`
    + `lockstep.visual.shoot_counter`."""
    tail = (f"\n    addq.l  #1,${PROBE:x}            ; post-frame counter (capture trigger)"
            if probe else "")
    frame = OverscanFrame(main_lines=main_lines, bot_lines=bot_lines, left_nops=left_nops,
                          bot_nops=bot_nops, bust=bust, cross=cross, bust_at=bust_at,
                          set_off=set_off, restore_off=restore_off, sync=cfg)
    setup = (f"    clr.l   ${PROBE:x}\n" if probe else "") + _setup(cfg)
    return frame.build(out_path, setup=setup, tail=tail, exit_on_key=False)


def build_robust(out_path: str, *, main_lines: int = 227, left_nops: int = 1,
                 bot_nops: int = 0, bust: bool = True, cross: bool = True, **kw) -> str:
    """Build the wakestate-robust bordopen `.TOS`: stable MMU lock + left stabiliser (left_nops=1)
    + cross-boundary bottom bust (cross=True). ALL FOUR borders open AND flicker-free on all 4 WS,
    pure lock-once full-sync. (cross=False => top+left+right only, bottom on ws1/ws3.)"""
    return build(out_path, ROBUST, main_lines=main_lines, left_nops=left_nops,
                 bot_nops=bot_nops, bust=bust, cross=cross, **kw)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    p = build(os.path.join(here, "bordopen.tos"))
    print(f"built {p} ({os.path.getsize(p)} bytes) — MMU lock-once (Aurora 227/1/32), original")
    p = build_robust(os.path.join(here, "bordws.tos"))
    print(f"built {p} ({os.path.getsize(p)} bytes) — wakestate-ROBUST (stabiliser + cross-bust): "
          f"ALL 4 borders STABLE on all 4 WS, pure full-sync")
