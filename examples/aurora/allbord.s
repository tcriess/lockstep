; Aurora's all-borders-open screen, re-created with Lockstep directives.
;
; This is the directive-front-end twin of examples/aurora/screen.py. It reproduces
; aurora.s:218-238 (the DEBUG border loop) EXACTLY: with the border switches pegged at
; Aurora's real offsets and no work between them, Lockstep sizes the gaps to dcb.w 90 / 13
; / 12 nops — the very numbers hand-counted in Aurora — so every line is 512c.
;
;   python -m lockstep schedule examples/aurora/allborders.src.s     # emit the asm
;   python -m lockstep verify   examples/aurora/allborders.src.s     # confirm 512c/line in Hatari
;
; (Aurora itself is never modified; this rebuilds its structure from Lockstep primitives.)

;@template allborders 512
;@peg 0 left                 ; left border: mono/lo-res flip   (aurora.s:220-221)
    move.b d3,(a1)
    move.b d4,(a1)
;@peg 376 right              ; right border: 60/50 Hz toggle   (aurora.s:225-227)
    move.b d4,(a0)
    move.b d3,(a0)
;@peg 444 extra              ; extra left flip                 (aurora.s:231-234)
    move.b d3,(a1)
    nop
    move.b d4,(a1)
;@endtemplate

;@schedule allborders lines=227
