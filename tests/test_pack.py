"""P5 tests: the Lockstep packer (DESIGN §7.2).

Pour a work stream into a line template and confirm the placement is cycle-exact: every
scanline closes on 512c, pegs land on their declared offsets, and the constraint failures
(atomic block too big, work overflow, overlapping pegs) surface loudly instead of mis-sizing.
The flagship case is the Aurora all-borders-open line (DESIGN §2.1) — the packer should
reproduce the hand-tuned 11-columns-then-flip structure, generated.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lockstep import (LineTemplate, Move, Peg, Segment, StepWork,   # noqa: E402
                      WorkBlock, WorkStream, pack, pack_schedule)
from lockstep.packer import PackError                              # noqa: E402
from st68k.annotate import block_cycles                           # noqa: E402
from st68k.cycles import CycleEngine                              # noqa: E402

# The "all borders open" template at the offsets the toolkit actually ships
# (lockstep/skeleton.py:48-52): left flip at line start, right 60/50 Hz toggle at 376c, an extra
# left flip at 444c. Gaps: 360c / 52c / 48c -> dcb.w 90 / 13 / 12, Aurora's own hand counts.
ALLBORDERS = LineTemplate([
    Peg(0,   "move.b d3,(a1)\nmove.b d4,(a1)", "left"),
    Peg(376, "move.b d4,(a0)\nmove.b d3,(a0)", "right"),
    Peg(444, "move.b d3,(a1)\nnop\nmove.b d4,(a1)", "extra"),
])
# one scroller column = move.l + addq = 24 + 8 = 32c (oracle-confirmed, see TIMING.md)
COLUMN = "move.l 8(a6),(a6)+\naddq #4,a6"


def _scanline_regions(asm):
    """Split expanded asm into per-scanline blocks at the budget markers."""
    blocks, cur = [], []
    for ln in asm.splitlines():
        if "--- scanline" in ln and cur:
            blocks.append("\n".join(cur))
            cur = []
        cur.append(ln)
    if cur:
        blocks.append("\n".join(cur))
    return blocks


def test_every_scanline_is_exactly_512():
    work = WorkStream.repeat(COLUMN, n=39, label="col")
    res = pack(ALLBORDERS, work, n_lines=3)
    assert res.complete and res.units_placed == 39
    # the whole packed routine is n * 512
    assert block_cycles(res.asm) == (3 * 512, 3 * 512)
    # and each scanline in isolation is 512c (re-timed independently)
    eng = CycleEngine()
    regions = _scanline_regions(res.asm)
    assert len(regions) == 3
    for r in regions:
        assert block_cycles(r, eng) == (512, 512)


def test_reproduces_aurora_column_count():
    # DESIGN §2.1 / aurora.s:843 — the first gap (16c..376c = 360c) holds exactly 11
    # columns (352c), then 8c of nop filler before the right-border flip.
    work = WorkStream.repeat(COLUMN, n=39, label="col")
    res = pack(ALLBORDERS, work, n_lines=3)
    sl0 = res.intermediate.split(";@end")[0]
    before_right = sl0.split(";@pad 376")[0]
    assert before_right.count("move.l 8(a6),(a6)+") == 11
    # 13 columns per line total (11 + 1 + 1), as in the hand-tuned loop
    assert res.placed_per_line == [13, 13, 13]


def test_pegs_land_on_their_offsets():
    work = WorkStream.repeat(COLUMN, n=39, label="col")
    res = pack(ALLBORDERS, work, n_lines=3)
    pads = {r.detail.split(":")[0] for r in res.report if r.kind == "pad"}
    assert "@pad 376" in pads and "@pad 444" in pads
    assert all(r.ok for r in res.report)


def test_output_is_pure_asm():
    # directives are comments; the expanded code carries no stray '@'
    work = WorkStream.repeat(COLUMN, n=13, label="col")
    res = pack(ALLBORDERS, work, n_lines=1)
    for line in res.asm.splitlines():
        assert "@" not in line.split(";", 1)[0]


def test_splittable_block_is_cut_at_a_peg():
    # a splittable column can be cut between its move.l and addq; with a peg at 24c the
    # 24c move.l fills the gap and the addq lands after the flip.
    tmpl = LineTemplate([Peg(24, "move.b d3,(a1)", "flip")], line_len=512)
    split = WorkStream([__import__("lockstep").WorkBlock(COLUMN, splittable=True)])
    res = pack(tmpl, split, n_lines=1)
    head = res.intermediate.split(";@pad 24")[0]
    tail = res.intermediate.split(";@pad 24")[1]
    assert "move.l 8(a6),(a6)+" in head        # the move.l fit before the peg
    assert "addq #4,a6" in tail                 # the addq spilled past it


def test_atomic_block_stays_whole():
    # the same column as one ATOMIC block does NOT fit the 24c gap (it is 32c), so it is
    # pushed past the peg in one piece — nothing before the flip.
    tmpl = LineTemplate([Peg(24, "move.b d3,(a1)", "flip")], line_len=512)
    atomic = WorkStream.repeat(COLUMN, n=1)     # atomic by default
    res = pack(tmpl, atomic, n_lines=1)
    head = res.intermediate.split(";@pad 24")[0]
    assert "move.l 8(a6),(a6)+" not in head


def test_atomic_block_too_big_errors():
    tmpl = LineTemplate([Peg(20, "nop")], line_len=40)   # biggest gap = 20c
    work = WorkStream.repeat("move.l 8(a6),(a6)+", n=1)   # 24c > 20c
    try:
        pack(tmpl, work, n_lines=1)
        assert False, "expected PackError"
    except PackError as e:
        assert "biggest gap" in str(e)


def test_work_overflow_errors():
    work = WorkStream.repeat(COLUMN, n=40, label="col")   # one column too many for 3 lines
    try:
        pack(ALLBORDERS, work, n_lines=3)
        assert False, "expected PackError"
    except PackError as e:
        assert "did not fit" in str(e)


def test_overlapping_pegs_error():
    bad = LineTemplate([
        Peg(0, "move.b d3,(a1)\nmove.b d4,(a1)", "left"),   # ends at 16c
        Peg(8, "nop", "too-early"),                          # 8 < 16 -> overlap
    ])
    try:
        pack(bad, WorkStream([]), n_lines=1)
        assert False, "expected PackError"
    except PackError as e:
        assert "overlap" in str(e)


# --- multi-variant screens: pack_schedule over bands (DESIGN §7.1) ---

# a top/bottom-border line: left flip + the vertical-border-removing switch, no scroller work
TOPBORDER = LineTemplate([
    Peg(0,   "move.b d3,(a1)\nmove.b d4,(a1)", "left"),
    Peg(380, "move.b d4,(a0)\nmove.b d3,(a0)", "vert-open"),
])


def test_pack_schedule_multi_variant_512_per_line():
    scroll = WorkStream.repeat(COLUMN, n=13)
    res = pack_schedule([
        Segment(TOPBORDER, WorkStream([]), 1),    # top-border line, border-only
        Segment(ALLBORDERS, scroll, 1),           # mid scroller line
        Segment(TOPBORDER, WorkStream([]), 1),    # bottom-border line
    ])
    assert res.n_lines == 3
    assert block_cycles(res.asm) == (3 * 512, 3 * 512)
    eng = CycleEngine()
    for region in _scanline_regions(res.asm):
        assert block_cycles(region, eng) == (512, 512)


def test_pack_schedule_per_band_work():
    res = pack_schedule([
        (TOPBORDER, WorkStream([]), 1),
        (ALLBORDERS, WorkStream.repeat(COLUMN, n=13), 1),
    ])
    sl = _scanline_regions(res.asm)
    assert "move.l 8(a6),(a6)+" not in sl[0]       # top band: border-only
    assert "move.l 8(a6),(a6)+" in sl[1]           # mid band: scroller work


def test_pack_schedule_mixes_stream_and_step_bands():
    res = pack_schedule([
        (ALLBORDERS, StepWork(steps=42, menu=MENU), 1),
        (ALLBORDERS, WorkStream.repeat(COLUMN, n=13), 1),
    ])
    assert block_cycles(res.asm) == (2 * 512, 2 * 512)


def test_pack_schedule_segment_error_names_the_band():
    try:
        pack_schedule([
            (TOPBORDER, WorkStream([]), 1),
            (ALLBORDERS, WorkStream.repeat(COLUMN, n=100), 1),   # far too much for one line
        ])
        assert False, "expected PackError"
    except PackError as e:
        assert "segment 1" in str(e) and "did not fit" in str(e)


SCREEN_SPEC = """\
;@template mid 512
;@peg 0 left
    move.b d3,(a1)
    move.b d4,(a1)
