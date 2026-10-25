"""Lockstep — Dosound music for cycle-exact frames.

The source format is the XBIOS `Dosound` byte stream: what trackers and converters export, and
what an interrupt-driven demo plays with a VBL routine. Commands:

    $00..$0f, v          write v to YM register (the mixer, R7, keeps port bits 6/7 = output)
    $80, v               temp = v
    $81, r, inc, end     temp += inc, write temp to register r, once per frame, until temp == end
    $82..$ff, n          wait n + 1 frames (n = 0 ends the tune)

A frame-locked program cannot run a Dosound player: its cost depends on how many commands a frame
holds. So the stream is played at build time (`frames`) into the writes of every frame, and
`Song` packs the frames that write anything into records: (frames until the next record, number
of writes, register/value pairs). The replay (`Song.routine`) costs the same every frame: a
record frame runs its n writes and K - n dummy writes of identical cost, an idle frame K dummies,
where K is the largest record. Straight-line code with computed jumps, so it is called with a
`;@stall` carrying its exact cost (`Song.call`), which the budget machinery adds like any other
instruction.

Waits: n lasts n + 1 frames. That is how dosound-tracker (https://dosound.alyx.pl/) writes them:
one tracker step is 2 ticks of 20 ms, exported as `$ff,$01 ; DL 2`, and a wait of t ticks as
`$ff,t-1`. `delay_extra=0` reads n as n frames instead.
"""

from __future__ import annotations

import os
import re

from st68k.annotate import block_cycles


class DosoundError(Exception):
    pass


def parse(path: str) -> bytes:
    """A Dosound stream from a file: `dc.b` source (`.s`, `.asm`, `.txt`: $hex, %binary, decimal,
    `;` comments, labels ignored) or anything else as raw bytes."""
    if os.path.splitext(path)[1].lower() not in (".s", ".asm", ".txt", ".i"):
        return open(path, "rb").read()
    out = []
    for ln, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
        code = line.split(";", 1)[0].split("*", 1)[0] if not line.lstrip().startswith("*") else ""
        m = re.match(r"\s*(?:[\w.]+:)?\s*dc\.b\s+(.*)", code, re.I)
        if not m:
            continue
        for tok in m.group(1).split(","):
            t = tok.strip()
            if not t:
                continue
            try:
                v = (int(t[1:], 16) if t.startswith("$") else int(t[1:], 2) if t.startswith("%")
                     else int(t, 0))
            except ValueError:
                raise DosoundError(f"{path} line {ln}: {t!r} is not a byte value") from None
            out.append(v & 0xff)
    if not out:
        raise DosoundError(f"{path}: no dc.b data")
    return bytes(out)


def frames(data: bytes, *, delay_extra: int = 1, max_frames: int = 50 * 60 * 30) -> list:
    """Play the stream: the (register, value) writes of every frame, up to and including the
    frame of the end command."""
    out, i, temp, wait = [], 0, 0, 0
    while len(out) < max_frames:
        w = []
        if wait > 0:
            wait -= 1
            out.append(w)
            continue
        while True:
            if i >= len(data):
                raise DosoundError(f"the stream ends without an end command ($82..$ff, 0) "
                                   f"at byte {i}")
            c = data[i]
            if c < 0x80:
                if i + 1 >= len(data):
                    raise DosoundError(f"byte {i}: register write without a value")
                reg, val = c & 0x0f, data[i + 1]
                i += 2
                if reg == 7:
                    val = (val & 0x3f) | 0xc0
                w.append((reg, val))
            elif c == 0x80:
                temp = data[i + 1]
                i += 2
            elif c == 0x81:
                reg, inc, end = data[i + 1], data[i + 2], data[i + 3]
                temp = (temp + inc) & 0xff
                w.append((reg & 0x0f, temp))
                if temp == end:
                    i += 4
                break                                   # one sweep step per frame
            else:
                n = data[i + 1]
                i += 2
                if n == 0:
                    out.append(w)
                    return out
                wait = n - 1 + delay_extra
                break
        out.append(w)
    raise DosoundError(f"no end command within {max_frames} frames")


