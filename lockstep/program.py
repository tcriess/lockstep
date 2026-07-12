"""Lockstep — wrap a scheduled VBL in a standalone, bootable full-sync demo (.TOS).

`emit_program` turns a per-frame body (a beam-sync + a Lockstep-generated VBL) into a complete
GEMDOS program, following the *proven* full-sync bootstrap that Aurora itself uses (read-only
reference, aurora.s:7-159): go supervisor, save the palette/resolution/sync/screen so it can
restore them, **disable all MFP interrupts** via both MFP interrupt-mask registers (Timer C's
200 Hz tick AND the keyboard/mouse ACIA — a level-6 interrupt that preempts the level-4 VBL and
walks the border switches off-cycle; a full-sync demo must own the machine so nothing preempts a
frame — leaving the ACIA on makes mouse movement close the borders on real hardware), set
up an aligned screen buffer, **install the frame as the $70 VBL handler** so it runs once per
vertical blank already synced to the top of the frame, and idle in the main program waiting for
a key. Exit un-installs the handler, re-enables Timer C, and restores everything.

Why VBL-driven and not a polled `move #$2700,sr` superloop: a full `sr` mask kills the VBL
*itself*, and with it the per-frame baseline the GLUE needs — the borders close (measured).
Aurora masks *inside* a VBL that keeps firing, and disables Timer C surgically. That keeps the
borders open AND removes the mid-frame intruder that scrambles the picture over a few frames.

This is the program skeleton — boot/install/exit boilerplate around the schedule. The *content*
is the author's: `setup` does ONE-TIME init (palette, screen fill, video base — `a3` = the live
aligned base); `frame` is one frame of full-sync code and must be **self-contained in registers**
(it runs in the VBL handler, where `setup`'s registers no longer survive), exactly as Aurora's
`my_70` re-loads its own registers each frame.
"""

from __future__ import annotations

import os
import subprocess
import tempfile

from st68k.hatari import VASM, HatariError

# A standalone full-sync demo, built on Aurora's proven bootstrap (aurora.s:7-159): disable
# Timer C via the MFP, install {frame} as the $70 VBL handler (so it runs once per vblank,
# synced to the frame top), and idle in the main program until a key. {setup} runs ONCE
# (a3 = aligned screen base = the live video base); {frame} is one VBL — self-contained in
# registers, because in the handler {setup}'s registers no longer survive.
_PROGRAM = """\
    text
__start:
    move.l  4(sp),__basepage    ; capture our basepage (only valid here, at entry) for Mshrink
    move.w  #2,-(sp)            ; Physbase
    trap    #14
    addq.l  #2,sp
    move.l  d0,__base
    clr.l   -(sp)               ; Super(0)
    move.w  #$20,-(sp)
    trap    #1
    addq.l  #6,sp
    move.l  d0,__ssp
    movem.l $ffff8240,d0-d7      ; save the 16-colour palette (8 longs)
    movem.l d0-d7,__pal
    move.b  $ffff8260,__res      ; save resolution
    move.b  $ffff820a,__sync     ; save sync mode
    move.b  $fffffa13,__imra     ; save MFP interrupt-mask register A
    move.b  $fffffa15,__imrb     ; save MFP interrupt-mask register B
    clr.b   $fffffa13            ; disable ALL MFP channel-A interrupts
    clr.b   $fffffa15            ; disable ALL MFP channel-B interrupts (Timer C 200 Hz AND the
                                 ;   keyboard/mouse ACIA on GPIP4 — a level-6 interrupt that would
                                 ;   otherwise preempt the level-4 VBL and walk the border switches.
                                 ;   A full-sync demo owns the machine; nothing may preempt a frame.)
    lea     __screen,a3          ; aligned screen base -> a3, and into the video base regs
    move.l  a3,d0
    add.l   #255,d0
    and.l   #$ffffff00,d0
    move.l  d0,a3
    move.l  d0,d1
    lsr.l   #8,d1
    move.b  d1,$ffff8203
    lsr.l   #8,d1
    move.b  d1,$ffff8201
    move.l  $70.w,__oldvbl       ; save the old VBL vector (early, so the out-of-memory path can __exit)
{pool}
{setup}
    move.l  #__vbl,$70.w         ; install our frame as the VBL handler (runs once per vblank)
{wait}
__exit:
    move.l  __oldvbl,$70.w       ; un-install our VBL handler
    move.b  __imra,$fffffa13     ; MFP interrupts back on
    move.b  __imrb,$fffffa15
    movem.l __pal,d0-d7          ; restore palette / resolution / sync
    movem.l d0-d7,$ffff8240
    move.b  __res,$ffff8260
    move.b  __sync,$ffff820a
    move.l  __base,d0            ; restore the video base
    move.l  d0,d1
    lsr.l   #8,d1
    move.b  d1,$ffff8203
    lsr.l   #8,d1
    move.b  d1,$ffff8201
    move.l  __ssp,-(sp)          ; back to user mode
    move.w  #$20,-(sp)
    trap    #1
    addq.l  #6,sp
    clr.w   -(sp)                ; Pterm0
    trap    #1
{nomem}
; --- the VBL handler: one full-sync frame, entered synced to the top of the display ---
__vbl:
    move.w  sr,-(sp)             ; we are an interrupt: save sr,
{mask}                           ;   optionally mask the rest of this (already-synced) frame,
    movem.l d0-d7/a0-a6,-(sp)    ;   and preserve the interrupted context's registers.
{frame}
    movem.l (sp)+,d0-d7/a0-a6
    move.w  (sp)+,sr
    rte

{extra}

    data
__base:     dc.l 0
__ssp:      dc.l 0
__oldvbl:   dc.l 0
__basepage: dc.l 0
__membase:  dc.l 0              ; GEMDOS-Malloc'd buffer pool base (0 if no pool requested)
__memoff:   dc.l 0              ; __membase - pool_origin: add to absolute buffer addresses
__pal:    dcb.l 8,0
__res:    dc.b 0
__sync:   dc.b 0
__imra:   dc.b 0
__imrb:   dc.b 0
    even

    bss
    even
__pstack:  ds.b 16384           ; private supervisor stack (so Mshrink can free the top-of-TPA stack)
__pstacktop:
__screen:  ds.b 65536           ; overscan screen buffer (+ alignment slack)
"""