;@peg 376 right
    move.b d4,(a0)
    move.b d3,(a0)
;@peg 444 extra
    move.b d3,(a1)
    nop
    move.b d4,(a1)
;@endtemplate
;@template top 512
;@peg 0 left
    move.b d3,(a1)
    move.b d4,(a1)
;@peg 380 vert-open
    move.b d4,(a0)
    move.b d3,(a0)
;@endtemplate
;@work name=scroll repeat=13
    move.l 8(a6),(a6)+
    addq #4,a6
;@endwork
;@screen
;@segment top lines=1
;@segment mid work=scroll lines=1
;@segment top lines=1
;@endscreen
"""


def test_screen_directive_matches_pack_schedule():
    from lockstep.directives import expand_schedule
    mid = LineTemplate([
        Peg(0,   "move.b d3,(a1)\nmove.b d4,(a1)", "left"),
        Peg(376, "move.b d4,(a0)\nmove.b d3,(a0)", "right"),
        Peg(444, "move.b d3,(a1)\nnop\nmove.b d4,(a1)", "extra"),
    ])
    top = LineTemplate([
        Peg(0,   "move.b d3,(a1)\nmove.b d4,(a1)", "left"),
        Peg(380, "move.b d4,(a0)\nmove.b d3,(a0)", "vert-open"),
    ])
    py = pack_schedule([
        (top, WorkStream([]), 1),
        (mid, WorkStream.repeat(COLUMN, n=13), 1),
        (top, WorkStream([]), 1),
    ]).asm
    spec_out = expand_schedule(SCREEN_SPEC)
    body = "\n".join(l for l in spec_out.splitlines() if not l.startswith("; ===")).strip("\n")
    assert body == py.strip("\n")


# --- step-budget solver: the move.l/move.w exact-cover trick (DESIGN §7.2) ---

# long-col = move.l + addq = 32c / 4 bytes ; word-col = move.w + addq = 24c / 2 bytes
MENU = [
    Move("move.l 8(a6),(a6)+\naddq #4,a6", steps=4, label="long"),
    Move("move.w 8(a6),(a6)+\naddq #4,a6", steps=2, label="word"),
]


def test_step_solver_hits_steps_and_512():
    res = pack(ALLBORDERS, StepWork(steps=42, menu=MENU), n_lines=3)
    assert res.steps_per_line == 42
    assert block_cycles(res.asm) == (3 * 512, 3 * 512)
    # the long/word mix per line really sums to 42 steps
    longs = res.asm.count("move.l 8(a6),(a6)+") // 3
    words = res.asm.count("move.w 8(a6),(a6)+") // 3
    assert longs * 4 + words * 2 == 42


def test_step_solver_fills_a_peg_gap_with_useful_work():
    """A gap that is an exact multiple of a work unit gets filled with REAL WORK, not nops — the
    whole point of the move.l/move.w trick.

    This needs a gap of exactly 48c (= 2 word-moves), so it uses its own template with the extra peg
    at 440 rather than the shipped 444 (whose pre-peg gap is 52c and so must leave 4c of nop). The
    packer is what's under test here, not the skeleton's offsets.
    """
    exact48 = LineTemplate([
        Peg(0,   "move.b d3,(a1)\nmove.b d4,(a1)", "left"),
        Peg(376, "move.b d4,(a0)\nmove.b d3,(a0)", "right"),
        Peg(440, "move.b d3,(a1)\nnop\nmove.b d4,(a1)", "extra"),   # -> a 48c gap at 392..440
    ])
    res = pack(exact48, StepWork(steps=42, menu=MENU), n_lines=1)
    pad = next(r for r in res.report if r.kind == "pad" and "@pad 440" in r.detail)
    assert "+0c" in pad.detail, f"the 48c gap should need no nop filler: {pad.detail}"
    assert "move.w" in res.asm and "move.l" in res.asm   # a genuine mix


def test_step_solver_minimizes_nops():
    # both granularities even -> reachable in fine steps; solver keeps waste tiny
    res = pack(ALLBORDERS, StepWork(steps=42, menu=MENU), n_lines=2)
    assert res.nop_cycles <= 8                # 4c/line, vs the 44c/line a pure pour wastes


def test_step_infeasible_target_errors():
    # menu advances 4 or 2 steps -> only even totals reachable; 41 is odd
    try:
        pack(ALLBORDERS, StepWork(steps=41, menu=MENU), n_lines=1)
        assert False, "expected PackError"
    except PackError as e:
        assert "cannot cover exactly 41" in str(e)


def test_step_non_phase_stable_move_errors():
    bad = [Move("exg d0,d1", steps=1, cost=6)]      # 6c is not a multiple of 4
    try:
        pack(ALLBORDERS, StepWork(steps=2, menu=bad), n_lines=1)
        assert False, "expected PackError"
    except PackError as e:
        assert "phase-stable" in str(e)


# --- directive front-end: must compile down to the SAME objects as the Python API ---

SPEC = """\
;@template allborders 512
;@peg 0 left
    move.b d3,(a1)
    move.b d4,(a1)
