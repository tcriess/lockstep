"""Lockstep — VISUAL verification (the capstone's seeing-is-believing gate).

The cycle verifier (`verify.py`) proves every line is 512c with `--disable-video`; it can't
prove the timing actually *opens the borders*. This module runs a full-sync routine with
**video on** and **borders shown**, captures the rendered frame headless (Hatari's debugger
`screenshot` command, reused via a relocating harness), and measures the displayed region —
so "the borders opened" becomes a number, not a vibe.

To see a border open you need display content whose colour differs from the border (which is
always palette entry 0): fill the screen with a non-zero colour, set palette[0]=black, and a
border that opens shows that colour spilling into the overscan. `active_bbox` returns the
bounding box of non-border pixels; a borders-open frame is wider/taller than a normal one.
"""

from __future__ import annotations

import glob
import os
import subprocess
import tempfile
from dataclasses import dataclass

from st68k.hatari import DEST, HATARI, VASM, HatariError, _indent, _parse_symbols, find_tos

_HARNESS = """\
    text
__strt:
    clr.l   -(sp)
    move.w  #$20,-(sp)
    trap    #1
    addq.l  #6,sp
    lea     __pl(pc),a0
    move.l  #{dest},a1
    move.w  #__ple-__pl-1,d0
.cp:
    move.b  (a0)+,(a1)+
    dbra    d0,.cp
    jmp     {dest}
__pl:
{setup}
__frame:
{body}
    bra     __frame
__ple:
"""


@dataclass
class Capture:
    png: str
    width: int
    height: int


