"""Lockstep verifier — confirm a packed routine is 512c/line on real silicon (DESIGN §3+§7).

Closes the P3 oracle loop on P5 output: pack a routine, drop a label at the start of every
scanline, run it headless in cycle-exact Hatari (`st68k.hatari.measure_markers`), and read
the FrameCycles delta across each line. The static model already *guarantees* every line is
line_len (expand() validates each region); this proves the per-instruction costs the packer
used are right on the actual emitted stream, and reports where the beam sits at each line.

Cycle cost is address-independent for the ops in a border template (border/shifter writes
carry no wait state — TIMING.md), so the default harness points the work pointers at scratch
RAM: same cycle count, no side effects under `--disable-video`. Pass a custom `setup` for
faithful addresses (real border regs, a real buffer) when that matters (e.g. PSG/SNDH later).
"""

from __future__ import annotations

from dataclasses import dataclass

from st68k.cycles import CycleEngine
from st68k.hatari import HatariError, Marker, measure_markers

from .packer import PackResult, pack

# Registers the border idiom + scroller use, aimed at scratch RAM (1MB machine, payload at
# $80000): a6 = work buffer with headroom; a0/a1 = byte-write targets well above it.
DEFAULT_SETUP = """\
    move.l  #$90000,a6         ; scroller buffer base (scratch RAM)
    move.l  #$f0000,a0         ; (a0) border-write target stand-in (scratch)
    move.l  #$f0000,a1         ; (a1) border-write target stand-in (scratch)
    moveq   #0,d3
    moveq   #0,d4
"""


@dataclass
class VerifyResult:
    expected_per_line: list[int]    # static target per scanline (per its band's line_len)
    n_lines: int
    per_line_cycles: list[int]      # measured FrameCycles delta for each scanline
    markers: dict[str, Marker]      # label -> Marker (beam position at each line start)
    pack: PackResult
    raw_setup: str

    @property
    def ok(self) -> bool:
        return self.per_line_cycles == self.expected_per_line

    def report(self) -> str:
        out = [f"lockstep verify: {self.n_lines} line(s)"]
        labels = [f"__l{i}" for i in range(self.n_lines)]
        for i, c in enumerate(self.per_line_cycles):
            m = self.markers[labels[i]]
            exp = self.expected_per_line[i]
            verdict = "ok " if c == exp else f"OFF {c - exp:+d}c (want {exp})"
            out.append(f"  line {i:3}: {c:4}c  {verdict}   "
                       f"(enters at HBL {m.hbl}, line-cycle {m.linecycles})")
        ok_msg = "ALL LINES on budget — borders hold" if self.ok else "DRIFT — see above"
        out.append(f"  => {ok_msg}")
        return "\n".join(out)


_BUDGET_RE = __import__("re").compile(r";@budget\s+(\d+)")


def _expected_per_line(asm: str) -> list[int]:
    """The static per-scanline budget (from each `;@budget N    ; --- scanline …`)."""
    return [int(_BUDGET_RE.search(ln).group(1))
            for ln in asm.splitlines() if "--- scanline" in ln]


def _label_scanlines(asm: str, n_lines: int) -> tuple[str, int]:
    """Inject `__lN:` at each scanline start (the `; --- scanline N ---` boundary) and a
    final `__lE:` + settle loop so the last line's end is a stable marker."""
    out: list[str] = []
    seen = 0
    for line in asm.splitlines():
        if "--- scanline" in line:
            out.append(f"__l{seen}:")
            seen += 1
        out.append(line)
    out.append("__lE:")
    out.append("    bra.s __lE")
    return "\n".join(out), seen


def _verify_packed(res: PackResult, *, setup: str | None, run_vbls: int,
                   timeout: float) -> VerifyResult:
    """Label every scanline of a packed routine and measure each line's cost in Hatari."""
    n_lines = res.n_lines
    labelled, seen = _label_scanlines(res.asm, n_lines)
    if seen != n_lines:
        raise HatariError(f"expected {n_lines} scanline markers in packed asm, found {seen}")

    setup_src = DEFAULT_SETUP if setup is None else setup
    # measure as real full-sync code: mask all interrupts so no ISR (HBL/VBL/Timer-C)
    # cycles intrude between the per-line markers. The harness has already entered
    # supervisor, so writing SR is legal.
    body = "    move    #$2700,sr      ; interrupts off (full-sync)\n" + setup_src + "\n" + labelled
    labels = [f"__l{i}" for i in range(n_lines)] + ["__lE"]
    markers = measure_markers(body, labels, run_vbls=run_vbls, timeout=timeout)

    gc = [markers[lab].global_cycles for lab in labels]
    per_line = [gc[i + 1] - gc[i] for i in range(n_lines)]
    return VerifyResult(_expected_per_line(res.asm), n_lines, per_line, markers,
                        res, setup_src)


def verify(template, work, n_lines: int, *, setup: str | None = None,
           engine: CycleEngine | None = None, run_vbls: int = 400,
           timeout: float = 120.0) -> VerifyResult:
    """Pack one template and measure the result in Hatari, per scanline. Raises HatariError
    if the emulator/assembler is unavailable or a marker never fires; PackError if packing
    fails."""
    engine = engine or CycleEngine()
    res = pack(template, work, n_lines, engine=engine)
    return _verify_packed(res, setup=setup, run_vbls=run_vbls, timeout=timeout)


def verify_segments(segments, *, setup: str | None = None,
                    engine: CycleEngine | None = None, run_vbls: int = 400,
                    timeout: float = 120.0) -> VerifyResult:
    """Verify a multi-band screen (a list of Segment / (template, work, n_lines)) — pack via
    pack_schedule, then measure every scanline in Hatari regardless of which band it is in."""
    from .packer import pack_schedule
    engine = engine or CycleEngine()
    res = pack_schedule(segments, engine=engine)
    return _verify_packed(res, setup=setup, run_vbls=run_vbls, timeout=timeout)


def verify_spec(text: str, *, setup: str | None = None,
                engine: CycleEngine | None = None, run_vbls: int = 400,
                timeout: float = 120.0) -> list[tuple[str, int, VerifyResult]]:
    """Parse a spec and verify every ;@schedule / ;@screen in Hatari.
    Returns [(label, n_lines, VerifyResult), ...]."""
    from .directives import ScheduleError, _resolve_segments, parse
    spec = parse(text)
    if not spec.items:
        raise ScheduleError("no ;@schedule or ;@screen directive — nothing to verify")
    out = []
    for item in spec.items:
        if item[0] == "single":
            _, tname, nlines, lineno = item
            if tname not in spec.templates:
                raise ScheduleError(f"line {lineno}: ;@schedule of unknown template {tname!r}")
            vr = verify(spec.templates[tname], spec.default_work, nlines, setup=setup,
                        engine=engine, run_vbls=run_vbls, timeout=timeout)
            out.append((tname, nlines, vr))
        else:
            _, segs, lineno = item
            segments = _resolve_segments(spec, segs, lineno)
            vr = verify_segments(segments, setup=setup, engine=engine,
                                 run_vbls=run_vbls, timeout=timeout)
            out.append((f"screen({len(segments)} seg)", vr.n_lines, vr))
    return out
