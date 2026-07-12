---
date: 2026-07-06
slug: reconstructing-and-build-your-own
categories:
  - Toolkit
  - Overscan
---

# Reconstructing a known-good demo, and building your own

This is the last post in the series. The previous five built up a tool: describe a scanline as pegs
and gaps, let it count the cycles, open the borders on every wakestate, keep the picture from tearing,
and put the frame's spare cycles on a budget. A reasonable question at that point is: why should I
believe any of it? This post is the answer, and then a short invitation.

<!-- more -->

## Trust, but reproduce

I didn't trust the tool until it could reproduce something I already trusted. Writing a new demo with
a new tool proves nothing — if it looks right, maybe the tool is correct, or maybe the demo is
forgiving. So the acceptance test was my previous demo: a full-overscan intro that already worked,
that I would *not* edit, and that I would try to rebuild through the tool from scratch.

The interesting comparison is the filler. Recall from [post 1](post-1-the-320x200-lie.md) that the old
way to pad a border line to 512 cycles was hand-counted `dcb.w` runs — 90 nops here, 13 there, 12 at
the end. In the original demo those counts were worked out by hand and sat in the source as magic
numbers. When the tool rebuilds the same line from nothing but the peg *positions*, it has to size
those same gaps itself. So that's the test, and it's a one-liner:

```python
res = allborders_screen(227)          # 227 lines, from the peg offsets alone

assert "dcb.w 90,$4e71" in res.asm, "left->right gap should be 90 nops (360c)"
assert "dcb.w 13,$4e71" in res.asm, "right->extra gap should be 13 nops (52c)"
assert "dcb.w 12,$4e71" in res.asm, "extra->end gap should be 12 nops (48c)"

lo, hi = block_cycles(res.asm)
assert lo == hi == 227 * 512          # and every line lands on exactly 512c
```

```
227 lines, 116224c total (== 227 x 512). Fillers: dcb.w 90 / 13 / 12
— identical to Aurora's hand-tuned debug loop.
```

Not "about the same." The same three numbers the demo shipped with, derived from the peg offsets
instead of counted by hand — and it does it for the whole frame: every band rebuilt through the
scheduler, every line measured at exactly 512 cycles in cycle-exact Hatari, the beam in the same place
on each line, the borders holding.

It's worth being clear about *why* that's convincing, because it's more than a nice coincidence. Those
hand-counted numbers are a known-good reference: a human worked them out carefully and the demo shipped
and ran on real hardware, so they are right. And they're a *demanding* reference, because a filler count
is only correct if every single instruction cost that fed into it was correct — mis-cost one instruction
by even a few cycles and the nop count for that line comes out different. So when the tool independently
arrives at the same numbers, line after line across a whole frame, it isn't matching one figure by luck;
it's showing that its cost model agrees with a careful human count on every instruction in the frame.
And then the emulator measures the assembled result against a cycle-exact model of the actual chips and
agrees as well.

Two independent yardsticks — a person's hand count and the silicon — landing on the same numbers. That
was the moment it stopped being a cycle-counting toy.

## The pipeline, on one page

Here's what building an overscan intro looks like now, start to finish. This is the whole thing:

```python
from lockstep import Move, StepWork
from lockstep.skeleton import OverscanFrame
from lockstep.budget import assert_within_budget
from lockstep.effects import assert_active_zone_clean
from lockstep.wakestate import verify_overscan

# 1. the frame. This one object owns everything from posts 2 and 4: the once-per-frame
#    beam lock, the left-border stabiliser, the cross-boundary bottom bust, the
#    interrupts-off bootstrap. You do not re-derive any of it.
frame = OverscanFrame()

# 2. your effect, poured into the display bands around the border switches
scroller = StepWork(steps=44, menu=[
    Move("move.l 8(a6),(a6)+\naddq #4,a6", steps=4, label="long"),
    Move("move.w 8(a6),(a6)+\naddq #4,a6", steps=2, label="word"),
])

# 3. the checks that run before the emulator is ever launched
assert_within_budget(frame, tail=my_tail)        # post 5: the frame's slack
assert_active_zone_clean(my_effect_asm)          # post 4: no absolute screen writes

# 4. out comes a bootable .TOS, bootstrap and all
frame.build("DEMO.TOS", setup=my_setup, upper=scroller, tail=my_tail)

# 5. and the oracle confirms it on the real assembled binary
report = verify_overscan("DEMO.TOS", wakestates=(1, 2, 3, 4), frames=range(320, 323))
print(report.matrix())
assert report.ok
```

