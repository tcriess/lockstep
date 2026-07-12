# bordopen — full-sync border-opening test demo + wakestate plan

`examples/bordopen/bordopen.py` builds the minimal standalone full-sync demo: Aurora's VBL-handler
bootstrap + Lockstep's all-borders bands, on a flat **green** screen so an open border is visible
(green spilling into the overscan). No drawing, no sound — it isolates the VBL-entry beam-sync so we
can calibrate it. Once it's robust, a real demo is the same skeleton + its (already-correct) effects.

```
python examples/bordopen/bordopen.py   # builds bordopen.tos (Aurora, all-4 ws1/ws3)
                                       #    + bordws.tos (ROBUST: all 4 borders, all 4 WS)
```

## ★★★ STATUS (2026-06-19) — ALL 4 BORDERS open + STABLE on ALL 4 WAKESTATES — GOAL MET ★★★

`build_robust()` → `examples/bordws.tos` (== `bord4.tos`) opens **all four borders on
ws1/ws2/ws3/ws4, flicker-free**, in **pure lock-once full-sync** (no HBL, no `stop`). Confirmed in
**Hatari** (`--video-timing ws1..ws4`): tecer's interactive Hatari (all 4 borders, all WS, stable) +
headless consecutive-frame 0-px (ws1, ws2 confirmed; ws3/ws4 pending under contention). NB: tecer
tests in **Hatari, not a physical ST** ([[feedback-no-pkill-hatari]]) — say "Hatari-confirmed".
`bordopen.tos` (original Aurora) = all 4 on ws1/ws3 only.

**THE FIX = three counted-placement ingredients on the proven stable `bordopen.tos` lock:**
1. **`left_nops=1`** — widen the left hi-res blip 8c→12c (TEX "another 70Hz shock to work on all STs").
   The STABILISER covering ws2's left-border GLUE window; ws2 top+right → top+left+right.
2. **`cross=True` — the CROSS-BOUNDARY bottom bust (the breakthrough).** The bottom-border decision is
   made AT the scanline edge; a within-line 60/50 Hz pulse restores 50 Hz *before* the edge, which
   ws2/ws4's GLUE vertical phase misses. Instead **SET 60 Hz late on the bust line** (`set_off`~500, no
   restore) + **RESTORE 50 Hz early on the NEXT line** (`restore_off`~20) ⇒ 60 Hz **straddles** the
   edge ⇒ all wakestates catch it. Pure counted writes (`lockstep._cross_bust`).
3. **`main_lines=227`** — the bust line lands on the bottom-border scanline.

It stays **Mode-A lock-once full-sync**: the Aurora `$8209` beam-poll ONCE per frame, then 313 lines
counted at exactly 512c — verified `bord4.tos` source has no `stop`/`$68`. `bordopen.py` emits both.

**Diagnostic trail (full detail in [[project-fullsynctoolbox]]):**
- `wsprobe.py`: the `$8209` (MMU) lock lands at IDENTICAL CPU LineCycles (HBL34/LC138) on all 4 WS ⇒
  the fine-sync is already WS-invariant ⇒ widening it ('wide') is **ruled out**; the residual is a
  GLUE *sub-cycle phase*. `nudge.py`: a GLOBAL nudge trades left-FOR-right on ws2 ⇒ the lever is the
  per-switch *pulse* (the stabiliser / the cross-bust), not the sync.
- ⚠️ **DEAD END — `coarse='hbl'` (GLUE-lock via stop-on-HBL): FLICKERS.** It also opens all-4 L+R+T
  but tecer saw **period-2 flicker** (every other frame); `cwsprobe.py` = ~8c residual jitter at
  __lock (the bare `stop` has no fine-sync — DHS uses stop+$8209-fine; I did only the coarse half).
  The stabiliser + cross-bust fix everything on the STABLE lock, so the GLUE-lock is unnecessary —
  abandoned (kept as a diagnostic). **LESSON: a single-shot capture CANNOT see period-2 flicker —
  always sample CONSECUTIVE frames (`stabchk.py`/`cxall.py`); tecer's interactive eye caught it.**

### How the bottom was cracked — the cross-boundary insight (2026-06-19)
The counted *within-line* bust opens the bottom on ws1/ws3 only. I exhausted it: swept `main_lines`
(221-232), `bust_at` (464-496), and a 40c hold — **nothing** opens ws2/ws4, on either lock. The local
ST sources explained why: **TEX `BORDERS.S`** (canonical ST) uses our same fine-sync + stabiliser and
also does NOT solve the bottom on all WS; **TBL `ALLREMOV.S`** (STE) busts the bottom with a heavier
recipe (Timer-B on the exact scanline → `$ff8209` poll → ~60c hold → closed-loop retry). The cheaper
answer that worked: the bottom decision is at the **line edge**, so hold 60 Hz **across** it (the
cross-bust) — no poll, no Timer-B, no retry needed, and it stays pure full-sync.