def capture(body: str, png: str, *, setup: str = "", at_vbl: int = 360,
            borders: bool = True, video_timing: str = "ws3", tos: str | None = None,
            run_vbls: int = 700, timeout: float = 180.0) -> Capture:
    """Run `setup` then `body` in a loop (one full-sync frame per iteration) with video on,
    and screenshot a stable frame to `png` once Hatari's frame counter passes `at_vbl` (well
    after EmuTOS boot, ~VBL 294, so the looping demo has rendered many identical frames).
    `body` is one frame of full-sync code that writes the real shifter/sync registers; the
    harness adds the loop. Returns the PNG path + dimensions."""
    import shutil
    if shutil.which(VASM) is None or shutil.which(HATARI) is None:
        raise HatariError("vasm or hatari not found")
    tos = tos or find_tos()

    src = _HARNESS.format(dest=f"${DEST:x}", setup=_indent(setup), body=_indent(body))
    work = tempfile.mkdtemp(prefix="lockstep_vis_")
    try:
        s_path = os.path.join(work, "vis.s")
        prog = os.path.join(work, "VIS.TOS")
        open(s_path, "w").write(src)
        r = subprocess.run([VASM, "-Ftos", "-o", prog, s_path], capture_output=True, text=True)
        if r.returncode != 0:
            raise HatariError(f"vasm failed:\n{r.stdout}\n{r.stderr}")
        return _shoot(prog, "VIS.TOS", png, work, at_vbl=at_vbl, borders=borders,
                      video_timing=video_timing, tos=tos, run_vbls=run_vbls, timeout=timeout)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _shoot(prog: str, dos_name: str, png: str, work: str, *, at_vbl: int, borders: bool,
           video_timing: str, tos: str, run_vbls: int, timeout: float) -> "Capture":
    """Autostart `prog` (a .TOS) headless with video on and screenshot a frame past at_vbl."""
    cmds = os.path.join(work, "cap.cmds")
    open(cmds, "w").write(f"screenshot {png}\nc\n")
    parse = os.path.join(work, "parse.ini")
    # fire once Hatari's frame counter passes at_vbl (Hatari supports < > = !, not >=)
    open(parse, "w").write(f"b VBL > {at_vbl} :once :file {cmds}\n")
    env = dict(os.environ, HOME=os.path.join(work, "home"),
               SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    os.makedirs(env["HOME"], exist_ok=True)
    cmd = [
        HATARI, "--machine", "st", "--memsize", "4", "--cpu-exact", "on",
        "--sound", "off", "--borders", "on" if borders else "off", "--crop", "off",
        "--statusbar", "off", "--drive-led", "off",
        "--video-timing", video_timing, "--tos", tos, "--screenshot-dir", work,
        "--screenshot-format", "png", "--run-vbls", str(run_vbls),
        "--parse", parse, "--auto", "C:\\" + dos_name, prog,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    if not os.path.exists(png):
        found = glob.glob(os.path.join(work, "*.png"))
        if found:
            os.replace(found[0], png)
        else:
            raise HatariError("screenshot was not produced:\n" + (r.stdout + r.stderr)[-1500:])
    from PIL import Image
    with Image.open(png) as im:
        w, h = im.size
    return Capture(png, w, h)


def screenshot_tos(prog: str, png: str, *, at_vbl: int = 360, borders: bool = True,
                   video_timing: str = "ws3", tos: str | None = None, run_vbls: int = 700,
                   timeout: float = 200.0) -> "Capture":
    """Run a pre-built standalone .TOS headless (video on, borders shown) and screenshot a
    frame once past `at_vbl`. Used to verify an `emit_program` demo actually boots and runs."""
    import shutil
    if shutil.which(HATARI) is None:
        raise HatariError("hatari not found")
    work = tempfile.mkdtemp(prefix="lockstep_tos_")
    try:
        return _shoot(prog, os.path.basename(prog).upper(), png, work, at_vbl=at_vbl,
                      borders=borders, video_timing=video_timing, tos=tos or find_tos(),
                      run_vbls=run_vbls, timeout=timeout)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def shoot_counter(prog: str, png: str, *, count_addr: int, count: int = 40,
                  video_timing: str = "ws3", borders: bool = True, tos: str | None = None,
                  timeout: float = 90.0) -> "Capture":
    """Screenshot a standalone full-sync .TOS by firing on the demo's OWN frame counter (a
    longword the VBL handler bumps at the fixed absolute `count_addr`), NOT Hatari's nVBLs.

    Needed once the bottom border is genuinely removed: that strips the vblank nVBLs counts, so
    `VBL > N` stalls and fires on an unpredictable, possibly-unsettled frame. The demo's own
    counter keeps ticking every $70 VBL regardless, so `b (count_addr).l > count` fires on a
    settled frame deterministically. `count_addr` must be low (Hatari validates memory-condition
    addresses against a small parse-time memory; high addresses are rejected). Breakpoint ends
    in `quit` so Hatari exits the instant the shot is taken."""
    import shutil
    if shutil.which(HATARI) is None:
        raise HatariError("hatari not found")
    tos = tos or find_tos()
    work = tempfile.mkdtemp(prefix="lockstep_cnt_")
    dos_name = os.path.basename(prog).upper()
    try:
        cmds = os.path.join(work, "cap.cmds")
        open(cmds, "w").write(f"screenshot {png}\nquit\n")
        parse = os.path.join(work, "parse.ini")
        open(parse, "w").write(f"b (${count_addr:x}).l > {count} :once :file {cmds}\n")
        env = dict(os.environ, HOME=os.path.join(work, "home"),
                   SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        os.makedirs(env["HOME"], exist_ok=True)
        cmd = [
            HATARI, "--machine", "st", "--memsize", "4", "--cpu-exact", "on",
            "--sound", "off", "--borders", "on" if borders else "off", "--crop", "off",
            "--statusbar", "off", "--drive-led", "off",
            "--video-timing", video_timing, "--tos", tos, "--screenshot-dir", work,
            "--screenshot-format", "png", "--run-vbls", "100000",
            "--parse", parse, "--auto", "C:\\" + dos_name, prog,
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
            tail = (r.stdout + r.stderr)[-1500:]
        except subprocess.TimeoutExpired:
            tail = "(hatari did not quit — counter never reached / demo hung / crashed?)"
        if not os.path.exists(png):
            found = glob.glob(os.path.join(work, "*.png"))
            if found:
                os.replace(found[0], png)
            else:
                raise HatariError("screenshot was not produced:\n" + tail)
        from PIL import Image
        with Image.open(png) as im:
            w, h = im.size
        return Capture(png, w, h)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def shoot_tos(prog: str, png: str, *, at_vbl: int = 320, video_timing: str = "ws3",
              borders: bool = True, tos: str | None = None, timeout: float = 60.0) -> "Capture":
    """Screenshot a standalone full-sync .TOS, fast and reliably. Fires on Hatari's frame
    counter (`b VBL > at_vbl`) and the breakpoint command ends in `quit`, so Hatari exits the
    instant the shot is taken — never waiting out `--run-vbls` (slow under --cpu-exact: the
    earlier capture path hung purely because it used `c` and ran to the vbls limit). `at_vbl`
    just needs to be a little past EmuTOS boot (~294) so the demo has run a few settled frames;
    nVBLs keeps advancing through an all-borders-open frame, so no special trigger is needed.
    Typical wall-clock: ~7s."""
    import shutil
    if shutil.which(HATARI) is None:
        raise HatariError("hatari not found")
    tos = tos or find_tos()
    work = tempfile.mkdtemp(prefix="lockstep_shoot_")
    dos_name = os.path.basename(prog).upper()
    try:
        cmds = os.path.join(work, "cap.cmds")
        open(cmds, "w").write(f"screenshot {png}\nquit\n")
        parse = os.path.join(work, "parse.ini")
        open(parse, "w").write(f"b VBL > {at_vbl} :once :file {cmds}\n")
        env = dict(os.environ, HOME=os.path.join(work, "home"),
                   SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        os.makedirs(env["HOME"], exist_ok=True)
        cmd = [
            HATARI, "--machine", "st", "--memsize", "4", "--cpu-exact", "on",
            "--sound", "off", "--borders", "on" if borders else "off", "--crop", "off",
            "--statusbar", "off", "--drive-led", "off",
            "--video-timing", video_timing, "--tos", tos, "--screenshot-dir", work,
            "--screenshot-format", "png", "--run-vbls", str(at_vbl + 4000),
            "--parse", parse, "--auto", "C:\\" + dos_name, prog,
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
            tail = (r.stdout + r.stderr)[-1500:]
        except subprocess.TimeoutExpired:
            tail = "(hatari did not quit within timeout — VBL trigger never fired / demo hung?)"
        if not os.path.exists(png):
            found = glob.glob(os.path.join(work, "*.png"))
            if found:
                os.replace(found[0], png)
            else:
                raise HatariError("screenshot was not produced:\n" + tail)
        from PIL import Image
        with Image.open(png) as im:
            w, h = im.size
        return Capture(png, w, h)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def active_bbox(png: str, border=None) -> tuple[int, int, int, int]:
    """Bounding box (left, top, right, bottom, inclusive) of pixels that differ from the
    border colour (default: the top-left corner pixel, which is always border)."""
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(png).convert("RGB"))
    if border is None:
        border = tuple(int(v) for v in a[0, 0])
    mask = np.any(a != np.array(border, dtype=a.dtype), axis=2)
    if not mask.any():
        return (0, 0, 0, 0)
    ys, xs = np.where(mask)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