The checks in step 3 — plus the per-line cycle count, which the packer enforces as it goes — all fail
the build *before* Hatari is ever launched. They're instant, they're free, and they catch the whole
class of mistakes that used to only show up as a wrong picture. Step 5 is the emulator confirming, on
the real assembled bytes, what the static checks predicted:

```
overscan matrix — wakestates × borders  (frames 320..322, 3 consecutive)
        left     right    top      bottom
  ws1   open     open     open     open
  ws2   open     open     open     open
  ws3   open     open     open     open
  ws4   open     open     open     open
  => ALL borders open on all wakestates, no flicker
```

Static checks tell you it *should* work; the oracle tells you it *does*.

And then you get to do the actual fun part, which is the demo:

![Aurora rebuilt by Lockstep: two sprites in the opened top border and a large bevelled scroller reading "GENERAT..." running through the opened bottom border, over a red-to-yellow colour gradient, the picture filling the entire overscan area](img/aurora.png)

That is a real headless capture of an assembled `.TOS` — and it is not a screenshot of the original
Aurora, it is a screenshot of Aurora *rebuilt by the toolkit*, with every hand-counted cycle number
deleted and re-derived. There is no black frame anywhere: the sprites sit in the opened top border
and the scroller runs through the opened bottom one. Compare that to the first picture in
[post 1](post-1-the-320x200-lie.md), which is what the machine gives you if you don't fight it.

The scroller is worth pointing at specifically, because it doubles as the proof. It lives *in the
bottom border*. If the bottom border were shut, the shifter would never fetch those scanlines, and
you would get the colour gradient with no letters in it — which is exactly what a four-cycle error in
the cycle model produced, and how I found one. That story is in
[the capstone](../../AURORA.md#the-four-cycles-that-hid-the-scroller).

## What's there, and what isn't

I want to be honest about the edges. The tool does the parts that were pure bookkeeping — cycle
counting, filler sizing, the border skeleton, the budget, the checks — and it does them well because
those parts are mechanical, and mechanical is what computers are good at. It does not write your demo.
The effect logic, the pointer arithmetic that threads a scroller through memory, the artistic decisions
about what bounces where — that's still yours. The tool sizes, places, verifies, and warns; it doesn't
invent.

There's also a list of things I'd still like it to do. Folding a full music player in as a first-class,
budgeted event rather than a hand-placed call. More ready-made effect recipes, so the common idioms —
the see-through scroller, the per-line palette split — aren't re-derived each time. A global step budget
that spans lines rather than sizing each one independently.

But the wall the first post described — the one that makes full-overscan feel like black magic — is
climbable now, and the ladder is checked into the repository rather than living in my head and a pile of
throwaway scripts.

That was the real goal, more than any single demo. The borders were always openable; people have been
opening them since these machines were new. What I wanted was to open them *without* spending a week
counting cycles by hand, testing on one wakestate, and hoping. Now the cycle-counting is the tool's job,
the border-opening is one object, and "did it work?" is a table, not a hope.

If you want to actually build one: the [tutorial](../../TUTORIAL.md) is the practical, code-level
version of posts 3 through 5, `docs/HOWTO_OVERSCAN.md` is the overscan recipe end to end, and
`examples/bordopen/` is the smallest thing that opens all four borders — about ninety lines, most of
them comments.

**Takeaway:** if your toolkit can reproduce a known-good demo to the cycle, you can trust it with a new
one. The border is a wall — but it turns out you can build a ladder, and then you can hand the ladder
to the next person. Thanks for reading.