class Song:
    """A Dosound stream compiled for constant-cost replay. Labels use `prefix`.

    Embed: `data()` and `routine()` in the program (text section: the state is written),
    `init()` once before the first frame, `call()` once per frame in a budgeted region,
    `silence()` on exit. `cycles` is what `call()` costs."""

    def __init__(self, data: bytes, *, delay_extra: int = 1, loop: bool = True,
                 prefix: str = "__mus", k: int | None = None):
        fr = frames(data, delay_extra=delay_extra)
        self.n_frames = len(fr)
        self.prefix = prefix
        self.loop = loop
        events = [(f, w) for f, w in enumerate(fr) if w]
        if not events:
            raise DosoundError("the tune writes no register")
        if any(len(w) > 255 for _, w in events):
            raise DosoundError("a frame writes more than 255 registers")
        self.k = max(len(w) for _, w in events) if k is None else k
        if any(len(w) > self.k for _, w in events):
            raise DosoundError(f"k={self.k} is smaller than the busiest frame")
        # Each record carries the frames until the next record; the last one wraps to the first
        # (or, without loop, waits for ever: 255 frames at a time on a silent record).
        recs = []
        for j, (f, w) in enumerate(events):
            nxt = events[j + 1][0] if j + 1 < len(events) else (events[0][0] + self.n_frames)
            recs.append((nxt - f, w))
        self.first_wait = events[0][0] + 1
        self.records = []
        for gap, w in recs:                                  # waits over 255: silent filler records
            self.records.append([min(gap, 255), w])
            gap -= 255
            while gap > 0:
                self.records.append([min(gap, 255), []])
                gap -= 255
        if not loop:
            self.records[-1][0] = 255
            self.records.append([255, []])
        self._entry_real = (f"    move.b  (a0)+,$ffff8800\n"
                            f"    move.b  (a0)+,$ffff8802\n")
        self._entry_dummy = self._dummy_entry()
        self.cycles = self._cost()

    # ---- code ----
    def _dummy_entry(self) -> str:
        """Same cost as a real entry, touching no YM register: read the pair, write it to RAM."""
        p = self.prefix
        real = block_cycles(self._entry_real)[1]
        base = (f"    move.b  (a0),{p}_sink\n"
                f"    move.b  (a0),{p}_sink\n")
        gap = real - block_cycles(base)[1]
        if gap < 0 or gap % 4:
            raise DosoundError(f"cannot pad the dummy entry: real {real}c, dummy {real - gap}c")
        return base + "    nop\n" * (gap // 4)

    def _head(self) -> str:
        p = self.prefix
        return f"""\
    move.w  {p}_wait,d0
    subq.w  #1,d0               ; frames left until the next record
    move.w  d0,d2
    neg.w   d2
    subx.w  d2,d2               ; d2 = -1 while frames are left (no record this frame)
    ext.l   d2
    move.l  {p}_ptr,d3
    move.l  #{p}_null,d4
    eor.l   d3,d4
    and.l   d2,d4
    eor.l   d4,d3               ; read from the record, or from the null record (0 writes)
    move.l  d3,a0
    moveq   #0,d4
    move.b  (a0)+,d4            ; the record's wait
    moveq   #0,d1
    move.b  (a0)+,d1            ; and its number of writes
    move.w  d0,d5
    eor.w   d4,d5
    and.w   d2,d5
    eor.w   d4,d5               ; wait = record ? its wait : frames left
    move.w  d5,{p}_wait
    add.w   d1,d1
    add.w   d1,d1
    lea     {p}_rtab,a2
    move.l  (a2,d1.w),a2        ; real writes: enter n entries before the end
    lea     {p}_dtab,a3
    move.l  (a3,d1.w),a3        ; dummies: k - n entries before the end
    jmp     (a2)
"""

    def _tail(self) -> str:
        p = self.prefix
        return f"""\
    move.l  a0,d3               ; past the record (a null read is discarded below)
    move.l  {p}_ptr,d4
    eor.l   d3,d4
    and.l   d2,d4
    eor.l   d4,d3               ; ptr = record ? past it : unchanged
    move.l  d3,d4
    sub.l   #{p}_end,d4
    neg.l   d4
    subx.l  d4,d4               ; -1 unless the last record was just read
    not.l   d4                  ; -1 iff it was
    move.l  #{p}_recs,d5
    eor.l   d3,d5
    and.l   d4,d5
    eor.l   d5,d3               ; ... then start over
    move.l  d3,{p}_ptr
    rts
"""

    def routine(self) -> str:
        """The replay subroutine. Trashes d0-d5/a0/a2/a3."""
        p, k = self.prefix, self.k
        real = "".join(f"{p}_r{j}:\n" + self._entry_real for j in range(k))
        dummy = "".join(f"{p}_d{j}:\n" + self._entry_dummy for j in range(k))
        return (f"{p}_play:\n{self._head()}{real}{p}_r{k}:\n    jmp     (a3)\n"
                f"{dummy}{p}_d{k}:\n{self._tail()}")

    def _cost(self) -> int:
        """jsr + routine, every path (each path runs k entries)."""
        k = self.k
        path = (f"    jsr     {self.prefix}_play\n" + self._head() + self._entry_real * k
                + "    jmp     (a3)\n" + self._tail())
        c = block_cycles(path)[1]
        alt = (f"    jsr     {self.prefix}_play\n" + self._head() + "    jmp     (a3)\n"
               + self._entry_dummy * k + self._tail())
        if block_cycles(alt)[1] != c:
            raise DosoundError("real and dummy paths differ in cost")
        if c % 4:
            raise DosoundError(f"the replay costs {c}c, not a multiple of 4")
        return c

    def call(self) -> str:
        """One frame of music, for a budgeted region: the jsr is costed by the model, the routine
        by the ;@stall (its exact cost, every path)."""
        jsr = block_cycles(f"    jsr     {self.prefix}_play\n")[1]
        return f"    jsr     {self.prefix}_play\n    ;@stall {self.cycles - jsr}\n"

    def init(self) -> str:
        """Once, before the first frame: the first record, and a silent chip."""
        p = self.prefix
        return (f"    move.l  #{p}_recs,{p}_ptr\n"
                f"    move.w  #{self.first_wait},{p}_wait\n" + self.silence())

    @staticmethod
    def silence() -> str:
        """Volume 0 on all three channels (untimed: setup and exit)."""
        return "".join(f"    move.b  #{r},$ffff8800\n    move.b  #0,$ffff8802\n" for r in (8, 9, 10))

    def data(self) -> str:
        p, k = self.prefix, self.k
        lines = [f"* ---- music: {self.n_frames} frames ({self.n_frames / 50:.1f} s), "
                 f"{len(self.records)} records, k = {k} ----",
                 "    even", f"{p}_rtab:"]
        lines += [f"    dc.l    {p}_r{k - n}" for n in range(k + 1)]
        lines.append(f"{p}_dtab:")
        lines += [f"    dc.l    {p}_d{n}" for n in range(k + 1)]
        lines += [f"{p}_ptr:\n    dc.l    {p}_recs", f"{p}_wait:\n    dc.w    {self.first_wait}",
                  f"{p}_null:\n    dc.b    0,0", f"{p}_sink:\n    dc.b    0", "    even", f"{p}_recs:"]
        for wait, w in self.records:
            b = [wait, len(w)] + [x for rv in w for x in rv]
            lines.append("    dc.b    " + ",".join(f"${v:02x}" for v in b))
        lines += [f"{p}_end:", "    even"]
        return "\n".join(lines) + "\n"

    @property
    def data_bytes(self) -> int:
        return sum(2 + 2 * len(w) for _, w in self.records)