# main program: wait for a key (GEMDOS Crawcin $07 — raw, no echo, blocks), then fall to exit.
# Matches Aurora's `jsr inp` (aurora.s:1403). The VBL does all the visible work meanwhile.
_WAIT_KEY = """\
__wait:
    move.w  #7,-(sp)             ; Crawcin: block until a key, no echo
    trap    #1
    addq.l  #2,sp"""

_WAIT_FOREVER = """\
__wait:
    bra.s   __wait               ; no key-exit: the VBL runs the demo forever"""


# Reserve the work-buffer pool from GEMDOS, so it lives in REAL free RAM *above* the program
# wherever it loaded — not at fixed absolute addresses that assume the program loaded low (an
# assumption that holds for an AUTO-folder/--auto launch but NOT a desktop launch, where the
# program loads higher and the pre-render would otherwise overwrite its own code). We first
# switch to a private stack inside our BSS (the original stack sits at the top of the TPA, which
# Mshrink is about to free), Mshrink the program to its real size, then Malloc the pool.
# `__memoff` = membase - origin is added to every absolute buffer address by the caller's code.
# membase is ROUNDED UP to a 256-byte boundary: the video base is set via the high+mid base bytes
# only (the low byte is forced 0 on the ST), so every frame/screen base MUST stay 256-aligned. The
# original buffer addresses are 256-aligned; with `pool_origin` 256-aligned too, an aligned membase
# keeps __memoff a multiple of 256 -> bases stay aligned. (GEMDOS Malloc only guarantees 2-byte
# alignment, so a raw membase would give a non-zero low byte: planes shift + the top overscan reads
# garbage, looking like a closed top border.) We Malloc 255 extra bytes to absorb the rounding.
# Out of memory (e.g. <4MB) -> a clear red screen + key, not a confusing black screen or bombs.
def _pool_asm(pool_bytes: int, pool_origin: int) -> str:
    # TEST hooks (verification only): POOL_MISALIGN=N simulates a Malloc that returns N bytes off a
    # 256-boundary; POOL_NOALIGN=1 drops the rounding (the old buggy behaviour). Default: aligned.
    misalign = int(os.environ.get("POOL_MISALIGN", "0"))
    noalign = os.environ.get("POOL_NOALIGN", "0") == "1"
    misalign_asm = f"    add.l   #{misalign},d0          ; TEST: simulate a misaligned Malloc result\n" if misalign else ""
    align_asm = ("" if noalign else
                 "    add.l   #255,d0              ; round membase UP to a 256-byte boundary (video base must be aligned)\n"
                 "    and.l   #$ffffff00,d0\n")
    return f"""\
    lea     __pstacktop,sp       ; --- reserve the work-buffer pool from GEMDOS ---
    move.l  __basepage,a5        ; keep = basepage($100) + text + data + bss
    move.l  $c(a5),d0
    add.l   $14(a5),d0
    add.l   $1c(a5),d0
    add.l   #$100,d0
    move.l  d0,-(sp)
    move.l  a5,-(sp)
    clr.w   -(sp)
    move.w  #$4a,-(sp)           ; Mshrink(0, basepage, keep) -> frees the rest of the TPA
    trap    #1
    lea     12(sp),sp
    move.l  #{pool_bytes + 255},-(sp)  ; Malloc(pool_bytes + 255 alignment slack)
    move.w  #$48,-(sp)
    trap    #1
    addq.l  #6,sp
    tst.l   d0
    beq     __nomem              ; 0 = not enough free RAM -> honest red screen
{misalign_asm}{align_asm}    move.l  d0,__membase
    sub.l   #{pool_origin},d0    ; __memoff = membase - origin (a multiple of 256, so bases stay aligned)
    move.l  d0,__memoff"""