;@peg 376 right
    move.b d4,(a0)
    move.b d3,(a0)
;@peg 444 extra
    move.b d3,(a1)
    nop
    move.b d4,(a1)
;@endtemplate

;@work repeat=39
    move.l 8(a6),(a6)+
    addq #4,a6
;@endwork

;@schedule allborders lines=3
"""


def test_directive_front_end_matches_python_api():
    from lockstep.directives import expand_schedule
    # Python API
    work = WorkStream.repeat(COLUMN, n=39, label="col")
    py = pack(ALLBORDERS, work, n_lines=3).asm
    # directive spec, with the header comment lines stripped
    spec_out = expand_schedule(SPEC)
    body = "\n".join(ln for ln in spec_out.splitlines()
                     if not ln.startswith("; ===")).strip("\n")
    assert body == py.strip("\n")
    assert block_cycles(spec_out) == (3 * 512, 3 * 512)


STEP_SPEC = """\
;@template allborders 512
;@peg 0 left
    move.b d3,(a1)
    move.b d4,(a1)
;@peg 376 right
    move.b d4,(a0)
    move.b d3,(a0)
;@peg 444 extra
    move.b d3,(a1)
    nop
    move.b d4,(a1)
;@endtemplate

;@stepwork steps=42
;@move 4
    move.l 8(a6),(a6)+
    addq #4,a6
