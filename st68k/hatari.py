"""P3 — the Hatari oracle: measure the *real* cycle cost of a chunk, cycle-exactly.

Mechanism (proven against this Hatari build, v2.6.0-devel):
  - wrap the chunk in a self-relocating harness that copies a payload to a fixed
    absolute address ($80000) and jumps there, so the markers sit at known PC
    addresses (no symbol-relocation timing problem);
  - assemble with vasm (keeping the DRI symbol table) to read the marker offsets;
  - run Hatari headless (clean HOME, dummy SDL, --disable-video, --cpu-exact) and
    autostart the program, with PC breakpoints whose `:info default` action prints
    `CPU=.. VBL=.. FrameCycles=.. HBL=.. LineCycles=..` and trace-continues;
  - the FrameCycles delta between the two markers is the exact cycle cost; HBL /
    LineCycles give the beam position at each marker (the beam-race ingredient).

This is the ground truth the static engine (cycles.py) is reconciled against (DESIGN §3),
and the enabler for the bus-phase model, SNDH worst-case profiling, and beam-race.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass

VASM = os.environ.get("STCYC_VASM", "vasmm68k_mot")
HATARI = os.environ.get("STCYC_HATARI", "hatari")
DEST = 0x80000                      # fixed run address for the payload (free RAM, 1MB)
CYCLES_PER_FRAME = 160256           # PAL; only matters if a chunk spans a VBL

_TOS_CANDIDATES = [
    os.environ.get("STCYC_TOS", ""),
    "/home/spanz/hatari/roms/etos256de.img",
    "/home/spanz/hatari/roms/TOS104GE.IMG",
    "/home/spanz/hatari/roms/tos206de.img",
]

_HARNESS = """\
    text
