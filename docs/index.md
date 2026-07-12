---
title: Lockstep
description: Cycle-exact tooling for full-sync Atari ST code — pegs, gaps, a frame budget, and an emulator that tells you the borders opened.
---

# Lockstep

**Lockstep owns the cycle bookkeeping for full-sync Atari ST code.** You declare where the immovable
hardware events belong and what work you want run; it counts the cycles, sizes the `nop` filler, packs
your effect into the gaps, and then proves the result in a cycle-exact emulator.

:material-github: **The code is on GitHub: [tcriess/lockstep](https://github.com/tcriess/lockstep)** —
the toolkit, the examples, and the tests that back every claim on this site.

![Aurora, rebuilt by Lockstep: an Atari ST frame with all four borders open — sprites in the opened top border and a bevelled scroller running through the opened bottom one, the picture reaching every edge of the tube](blog/posts/img/aurora.png)

On an Atari ST, every scanline is exactly **512 CPU cycles**, and a border-opening write has to land on
an exact cycle within them — every line, every frame. Traditionally you get there by counting by hand
and padding with `dcb.w 90,$4e71`. Lockstep does the counting:

```asm
;@template allborders 512
;@peg 0 left                 ; left border: mono/lo-res flip
    move.b d3,(a1)
    move.b d4,(a1)
;@peg 376 right              ; right border: 60/50 Hz toggle
    move.b d4,(a0)
    move.b d3,(a0)
;@peg 444 extra
    move.b d3,(a1)
    nop
    move.b d4,(a1)
;@endtemplate

;@schedule allborders lines=227
```

You state the cycle each hardware event lands on — a fact about the video chip, which you have to know
anyway — and the filler counts fall out. No magic numbers to recompute when the effect changes.

## Start here

<div class="grid cards" markdown>

-   :material-book-open-variant: **[Racing the Beam](blog/index.md)**

    ---

    A six-post devlog: what the borders are, why the same binary opens them on half your STs, and how
    the toolkit came about. Start here if you want the *why*.

-   :material-console: **[Tutorial](TUTORIAL.md)**

    ---

    The practical, code-level guide: the cycle engine, the `;@` directives, the scheduler, and the
    Hatari oracle. Start here if you want to *use* it.

-   :material-television-classic: **[Opening the borders](HOWTO_OVERSCAN.md)**

    ---

    The overscan recipe end to end — all four borders, all four wakestates, on a plain STF.

</div>

## What it gives you

- **A cost model that is right, not rounded.** The 68000 shares one memory bus on a four-cycle beat,
  so an instruction's real cost depends on where in that beat it starts. Two `exg` instructions cost
  14 cycles, not the 16 that round-to-four predicts — and four cycles is a `nop`, which is the
  difference between a 512-cycle line and a broken picture.
- **A packer.** Declare pegs and work; get an unrolled routine where every scanline is exactly 512c.
- **A border skeleton.** One object that opens all four borders on all four wakestates, on a plain
  STF, in pure lock-once full-sync.
- **A frame budget.** The per-line check can't see the post-display tail; this one can, and fails the
  build before the emulator runs.
- **An oracle.** Every guarantee ends in a headless, cycle-exact Hatari run — "the borders opened" is
  a measurement, not a mood:

```
overscan matrix — wakestates × borders  (frames 320..322, 3 consecutive)
        left     right    top      bottom
  ws1   open     open     open     open
  ws2   open     open     open     open
  ws3   open     open     open     open
  ws4   open     open     open     open
  => ALL borders open on all wakestates, no flicker
```