;@move 2
    move.w 8(a6),(a6)+
    addq #4,a6
;@endstepwork

;@schedule allborders lines=3
"""


def test_step_directive_matches_python_api():
    from lockstep.directives import expand_schedule
    py = pack(ALLBORDERS, StepWork(steps=42, menu=MENU), n_lines=3).asm
    spec_out = expand_schedule(STEP_SPEC)
    body = "\n".join(ln for ln in spec_out.splitlines()
                     if not ln.startswith("; ===")).strip("\n")
    assert body == py.strip("\n")
    assert block_cycles(spec_out) == (3 * 512, 3 * 512)


def test_directive_errors_surface():
    from lockstep.directives import ScheduleError, expand_schedule
    try:
        expand_schedule(";@schedule nope lines=1\n")
        assert False, "expected ScheduleError"
    except ScheduleError as e:
        assert "unknown template" in str(e)


# --- beam-race placement: a write constrained to a cycle window (DESIGN §1.3.2, §7.1) ---

def test_beam_window_places_block_in_its_window():
    # a palette write that must execute in line cycles [40,120] is padded up to 40 and
    # runs within the window; the line still closes on 512c.
    pal = WorkBlock("move.w d5,$ffff8240\nmove.w d6,$ffff8242", beam=(40, 120))
    res = pack(ALLBORDERS, WorkStream([pal]), n_lines=1)
    assert block_cycles(res.asm) == (512, 512)
    assert ";@pad 40" in res.intermediate                 # padded up to the window start
    # the write executes inside the window: re-time from line start to just before the write
    head = res.asm.split("move.w d5,$ffff8240")[0]
    # everything emitted before the write in scanline 0 (drop directive comment lines)
    region = "\n".join(l for l in head.splitlines() if not l.lstrip().startswith(";"))
    start = block_cycles(region)[0]
    assert 40 <= start <= 120 - 8                          # starts in window, fits before hi


def test_beam_directive_matches_python_api():
    from lockstep.directives import expand_schedule
    pal = WorkBlock("move.w d5,$ffff8240", beam=(40, 120))
    py = pack(ALLBORDERS, WorkStream([pal]), n_lines=1).asm
    spec = (
        ";@template t 512\n"
        ";@peg 0 left\n    move.b d3,(a1)\n    move.b d4,(a1)\n"
        ";@peg 376 right\n    move.b d4,(a0)\n    move.b d3,(a0)\n"
        ";@peg 444 extra\n    move.b d3,(a1)\n    nop\n    move.b d4,(a1)\n"
        ";@endtemplate\n"
        ";@work beam=40:120\n    move.w d5,$ffff8240\n;@endwork\n"
        ";@schedule t lines=1\n"
    )
    out = expand_schedule(spec)
    body = "\n".join(l for l in out.splitlines() if not l.startswith("; ===")).strip("\n")
    assert body == py.strip("\n")


def test_beam_window_too_tight_errors():
    pal = WorkBlock("move.w d5,$ffff8240\nmove.w d6,$ffff8242", beam=(40, 50))  # 10c window
    try:
        pack(ALLBORDERS, WorkStream([pal]), n_lines=1)
        assert False, "expected PackError"
    except PackError as e:
        assert "beam window" in str(e) and "too small" in str(e)


def test_beam_deadline_completes_before_hi():
    # beam=(0, H) is a pure deadline: the write must finish by H. With borders, gap0 ends at
    # 376, so a deadline of 200 forces the write early.
    pal = WorkBlock("move.w d5,$ffff8240", beam=(0, 200))
    res = pack(ALLBORDERS, WorkStream([pal]), n_lines=1)
    assert block_cycles(res.asm) == (512, 512)
    head = res.asm.split("move.w d5,$ffff8240")[0]
    region = "\n".join(l for l in head.splitlines() if not l.lstrip().startswith(";"))
    assert block_cycles(region)[0] + 16 <= 200             # completes well before the deadline


def test_reserved_sound_peg_reserves_its_budget():
    # DESIGN §8: a peg with reserve=W occupies exactly W cycles; no work is poured into it.
    tmpl = LineTemplate([
        Peg(0,   "move.b d3,(a1)\nmove.b d4,(a1)", "left"),
        Peg(376, "move.b d4,(a0)\nmove.b d3,(a0)", "right"),
        Peg(400, "bsr play", "sound", reserve=64),
    ])
    res = pack(tmpl, WorkStream.repeat(COLUMN, n=2), n_lines=1)
    assert block_cycles(res.asm) == (512, 512)
    assert ";@pad 464" in res.intermediate                 # slot padded to offset+reserve
    # the reserved headroom carries no work — the columns land in the gap before the slot
    headroom = res.asm.split("bsr play")[1].split(";@fill")[0]
    assert "move.l 8(a6),(a6)+" not in headroom


def test_reserved_peg_overrunning_the_line_errors():
    tmpl = LineTemplate([Peg(0, "bsr play", "snd", reserve=600)], line_len=512)
    try:
        pack(tmpl, WorkStream([]), n_lines=1)
        assert False, "expected PackError"
    except PackError as e:
        assert "overrun" in str(e)


def test_aurora_capstone_frame_is_cycle_exact():
    # the capstone: Aurora's full display region (260 bands-worth of lines) re-created via
    # pack_schedule must total exactly 260 x 512c, every line on budget (static check; the
    # silicon proof is examples/aurora/frame.py + verify_segments).
    from examples.aurora.frame import aurora_frame
    res = aurora_frame()
    assert res.n_lines == 260
    assert block_cycles(res.asm) == (260 * 512, 260 * 512)


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed")


if __name__ == "__main__":
    _run()