__strt:
    clr.l   -(sp)              ; Super(0): enter supervisor mode (real sync code runs
    move.w  #$20,-(sp)         ; in supervisor; needed to touch $ffff8xxx IO)
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
__m0:
{chunk}
__m1:
    bra.s   __m1
__ple:
"""

_INFO_RE = re.compile(
    r"CPU=\$([0-9a-fA-F]+), VBL=(-?\d+), FrameCycles=(-?\d+), "
    r"HBL=(-?\d+), LineCycles=(-?\d+)")


class HatariError(Exception):
    pass


@dataclass
class Marker:
    addr: int
    vbl: int
    framecycles: int
    hbl: int            # scanline within the frame
    linecycles: int     # cycle within the scanline

    @property
    def global_cycles(self) -> int:
        return self.vbl * CYCLES_PER_FRAME + self.framecycles


@dataclass
class Measurement:
    cycles: int         # real cycle cost of the chunk (m1 - m0)
    start: Marker
    end: Marker
    spans_vbl: bool
    raw: str

    @property
    def beam(self) -> str:
        return f"line {self.start.hbl} cyc {self.start.linecycles} -> line {self.end.hbl} cyc {self.end.linecycles}"


def find_tos() -> str:
    for p in _TOS_CANDIDATES:
        if p and os.path.exists(p):
            return p
    raise HatariError("no TOS/EmuTOS image found; set STCYC_TOS to an ST ROM image")


def _parse_symbols(tos_path: str) -> dict[str, int]:
    d = open(tos_path, "rb").read()
    tl = int.from_bytes(d[2:6], "big")
    dl = int.from_bytes(d[6:10], "big")
    sl = int.from_bytes(d[14:18], "big")
    off = 28 + tl + dl
    syms: dict[str, int] = {}
    skip_next = False
    for i in range(off, off + sl, 14):
        if skip_next:                       # DRI long-name continuation entry
            skip_next = False
            continue
        name = d[i:i + 8].split(b"\x00")[0].decode("latin1").strip()
        typ = int.from_bytes(d[i + 8:i + 10], "big")
        val = int.from_bytes(d[i + 10:i + 14], "big")
        syms[name] = val
        if typ & 0x0048 == 0x0048:
            skip_next = True
    return syms


def measure(chunk: str, *, setup: str = "", tos: str | None = None,
            run_vbls: int = 400, timeout: float = 90.0) -> Measurement:
    """Measure the real cycle cost of `chunk` (asm text). `setup` runs before the
    measured region (load registers etc.). Returns a Measurement."""
    if shutil.which(VASM) is None:
        raise HatariError(f"assembler {VASM!r} not found")
    if shutil.which(HATARI) is None:
        raise HatariError(f"emulator {HATARI!r} not found")
    tos = tos or find_tos()

    src = _HARNESS.format(dest=f"${DEST:x}",       # vasm hex, not Python 0x...
                          setup=_indent(setup), chunk=_indent(chunk))
    work = tempfile.mkdtemp(prefix="stcyc_hat_")
    try:
        s_path = os.path.join(work, "measure.s")
        tos_prog = os.path.join(work, "MEASURE.TOS")
        open(s_path, "w").write(src)

        r = subprocess.run([VASM, "-Ftos", "-no-opt", "-m68000", "-no-fpu", "-o", tos_prog, s_path],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise HatariError(f"vasm failed:\n{r.stdout}\n{r.stderr}")

        syms = _parse_symbols(tos_prog)
        for m in ("__pl", "__m0", "__m1"):
            if m not in syms:
                raise HatariError(f"marker {m} missing from symbol table {list(syms)}")
        m0_addr = DEST + (syms["__m0"] - syms["__pl"])
        m1_addr = DEST + (syms["__m1"] - syms["__pl"])

        parse_ini = os.path.join(work, "parse.ini")
        open(parse_ini, "w").write(
            f"b pc=${m0_addr:x} :once :info default\n"
            f"b pc=${m1_addr:x} :once :info default\n")

        env = dict(os.environ, HOME=os.path.join(work, "home"),
                   SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        os.makedirs(env["HOME"], exist_ok=True)
        cmd = [
            HATARI, "--machine", "st", "--memsize", "1", "--cpu-exact", "on",
            "--sound", "off", "--disable-video", "on", "--tos", tos,
            "--run-vbls", str(run_vbls), "--parse", parse_ini,
            "--auto", "C:\\MEASURE.TOS", tos_prog,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        raw = r.stdout + r.stderr

        markers: dict[int, Marker] = {}
        for line in raw.splitlines():
            mm = _INFO_RE.search(line)
            if not mm:
                continue
            addr = int(mm.group(1), 16)
            markers[addr] = Marker(addr, int(mm.group(2)), int(mm.group(3)),
                                   int(mm.group(4)), int(mm.group(5)))
        if m0_addr not in markers or m1_addr not in markers:
            raise HatariError(
                f"markers did not both fire (m0=${m0_addr:x} hit={m0_addr in markers}, "
                f"m1=${m1_addr:x} hit={m1_addr in markers}); chunk may crash or boot was "
                f"too slow (raise run_vbls).")
        m0, m1 = markers[m0_addr], markers[m1_addr]
        return Measurement(m1.global_cycles - m0.global_cycles, m0, m1,
                           m1.vbl != m0.vbl, raw)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _indent(asm: str) -> str:
    return "\n".join(("    " + ln if ln.strip() and not ln.startswith((" ", "\t"))
                      else ln) for ln in asm.splitlines())


# --- multi-marker variant (used by the lockstep scheduler's per-line verifier) ---

_HARNESS_MULTI = """\
    text
__strt:
    clr.l   -(sp)
    move.w  #$20,-(sp)          ; Super(0)
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
{body}
__ple:
"""


def measure_markers(body: str, labels: list[str], *, tos: str | None = None,
                    run_vbls: int = 400, timeout: float = 120.0) -> dict[str, Marker]:
    """Like `measure`, but `body` defines its own `labels:` (e.g. one per scanline) and a
    PC breakpoint is set at each. Returns {label: Marker}. `body` should run straight-line
    through every label and end parked (a `bra.s` self-loop) so the last marker settles.

    The cycle cost between two labels is the FrameCycles/global_cycles delta of their
    Markers — this is what the lockstep verifier uses to confirm each packed line is 512c.
    """
    if shutil.which(VASM) is None:
        raise HatariError(f"assembler {VASM!r} not found")
    if shutil.which(HATARI) is None:
        raise HatariError(f"emulator {HATARI!r} not found")
    tos = tos or find_tos()

    src = _HARNESS_MULTI.format(dest=f"${DEST:x}", body=_indent(body))
    work = tempfile.mkdtemp(prefix="stcyc_hatm_")
    try:
        s_path = os.path.join(work, "measure.s")
        tos_prog = os.path.join(work, "MEASURE.TOS")
        open(s_path, "w").write(src)

        r = subprocess.run([VASM, "-Ftos", "-no-opt", "-m68000", "-no-fpu", "-o", tos_prog, s_path],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise HatariError(f"vasm failed:\n{r.stdout}\n{r.stderr}")

        syms = _parse_symbols(tos_prog)
        if "__pl" not in syms:
            raise HatariError("payload base __pl missing from symbol table")
        addr_of = {}
        bp_lines = []
        for lab in labels:
            if lab not in syms:
                raise HatariError(f"label {lab!r} missing from symbol table {list(syms)}")
            a = DEST + (syms[lab] - syms["__pl"])
            addr_of[lab] = a
            bp_lines.append(f"b pc=${a:x} :once :info default\n")

        parse_ini = os.path.join(work, "parse.ini")
        open(parse_ini, "w").write("".join(bp_lines))

        env = dict(os.environ, HOME=os.path.join(work, "home"),
                   SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        os.makedirs(env["HOME"], exist_ok=True)
        cmd = [
            HATARI, "--machine", "st", "--memsize", "1", "--cpu-exact", "on",
            "--sound", "off", "--disable-video", "on", "--tos", tos,
            "--run-vbls", str(run_vbls), "--parse", parse_ini,
            "--auto", "C:\\MEASURE.TOS", tos_prog,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        raw = r.stdout + r.stderr

        by_addr: dict[int, Marker] = {}
        for line in raw.splitlines():
            mm = _INFO_RE.search(line)
            if mm:
                a = int(mm.group(1), 16)
                by_addr[a] = Marker(a, int(mm.group(2)), int(mm.group(3)),
                                    int(mm.group(4)), int(mm.group(5)))
        out: dict[str, Marker] = {}
        missing = []
        for lab in labels:
            m = by_addr.get(addr_of[lab])
            if m is None:
                missing.append(lab)
            else:
                out[lab] = m
        if missing:
            raise HatariError(
                f"markers did not all fire: missing {missing} "
                f"(routine may crash, or boot too slow — raise run_vbls)")
        return out
    finally:
        shutil.rmtree(work, ignore_errors=True)