<!-- superseded research note (kept for the record): -->
Our earlier bottom bust was a COUNTED peg holding 60 Hz only 8c. **Recommended-next (now SUPERSEDED by
the cross-bust):** on the bust LINE, re-pin to the MMU video offset with a `$ff8209` poll right
before the switch (TBL technique) and hold 60 Hz ~60c. Likely also needs the closed-loop retry, or
falls back to per-WS bottom or per-line re-sync (Option 3). Even Aurora only busts the bottom on WS 1&3.

### STATUS (2026-06-18 end of day) — superseded by the above for L+R+T

**Working: all four borders open, stable, mouse-proof — on ws1 and ws3.** Headless ws3 = full green
overscan 824×548 (97%); tecer confirmed ws1 + ws3 on real Hatari, and the mouse no longer disturbs it.
- **ws2**: only top+right open.   **ws4**: only top+left+right (no bottom).
That ws2/ws4 gap is the genuine **wakestate** frontier (Aurora's own source: the bottom bust "only
works in wakestate 1 & 3"). Tomorrow's work — see the PLAN below.

### The five fixes that got us here (each a real-HW issue the headless oracle first hid)

1. **Headless oracle fixed** (`lockstep/visual.py`): `shoot_tos` = `b VBL > N` + **`quit`**, ~7 s/shot.
   The old looping `capture()` wasn't frame-locked → stalled nVBLs → 180 s hangs. For bottom-OPEN
   frames (which stall nVBLs by removing the counted vblank) use `shoot_counter` (fires on the demo's
   post-bands RAM counter at `$1000`).
2. **Scramble** was a video-base hex bug: Python emitted `move.b #0x0a` (should be `#$0a`), so the base
   was `$0` → the demo displayed uninitialised RAM. Fixed (`{:02x}` with a literal `$`).
3. **Top flicker** (every-other-frame): my `SyncCfg` had a `baseline` re-assert (`move.b #2,$820a` /
   `clr.b $8260`) at handler entry that Aurora's `my_70` does NOT have. It shifts the pre-sync timing
   ~28c (nudging the eor-dance top-removal pulse off its line) and writes `$820a` early → top lands
   metastably. `baseline=False` ⇒ rock-steady top. (Beware: I first measured "stable" by sampling
   frames 50 apart — a multiple of the period-2 flicker → aliased to "4/4 identical". ALWAYS sample
   CONSECUTIVE frames to see flicker.)
4. **Bottom border**: a SHARP resonance at `main_lines=227`. With the top stably open, display DMA
   starts ~28 lines early so the `$8209` lock lands at scanline ~35; 227 lines then puts the bust on
   the ~262 bottom-border line (Aurora's exact 227/1/32). 219/223/231/235 all leave the bottom closed.
5. **Mouse closes top**: the IKBD/mouse **ACIA interrupt** (level 6, ABOVE the level-4 VBL) preempted
   the frame and walked the switches. Headless (dummy SDL) has no input so never saw it. `emit_program`
   now disables ALL MFP interrupts (`clr.b $fffffa13`=IMRA + `clr.b $fffffa15`=IMRB), not just Timer C
   — a full-sync demo must own the machine. You can't block level-6 via the SR mask without also
   blocking the VBL, so it must be done at the MFP.

### Beam geometry (probe in `.wsdbg/beam.py`)
Zero-byte labels `__lock`/`__band0` in the demo; read HBL/LineCycles on the running `.TOS` via PC
breakpoint. `.TOS` loads at a fixed EmuTOS TPA base: `text_base = runtime(__vbl=$10ce8) - sym(0x108)
= $10be0`, `addr = $10be0 + _parse_symbols(tos)[sym]`, `b pc=$addr :once :info default`. Found: the
`$8209` poll locks at display-DMA-start (HBL 63 with top closed, ~35 with top open) — **pause-
independent** (the counter only ticks during display), which is why sweeping `pause` never moved it.

### Files / knobs
`examples/bordopen/bordopen.py`: `SyncCfg(pause, first_line=85, fine='aurora'|'wide', baseline=False)` +
`build(main_lines=227, bot_lines=32, bust=True, bust_at=496, probe=False)`. `lockstep/visual.py`:
`shoot_tos` / `shoot_counter`. Scratch sweeps in `.wsdbg/`. Cycle-exact (260×512), 29 static tests green.

---

## PLAN — robust all-4-wakestate border opening (tomorrow, priority 2 → 3 → 4)

The wakestate = GLUE/MMU power-up phase = the relative phase between the 8 MHz CPU clock and the
video timing (Hatari `--video-timing ws1..ws4`, fixed at launch; on real HW fixed at power-on, so it
does NOT change mid-run). ws2/ws4 fail because our narrow per-frame lock (Aurora `moveq #16`/`lsl.w`,
~2c granularity over a small range) doesn't align the CPU to the video tightly enough on those
phases, so the left peg (ws2) and bottom bust (ws2/ws4) miss their GLUE-check cycles.

All approaches re-lock to the hardware via the two DHS `do_hardsync` ingredients (`…/DHS/Demo/Drone/
sys/common.s`): **coarse** `move.w #$2100,sr` / `stop #$2100` / `move.w #$2700,sr` (halt until the
next HBL = a jitter-free line edge; the STOP wakes with zero instruction-completion jitter, unlike a
polled wait), and **fine** the wide window `lea $ffff8209,a0 / moveq #127,d1 / .s tst.b (a0) / beq.s
.s / move.b (a0),d2 / sub.b d2,d1 / lsr.l d1,d1`. They differ in how OFTEN they re-lock.

### ▶ PRIORITY 1 = Option 2: robust per-FRAME lock (keep lock-once, stays full-sync)
Make the single per-frame lock wakestate-proof; the 512c-counted bands then stay aligned (beam is
512c/line). Restructure the VBL sync to:
1. `stop #$2100`-on-HBL FIRST — jitter-free frame entry (kills the VBL-dispatch jitter that the
   current `pause` rides on). Needs an **HBL handler at `$68`** (just `rte`) installed in setup, and
   `$68` saved/restored. NOTE the HBL is a GLUE level-2 autovector, NOT MFP, so it still fires with
   all MFP interrupts off — but verify EmuTOS isn't masking/usurping it; `stop #$2100` (mask=1) admits
   level-2.
2. counted delay to the top-overscan region, then the **eor-dance top-removal** (now jitter-free).
3. the **wide `$8209` fine-sync** (`#127`/`lsr.l`) for the band lock (replaces `#16`/`lsl.w`).
4. the existing 227/1/32 bands.
Calibrate the counted delays on ws3 (known-good), then test ws1/ws2/ws4. **Acceptance: all 4 borders
open AND consecutive frames identical (no flicker) on all 4 wakestates.**
RISK: the wakestate phase is sub-cycle; the wide fine-sync has 2c granularity. If ws2/ws4 still drift,
fall back to Option 4 (per-WS builds); Option 3 (per-line) is the optional last resort. (Quick
pre-test before any restructure: just swap `fine='aurora'`→`'wide'` and re-check ws2/ws4 — already a
`SyncCfg` knob, though it shifts the horizontal phase so `first_line` needs re-tuning.)

### ▶ PRIORITY 2 = Option 4: per-wakestate builds
If a single robust per-frame lock can't reach all 4, fall back to per-WS calibration. Keep the working
lock-once; find the ws2/ws4 offset corrections empirically (sweep the fine-sync constant / first_line /
peg offsets with the now-faithful oracle), emit up to 4 `.TOS` variants (Aurora's aurora0-4 approach).
Simplest mechanism, but N binaries and the user must pick. Note: `aurora0.tos` reportedly opens all 4
WS, yet all aurora builds share the SAME fine-sync (`#16`/`lsl.w`, no `stop`) — so its robustness is in
the constants/structure, not a different technique; reverse-engineering the binary isn't worth it vs.
just calibrating with the oracle. (Could also be auto-selected by a boot-time WS detect, but tecer
prefers not to rely on a once-at-boot table.)

### ▶ OPTIONAL variant = Option 3: per-LINE re-sync (DHS-style escape hatch)
`do_hardsync` EVERY scanline, then the switches. Robust on all 4 by construction, but NOT pure
full-sync (the `stop` burns uncounted cycles) — hence optional. The hard part: the canonical border
line is already exactly 512c, so the re-sync overhead must be ABSORBED, not added — the `stop` consumes
the line's slack, but the exception-dispatch + fine-sync (~60c) competes with the 12-nop tail. DHS
drives it off **Timer A** (`fulltc.s`: `fulltc_ta` arms TimerA data=52 ctrl=4 /50; `fulltc_ta_effect`
= `do_hardsync` + switches, re-points `$134`). Plan: install an HBL handler, run the per-line loop
either Timer-A-driven (faithful) or as a tight `do_hardsync`+switch loop where each iteration's `stop`
waits for the next HBL (simpler — but the per-line work must fit one line or it skips an HBL).
Calibrate the HBL-relative switch offsets with the beam probe + oracle. For Lockstep: a `sync="line"`
`LineTemplate` mode that emits this — a real new feature.

### Calibration logistics (all approaches)
The headless oracle is now FAITHFUL (ACIA fix removed the last real-HW divergence; ws3 matched tecer
exactly) — so I can calibrate headless. BUT `--cpu-exact` runs contend with tecer's live Hatari (the
4-WS sweep timed out fighting for CPU). Need an uncontended window, or hand tecer parameterized builds.
Per-WS measurement: `shoot_counter` (works whether or not the bottom is open). Stability: CONSECUTIVE
frames, never strided. Test matrix = approach × ws1/2/3/4 × {4 borders open, no flicker}.