_NOMEM = """\
__nomem:                         ; not enough RAM for the work-buffer pool: clear red screen + key
    lea     $ffff8240,a0
    moveq   #7,d1
.np:
    move.w  #$700,(a0)+
    dbra    d1,.np
    move.w  #7,-(sp)             ; Crawcin: wait for a key so the red screen is seen
    trap    #1
    addq.l  #2,sp
    bra     __exit"""


def emit_program(frame: str, *, setup: str = "", extra: str = "", exit_on_key: bool = True,
                 mask: bool = True, main: str = "", pool_bytes: int = 0, pool_origin: int = 0) -> str:
    """Return the assembly source of a standalone full-sync demo (.TOS), built on Aurora's
    bootstrap. `setup` runs ONCE in the main program (a3 = the live, aligned screen base);
    `frame` is one VBL, installed as the $70 handler. `frame` MUST be self-contained in
    registers — it runs in the interrupt handler where `setup`'s register values no longer
    live (the main program is blocked in the GEMDOS input call), exactly as Aurora's `my_70`
    re-loads its own registers each frame. `extra` is appended after the program (subroutines +
    data reached via jsr). With `exit_on_key` the main program blocks on a key (and then
    restores + exits); otherwise it idles forever.

    `mask` (default True) — emit `or.w #$0700,sr` at the top of the VBL handler, masking the
    rest of the (already vblank-synced) frame as Aurora does. Timer C is disabled at the MFP
    regardless, so the 200 Hz mid-frame intruder is gone either way; the in-handler mask just
    keeps the remaining interrupts out of the synced frame. This is NOT a top-level `move
    #$2700,sr`: that would mask the VBL itself and close the borders. Pass mask=False only to
    measure the handler-unmasked case.

    `main` — custom main-program body (runs ONCE after the $70 handler is installed, then should
    idle itself). Use it to do slow background work — e.g. drawing the screen incrementally — while
    the VBL handler keeps animating; the VBL preserves the main program's registers across its
    interrupts. Overrides exit_on_key. Label your own loops; `__wait`/`__exit` are reserved.

    `pool_bytes` — if >0, reserve that many bytes of work-buffer memory from GEMDOS (Mshrink +
    Malloc) before `setup` runs, and expose it as `__membase` (the pool base) and `__memoff`
    (= __membase - `pool_origin`). The intro must address its buffers RELATIVE to the pool: keep
    the absolute address immediates but add `__memoff` to each (and to frame addresses before
    writing the video base). This makes the buffers land in real free RAM above the program no
    matter where it loaded (desktop OR auto); out of memory shows a red screen instead of black."""
    if main:
        wait = main
    else:
        wait = _WAIT_KEY if exit_on_key else _WAIT_FOREVER
    mask_asm = "    or.w    #$0700,sr" if mask else ""
    pool = _indent(_pool_asm(pool_bytes, pool_origin)) if pool_bytes else ""
    nomem = _NOMEM if pool_bytes else ""
    return _PROGRAM.format(mask=mask_asm, pool=pool, nomem=nomem, setup=_indent(setup),
                           frame=_indent(frame), wait=_indent(wait), extra=extra)


def build_tos(src: str, out_path: str) -> str:
    """Assemble demo source to a `.TOS` at out_path (returns the path). Raises on vasm error."""
    work = tempfile.mkdtemp(prefix="lockstep_prog_")
    s_path = os.path.join(work, "demo.s")
    open(s_path, "w").write(src)
    r = subprocess.run([VASM, "-Ftos", "-no-opt", "-m68000", "-no-fpu", "-o", out_path, s_path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise HatariError(f"vasm failed:\n{r.stdout}\n{r.stderr}")
    return out_path


def _indent(asm: str) -> str:
    return "\n".join(("    " + ln if ln.strip() and not ln.startswith((" ", "\t"))
                      else ln) for ln in asm.splitlines())
