---
title: Racing the Beam
description: A six-post devlog about opening all four Atari ST borders on every wakestate — and the toolkit that counts the cycles.
---

# Racing the Beam — a 6-post devlog

Building a full-overscan intro on a plain Atari ST, and the little toolkit that keeps the
cycle-counting out of my hands. Problem → toolkit → ship. Each post stands alone but they read best
in order.

![The same green screen with all four borders open — the picture running out to the edges of the tube](posts/img/borders-open.png)

## Read in order

1. **[The 320×200 lie: what full-overscan really costs](posts/post-1-the-320x200-lie.md)** — what the
   borders are, the 512-cycle scanline, and why there's no "close enough."
2. **[Same code, half your STs: wakestates and owning the machine](posts/post-2-same-code-half-your-sts.md)**
   — the wakestate lottery (and the STE escape hatch), plus the interrupt that closes your borders
   when someone moves the mouse.
3. **[Pegs, budgets, and an oracle: the toolkit](posts/post-3-pegs-budgets-and-an-oracle.md)** — describing
   a scanline as pegs and gaps, and letting the emulator tell you the borders opened.
4. **[Opening all four borders, on every wakestate](posts/post-4-all-four-borders-every-wakestate.md)** —
   lock once, straddle the boundary for the bottom border, and why *how* you write a pixel is part of
   the timing.
5. **[Sound, slack, and the rest of the frame](posts/post-5-sound-slack-and-the-rest-of-the-frame.md)** —
   inline replay, the YM2149 wait state that never added up, and costing the part of the frame that
   isn't a scanline.
6. **[Reconstructing a known-good demo, and building your own](posts/post-6-reconstructing-and-build-your-own.md)**
   — proving the tool by reproducing a demo to the cycle, and the whole pipeline on one page.

## Figures

Every screenshot in the series is a real headless [Hatari](https://hatari.tuxfamily.org/) capture of
an assembled `.TOS` — nothing is a mockup. Regenerate them all with:

```
python docs/blog/posts/img/make_images.py   # needs hatari + vasm + a TOS ROM; `make` first for the demos
```

The diagrams (`posts/img/*.svg`) are hand-drawn.

*The toolkit these posts describe is `lockstep/`; the practical, code-level version of posts 3–6 is
the [tutorial](../TUTORIAL.md) and [opening the borders](../HOWTO_OVERSCAN.md).*
