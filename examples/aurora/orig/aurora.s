; aurora demo.
; 4k Atari ST intro for SillyVenture 2024 WE
    text
mask_b  equ     $fffffa15
bot_lines       equ     32

; into supervisor
    clr.l -(sp)
    move.w #$20,-(sp)
    trap #1
    addq.l #6,sp
    move.l d0,-(sp) ; put the old stack pointer on top

    jsr prepare_font
    jsr prepare_scrolltext

    move.b  mask_b.w,-(sp) ; store the old mask register B to the top of the stack 
    bclr.b  #5,mask_b.w ; bit 5 in the interrupt mask register B = timer C on/off

; init screen
    jsr init_screen

; get the (new) screen address 2 (make sure it has the lower byte = 0)
    move.l #scrn2,d0
    add.l #255,d0
    clr.b d0
    move.l d0,d1
    lsr.l #8,d1
    move.w d1,hw_screen2
    move.w d1,hw_screen
    add.l #160,d0 ; skip 1. line
    move.l d0,screen2
    move.l d0,d1
    move.l d0,a5
    add.l #230*(28+200+bot_lines-64),d1
    addq.l #4,d1 ; planes 3+4 instead of 1+2
    move.l d1,scrollscraddr2 ; we start drawing in scrollscraddr2
    move.l d1,scrollscraddr

    movem.l pal_start,d0-d7
    movem.l d0-d7,$ffff8240.w

; get the (new) screen address (make sure it has the lower byte = 0)
    move.l #scrn,d0
    add.l #255,d0
    clr.b d0 ; clear the lower byte
    move.l d0,d1
    lsr.l #8,d1
    move.w d1,hw_screen1
    add.l #160,d0
    move.l d0,screen1 ; and store the result as the new screen address (this is actually "somewhere" beween "scrn" and "s")
    move.l d0,screen
    move.l d0,a6 ; also, store it in a6 to put some data in

; set the new (larger) screen address
    move.l d0,d1

    move.l d1,d0
    add.l #230*(28+200+bot_lines-64),d0 ; scroller is at address screenstart + 160 (first line) + 230 * 28 (upper border) + 230 * 228 (at the very end) - 230 * 64
    addq.l #4,d0 ; planes 3+4 instead of 1+2
    move.l d0,scrollscraddr1

    ; fill screen with logo
    lea 230*51(a6),a6
    lea logo_data,a5
    move.w #50-1,d0
.logoloop:
    rept 13
    move.l (a5)+,(a6)+
    move.l #0,(a6)+
    endr
    lea -13*4(a5),a5
    addq #2,a6
    rept 13
    move.l (a5)+,(a6)+
    move.l #0,(a6)+
    endr
    lea 20(a6),a6
    lea -13*4(a5),a5

    rept 13
    move.l (a5)+,(a6)+
    move.l #0,(a6)+
    endr
    lea -13*4(a5),a5
    addq #2,a6
    rept 13
    move.l (a5)+,(a6)+
    move.l #0,(a6)+
    endr
    lea 20(a6),a6

    dbra d0,.logoloop

    moveq #-1,d0
    ; new screen still in d1
    jsr set_scrn

    move.l screen1,a6
    move.l screen2,a5

    ; copy the contents of screen1 to screen2
    ; 160 + 230*27 + 230 * 200 + 230*bot_lines bytes
    move.w #(230*28+230*200+230*bot_lines)/4-1,d7
.cpyscr:
    move.l (a6)+,(a5)+
    dbra d7,.cpyscr
    lea raw_spr_cursor,a0
    lea spr_cursor,a1
    jsr prepare_sprite
    lea raw_spr_empty,a0
    lea spr_empty,a1
    jsr prepare_sprite
    lea raw_spr_butterfly_0,a0
    lea spr_butterfly_0,a1
    jsr prepare_sprite
    lea raw_spr_butterfly_1,a0
    lea spr_butterfly_1,a1
    jsr prepare_sprite
    lea raw_spr_qm1,a0
    lea spr_qm1,a1
    jsr prepare_sprite
    lea raw_spr_qm3,a0
    lea spr_qm3,a1
    jsr prepare_sprite

    jsr init_sprite


; set up vbl (will initialize timer b every time)
    move.l $70.w,-(sp) ; store old vbl on top of stack
    if DEBUG
    move.l #my_70_debug,$70.w ; install new vbl!
    else
    move.l #my_70,$70.w ; install new vbl!
    endif

; main program
    jsr inp ; wait for input

; restore vbl
    move.l (sp)+,$70.w

; restore screen
    jsr restore

; timer c on (order here is important, remember: old mask b currently on top of stack)
    ;ifeq keep_c
    move.b (sp)+,mask_b.w 
    ;endc

; out of supervisor, remmeber the old stack address is still on top of stack
    move.w #$20,-(sp)
    trap #1
    addq.l #6,sp

; terminate
    clr.l -(sp)
    trap #1

    if DEBUG
my_70_debug:
    move.w sr,-(sp) ; store status register on top of stack
    or.w #$0700,sr ; interrupts off

    movem.l d0-d7/a0-a6,-(sp) ; store all registers

; original pause code
; pause for a bit - 1065 loops
    move.w #1064,d0
pause:
    nop
    dbra d0,pause ; nicht gesprungen (1x) 14 cycles, gesprungen (1064x) 12 cycles

    eor.b #2,$ffff820a.w

    rept 8
    nop
    endr

; back to 50Hz
    eor.b #2,$ffff820a.w

; prepare registers
    move.w  #$8209,a0 ; screen counter (video address low byte)
    lea     $ff8260,a1      ; resolution
    moveq   #0,d0
    moveq   #16,d1
    moveq   #2,d3
    moveq   #0,d4

.wait:
    move.b  (a0),d0
    beq.s   .wait ; wait for video address low byte != 0

    if DEBUG
    eor.w   #$f0f,$ffff8240.w ; do sth with palette bg color (remove this in production!)
    else
    dcb.w 5,$4e71
    endif

    sub.w   d0,d1 ; d0 <> 0, d1 = 16 => d1 = 16 - d0
    lsl.w   d1,d0 ; probably some trick to sync with the correct number of cycles without hassle (i.e. "synchronize" the cpu)

    ; SYNC is done here!
    
    if DEBUG
    eor.w   #$f0f,$ffff8240.w ; reset palette bg color (remove this in production!)
    else
    dcb.w 5,$4e71
    endif

    move.w #$820a,a0

    dcb.w   85,$4e71 ; 340 cycles = total 368 cycles in the first line after sync

linesdeb   equ     227
    rept    linesdeb

    move.b  d3,(a1)         ; to monochrome
    move.b  d4,(a1)         ; to lo-res

    dcb.w   90,$4e71 ; 360c

; RIGHT AGAIN...
    move.b  d4,(a0)
    move.b  d3,(a0)

    dcb.w   13,$4e71

; EXTRA!
    move.b  d3,(a1)
    nop
    move.b  d4,(a1)

    dcb.w   12,$4e71

    endr

    movem.l (sp)+,d0-d7/a0-a6
    move.w  (a7)+,sr

    rte

    endif

; new vbl routine
my_70:
; interrupts off
    move.w sr,-(sp) ; store status register on top of stack
    or.w #$0700,sr ; interrupts off

    movem.l d0-d7/a0-a6,-(sp) ; store all registers

; original pause code
; pause for a bit - 1065 loops
;    move.w #1064,d0
;pause:
;    nop
;    dbra d0,pause ; nicht gesprungen (1x) 14 cycles, gesprungen (1064x) 12 cycles

; dbra seems to take 1x 14 cycles (counter expired) and 1064x 12 cycles (a little unclear why it is like that...)
; round-to-four means: 1x 16 cycles (counter exp) + 1064x 12 cycles (counter counting) + 1065x 4 cycles (nop) + 8 cycles (move) = 17052 cycles
; number of nops then 17052 / 4 = 4263

; it seems those 2 cycles are totally ok to go up or down (actually even a few more or less are ok at this stage)

; code in the spare cycles start

; first, toggle the screen addresses
    ; A - toggle the screen bit
    bchg.b #2,screen_toggle+1
    ; A: 24c (6 nops)
    ; B - set the current (draw, not shown) address to a0
    move.w screen_toggle,d0 ; d0.w is an indicator, in which screen we are (screen 1 or screen 2), it contains 0 or 4
    lea screens,a0
    movea.l 0(a0,d0.w),a0 ; 20 c? - screen address to use in a0
    ; B: 48c (12 nops)
    ; C - prepare the new hw screen address to set at the end of the interrupt routine
    lea hw_screens,a1
    move.w 2(a1,d0.w),d1
    move.w d1,hw_screen ; hw screen address to set at the end of the vbi routine, see below
    ; C: 44c (11 nops)
    ; D - set the screen table for line addresses on the current screen to a1
    ;lea screentables,a1
    ;movea.l 0(a0,d0.w),a1
    ; D: 32c (8 nops) - screen table in a1, screen address in a0

    ; E - sprite sequence
    lea current_sprite_sequence_struct,a3 ; currently executed sprite sequence position
    ; - 0w: counter
    ; - 2l: address of animated sprite definition
    ; - 6l: address of next entry in sequence
    lea current_ani_sprite_struct,a2 ; see below
    move.w (a3),d2 ; counter
    subq #1,d2
    bge.s .current_sprite_seq_cnt_ok
    ; things to do when the current sprite sequence counter is <0 (i.e. jump to the next entry in the sequence)
    ;INNER CODE 1
    move.l 6(a3),a4 ; a4: point to the next position in the sprite sequence
    move.w 10(a4),d3 ; 10(a4).w: offset to the next entry to avoid branching (can be negative or 0)
    move.w (a4),d2 ; new counter
    move.l 2(a4),a5 ; new animated sprite definition (delay, sprite address, next entry offset)
    move.l a5,d4
    tst.l d4
    ; check if it is != 0. if it is zero, keep the current animation and only update the position (screen + sprite offsets)
    beq.s .nonewani
    move.l a5,2(a3) ; update current_sprite_sequence_struct - address of animated sprite definition
    ; now we update the current_ani_sprite_stuct in a2
    move.w (a5),(a2) ; counter
    move.l 2(a5),2(a2) ; sprite data address
    add.w 6(a5),a5 ; next entry in ani
    move.l a5,10(a2)
    bra.s .newanicont
.nonewani:
    dcb.w 22,$4e71 ; 88c
    nop
    nop
.newanicont:
    move.w 6(a4),8(a2) ; screen offset
    move.w 8(a4),6(a2) ; sprite offset

    add.w d3,a4 ; next entry in the sprite sequence
    move.l a4,6(a3)
    ;/INNER CODE 1
    bra.s .current_sprite_seq_cont
.current_sprite_seq_cnt_ok:
    ; nops for INNER CODE 1
    dcb.w 58,$4e71 ; 232c

    ; following two nops to even out the cycles of the bge/bra construct
    nop
    nop
.current_sprite_seq_cont:
    move.w d2,(a3) ; write back the counter to current_sprite_sequence_struct
    ; E: 296c (74 nops)

    ; F - sprite handling part 1 - animated sprites (no sequence etc, just the animation)
    ; animated sprites are defined in a simple sequence which consists of
    ; - 0w: delay (or -1 for end-of-sequence)
    ; - 2l: pointer to the sprite data (base, will have to add the shift to that address)
    lea current_ani_sprite_struct,a2 ; currently displayed sprite
    ; this struct needs to contain:
    ; - 0w: counter which counts to (including) 0 (delay value)
    ; - 2l: pointer to the sprite data (base address)
    ; - 6w: offset to the correct shift (sprite_size_per_shift(384) bytes * shift (x % 16))
    ; - 8w: offset to the screen address (230 * y coordinate + x offset (x // 16 * 8))
    ; - 10l: pointer to the *next* position in the animated sprite definition (f.e. ani_spr_cursor)
    ; the struct is updated:
    ; - here, the counter is updated (-1) and
    ;   - if required, the animation data (+counter) is updated if the counter has run out
    ; - in the playbook code (below? above? we'll see)

    move.w (a2),d2 ; counter
    subq #1,d2
    bge.s .current_ani_spr_cnt_ok
    ; things to do when the current sprite counter is <0 (i.e. jump to the next sprite content in the animated sprite)
    ;INNER CODE 1
    move.l 10(a2),a3 ; point to the next position in the animated sprite definition
    move.w 6(a3),d3 ; to avoid branching, this is the offset to the next entry (can be negative)
    move.w (a3),d2 ; counter
    move.l 2(a3),2(a2) ; sprite data address
    add.w d3,a3
    move.l a3,10(a2) ; point to the next position
    ;/INNER CODE 1
    bra.s .current_spr_cont
.current_ani_spr_cnt_ok: ; counter is still >= 0, do nothing
   ; nops for INNER CODE 1
    dcb.w 22,$4e71 ; 132c

    ; following two nops to even out the cycles of the bge/bra construct
    nop
    nop
    ; 28c placeholder for now
.current_spr_cont:
    move.w d2,(a2) ; write back the counter to current_ani_sprite_struct
    ; F: 140c (35 nops)

    ; G - draw sprite
    ; a0 - screen address, a1 - screen table, a2 is still pointing to current_ani_sprite_struct
    move.l d0,-(sp) ; save d0 as it is destroyed
    lea spr_bgs,a5 ; the sprite backgrounds (1 or 2)
    move.l (a5,d0.w),a5 ; sprite background - address of correct sprite background struct in a5
    move.l (a5),a6 ; address on screen to put the old background back on in a6
    move.l a0,a4 ; screen address
    adda.w 8(a2),a4 ; correct address to put the sprite
    move.l a4,(a5)+ ; save for later in the bg struct
    move.l 2(a2),a3 ; sprite data
    add.w 6(a2),a3 ; add offset to the correct shift -> address of final sprite data in a3
    
    rept 16
    ; restore old bg
    movem.l (a5)+,d0-d3 ; 44c
    movem.l d0-d3,(a6) ; 40c
    
    lea 230(a6),a6 ; 8c
    endr
    lea -230*16(a6),a6
    lea -16*16(a5),a5

    rept 16
    ; restore old bg
    ;movem.l (a5),d0-d3 ; 44c
    ;movem.l d0-d3,(a6) ; 40c
    ; save bg
    movem.l (a4),d0-d3 ; 44c store the new background
    move.l d0,(a5)+ ; 12c
    move.l d1,(a5)+ ; 12c
    move.l d2,(a5)+ ; 12c
    move.l d3,(a5)+ ; 12c this seems faster than the "movem + add" version

    move.l (a3)+,d4 ; 12c mask left
    ;nop
    ;nop
    ;nop
    move.l (a3)+,d5 ; 12c mask right
    ;nop
    ;nop
    ;nop

    and.l d4,d0 ; 8c
    and.l d4,d1 ; 8c
    and.l d5,d2 ; 8c
    and.l d5,d3 ; 8c

    movem.l (a3)+,d4-d7 ; 44c
    ; dcb.w 11,$4e71
    or.l d4,d0 ; 8c
    or.l d5,d1 ; 8c
    or.l d6,d2 ; 8c
    or.l d7,d3 ; 8c
    movem.l d0-d3,(a4) ; 40c
    lea 230(a4),a4 ; 8c
    lea 230(a6),a6 ; 8c
    endr

    move.l (sp)+,d0 ; restore d0
    ; G: 5956c (1489 nops) + 144c ( + 36 nops)

    ; second sprite - E2, F2, G2
    ; E2 - sprite sequence
    lea current_sprite_sequence_struct2,a3 ; currently executed sprite sequence position
    ; - 0w: counter
    ; - 2l: address of animated sprite definition
    ; - 6l: address of next entry in sequence
    lea current_ani_sprite_struct2,a2 ; see below
    move.w (a3),d2 ; counter
    subq #1,d2
    bge.s .current_sprite_seq_cnt_ok2
    ; things to do when the current sprite sequence counter is <0 (i.e. jump to the next entry in the sequence)
    ;INNER CODE 1
    move.l 6(a3),a4 ; a4: point to the next position in the sprite sequence
    move.w 10(a4),d3 ; 10(a4).w: offset to the next entry to avoid branching (can be negative or 0)
    move.w (a4),d2 ; new counter
    move.l 2(a4),a5 ; new animated sprite definition (delay, sprite address, next entry offset)
    move.l a5,d4
    tst.l d4
    ; check if it is != 0. if it is zero, keep the current animation and only update the position (screen + sprite offsets)
    beq.s .nonewani2
    move.l a5,2(a3) ; update current_sprite_sequence_struct2 - address of animated sprite definition
    ; now we update the current_ani_sprite_stuct2 in a2
    move.w (a5),(a2) ; counter
    move.l 2(a5),2(a2) ; sprite data address
    add.w 6(a5),a5 ; next entry in ani
    move.l a5,10(a2)
    bra.s .newanicont2
.nonewani2:
    dcb.w 22,$4e71 ; 88c
    nop
    nop
.newanicont2:
    move.w 6(a4),8(a2) ; screen offset
    move.w 8(a4),6(a2) ; sprite offset

    add.w d3,a4 ; next entry in the sprite sequence
    move.l a4,6(a3)
    ;/INNER CODE 1
    bra.s .current_sprite_seq_cont2
.current_sprite_seq_cnt_ok2:
    ; nops for INNER CODE 1
    dcb.w 58,$4e71 ; 232c

    ; following two nops to even out the cycles of the bge/bra construct
    nop
    nop
.current_sprite_seq_cont2:
    move.w d2,(a3) ; write back the counter to current_sprite_sequence_struct
    ; E2: 296c (74 nops)

    ; F2 - sprite handling part 1 - animated sprites (no sequence etc, just the animation)
    ; animated sprites are defined in a simple sequence which consists of
    ; - 0w: delay (or -1 for end-of-sequence)
    ; - 2l: pointer to the sprite data (base, will have to add the shift to that address)
    lea current_ani_sprite_struct2,a2 ; currently displayed sprite
    ; this struct needs to contain:
    ; - 0w: counter which counts to (including) 0 (delay value)
    ; - 2l: pointer to the sprite data (base address)
    ; - 6w: offset to the correct shift (sprite_size_per_shift(384) bytes * shift (x % 16))
    ; - 8w: offset to the screen address (230 * y coordinate + x offset (x // 16 * 8))
    ; - 10l: pointer to the *next* position in the animated sprite definition (f.e. ani_spr_cursor)
    ; the struct is updated:
    ; - here, the counter is updated (-1) and
    ;   - if required, the animation data (+counter) is updated if the counter has run out
    ; - in the playbook code (below? above? we'll see)

    move.w (a2),d2 ; counter
    subq #1,d2
    bge.s .current_ani_spr_cnt_ok2
    ; things to do when the current sprite counter is <0 (i.e. jump to the next sprite content in the animated sprite)
    ;INNER CODE 1
    move.l 10(a2),a3 ; point to the next position in the animated sprite definition
    move.w 6(a3),d3 ; to avoid branching, this is the offset to the next entry (can be negative)
    move.w (a3),d2 ; counter
    move.l 2(a3),2(a2) ; sprite data address
    add.w d3,a3
    move.l a3,10(a2) ; point to the next position
    ;/INNER CODE 1
    bra.s .current_spr_cont2
.current_ani_spr_cnt_ok2: ; counter is still >= 0, do nothing
   ; nops for INNER CODE 1
    dcb.w 22,$4e71 ; 132c

    ; following two nops to even out the cycles of the bge/bra construct
    nop
    nop
    ; 28c placeholder for now
.current_spr_cont2:
    move.w d2,(a2) ; write back the counter to current_ani_sprite_struct
    ; F2: 140c (35 nops)

    ; G2 - draw sprite 2
    ; a0 - screen address, a1 - screen table, a2 is still pointing to current_ani_sprite_struct
    move.l d0,-(sp) ; save d0 as it is destroyed
    lea spr_bgs2,a5 ; the sprite backgrounds (1 or 2)
    move.l (a5,d0.w),a5 ; sprite background - address of correct sprite background struct in a5
    move.l (a5),a6 ; address on screen to put the old background back on in a6
    move.l a0,a4 ; screen address
    add.w 8(a2),a4 ; correct address to put the sprite
    move.l a4,(a5)+ ; save for later in the bg struct
    move.l 2(a2),a3 ; sprite data
    add.w 6(a2),a3 ; add offset to the correct shift -> address of final sprite data in a3
    
    ; +16*(8) + 8 +8 = 144c = 36 nops

    rept 16
    ; restore old bg
    movem.l (a5)+,d0-d3 ; 44c
    movem.l d0-d3,(a6) ; 40c
    
    lea 230(a6),a6 ; 8c
    endr
    lea -230*16(a6),a6
    lea -16*16(a5),a5

    rept 16
    ; save bg
    movem.l (a4),d0-d3 ; 44c store the new background
    move.l d0,(a5)+ ; 12c
    move.l d1,(a5)+ ; 12c
    move.l d2,(a5)+ ; 12c
    move.l d3,(a5)+ ; 12c this seems faster than the "movem + add" version

    move.l (a3)+,d4 ; 12c mask left
    ;nop
    ;nop
    ;nop
    move.l (a3)+,d5 ; 12c mask right
    ;nop
    ;nop
    ;nop

    and.l d4,d0 ; 8c
    and.l d4,d1 ; 8c
    and.l d5,d2 ; 8c
    and.l d5,d3 ; 8c

    movem.l (a3)+,d4-d7 ; 44c
    ; dcb.w 11,$4e71
    or.l d4,d0 ; 8c
    or.l d5,d1 ; 8c
    or.l d6,d2 ; 8c
    or.l d7,d3 ; 8c
    movem.l d0-d3,(a4) ; 40c
    lea 230(a4),a4 ; 8c
    lea 230(a6),a6 ; 8c
    endr

    move.l (sp)+,d0 ; restore d0
    ; G2: 5956c (1489 nops) + 144c (+36nops)

    ; H - palette sequence
    lea current_pal_sequence_struct,a3 ; currently executed palette sequence position
    ; - 0w: counter
    ; - 2l: address of palette
    ; - 6l: address of next entry in sequence
    ; sequence entry:
    ; - 0w: delay
    ; - 2l: address of palette
    ; - 6w: offset to next entry
    
    move.w (a3),d2 ; counter
    move.l 2(a3),a5 ; current palette
    subq #1,d2
    bge.s .current_pal_seq_cnt_ok
    ; things to do when the current pal sequence counter is <0 (i.e. jump to the next entry in the sequence)
    ;INNER CODE 1
    move.l 6(a3),a4 ; a4: point to the next position in the palette sequence
    move.w 6(a4),d3 ; 6(a4).w: offset to the next entry to avoid branching (can be negative or 0)
    move.w (a4),d2 ; new counter
    ;movem.l (a5),d4-d7/a0-a2/a6
    ;movem.l d4-d7/a0-a2/a6,$ffff8240.w
    move.l 2(a4),2(a3) ; next current palette
    add.w d3,a4 ; next entry in the sequence
    move.l a4,6(a3)
    ;/INNER CODE 1
    bra.s .current_pal_seq_cont
.current_pal_seq_cnt_ok:
    ; nops for INNER CODE 1
    ; dcb.w 64,$4e71 ; 256c-76-76-16
    dcb.w 22,$4e71 ; 88c

    ; following two nops to even out the cycles of the bge/bra construct
    nop
    nop
.current_pal_seq_cont:
    move.w d2,(a3) ; write back the counter to current_pal_sequence_struct
    movem.l (a5),d4-d7/a0-a2/a6
    movem.l d4-d7/a0-a2/a6,$ffff8240.w
    ; H: 308c (77 nops)

    ; I - sound sequence
    lea current_snd_sequence_struct,a3 ; currently executed sound sequence position
    ; - 0w: counter
    ; - 2l: address of snd
    ; - 6l: address of next entry in sequence
    ; sequence entry:
    ; - 0w: delay
    ; - 2l: address of snd
    ; - 6w: offset to next entry

    lea current_dosound_sequence_struct,a2
    ; - 0w: counter
    ; - 2l: address of the current entry in the dosound sequence
    ; - 6b: current value of the temporary var
    ; - 7b: filler (0)
    ; ; - 8l: next entry in the dosound sequence - not required
    
    move.w (a3),d2 ; counter
    move.l 2(a3),a5 ; current snd addr
    subq #1,d2
    bge.s .current_snd_seq_cnt_ok
    ; things to do when the current snd sequence counter is <0 (i.e. jump to the next entry in the sequence)
    ;INNER CODE 1
    move.l 6(a3),a4 ; a4: point to the next position in the sound sequence
    move.w 6(a4),d3 ; 6(a4).w: offset to the next entry to avoid branching (can be negative or 0)
    move.w (a4),d2 ; new counter
    ;move.l a5,play_sound
    move.l a5,2(a2)
    move.w #0,0(a2) ; this counter works differently
    move.b #0,7(a2) ; clear temp var

    move.l 2(a4),2(a3) ; next current snd
    add.w d3,a4 ; next entry in the sequence
    move.l a4,6(a3)
    ;/INNER CODE 1
    bra.s .current_snd_seq_cont
.current_snd_seq_cnt_ok:
    ; nops for INNER CODE 1
    dcb.w 34,$4e71 ; 108c - 20c + 16c + 16c + 16c

    ; following two nops to even out the cycles of the bge/bra construct
    nop
    nop
.current_snd_seq_cont:
    move.w d2,(a3) ; write back the counter to current_snd_sequence_struct
    ; I: 216c (54 nops)

    ; J - scrollerpal sequence
    lea current_scrollerpal_sequence_struct,a3 ; currently executed scroller palette sequence position
    ; - 0w: counter
    ; - 2l: address of palette table
    ; - 6l: address of next entry in sequence
    ; sequence entry:
    ; - 0w: delay
    ; - 2l: address of palette table
    ; - 6w: offset to next entry
    
    move.w (a3),d2 ; counter
    ;move.l 2(a3),a5 ; current palette table addr
    subq #1,d2
    bge.s .current_scrpal_seq_cnt_ok
    ; things to do when the current scrollerpal sequence counter is <0 (i.e. jump to the next entry in the sequence)
    ;INNER CODE 1
    move.l 6(a3),a4 ; a4: point to the next position in the scrollerpal sequence
    move.w 6(a4),d3 ; 6(a4).w: offset to the next entry to avoid branching (can be negative or 0)
    move.w (a4),d2 ; new counter

    ;lea scrollerpals,a5
    nop
    move.l 2(a4),d5
    add.l d5,2(a3)
    ;add.w 2(a4),a5
    ;move.l a5,2(a3)
    ;add.l #4,2(a3)
    ;move.l 2(a4),2(a3) ; next current scrollerpal table
    add.w d3,a4 ; next entry in the sequence
    move.l a4,6(a3)
    ;/INNER CODE 1
    bra.s .current_scrpal_seq_cont
.current_scrpal_seq_cnt_ok:
    ; nops for INNER CODE 1
    dcb.w 26,$4e71 ; 88c

    ; following two nops to even out the cycles of the bge/bra construct
    nop
    nop
.current_scrpal_seq_cont:
    move.w d2,(a3) ; write back the counter to current_scrollerpal_sequence_struct
    ; J: 156c (39 nops)
    

; *** all preparation code before the first visible line done ***, still a few cycles to burn here (but that needs to be calculated carefully!)

    ; actually, it seems more stable with a total of 4267 nops
    ; dcb.w 4192,$4e71 ; A-E
    ;dcb.w 2704,$4e71 ; A-G without E
    ;dcb.w 2630,$4e71 ; A-G
    ;dcb.w 2553,$4e71 ; A-H
    ;dcb.w 2499,$4e71 ; A-I, without E2-G2
    ;dcb.w 901,$4e71 ; A-I, with E2-G2
    ;dcb.w 862,$4e71 ; A-J, with E2-G2
    ;dcb.w 870,$4e71 ; A-J, with E2-G2, without D
    dcb.w 798,$4e71 ; A-J, with E2-G2, without D

; to 60Hz
    eor.b #2,$ffff820a.w

    rept 8
    nop
    endr

; back to 50Hz
    eor.b #2,$ffff820a.w

; prepare registers
    move.w  #$8209,a0 ; screen counter (video address low byte)
    lea     $ff8260,a1      ; resolution
    moveq   #0,d0
    moveq   #16,d1
    moveq   #2,d3
    moveq   #0,d4

.wait:
    move.b  (a0),d0
    beq.s   .wait ; wait for video address low byte != 0

    if DEBUG
    eor.w   #$f0f,$ffff8240.w ; do sth with palette bg color (remove this in production!)
    else
    dcb.w 5,$4e71
    endif

    sub.w   d0,d1 ; d0 <> 0, d1 = 16 => d1 = 16 - d0
    lsl.w   d1,d0 ; probably some trick to sync with the correct number of cycles without hassle (i.e. "synchronize" the cpu)

    ; SYNC is done here!
    
    if DEBUG
    eor.w   #$f0f,$ffff8240.w ; reset palette bg color (remove this in production!)
    else
    dcb.w 5,$4e71
    endif

    move.w #$820a,a0
    ; up to this point, after the wait: 58 cycles


    movea.l scrollscraddr,a6 ; 20 c / 5 nops
    move.l font_addr1,a3
    move.l font_addr2,a4
    move.w fontoffset1,d4
    move.w fontoffset2,d5
    add.w d4,a3
    add.w d5,a4

    movea.l scrollscraddr,a6 ; put the start address of the first line of the scroller in a6
    move.l a6,a5
    lea 216(a5),a5 ; end of the line, this is where we put the new char data

    ; a6: scroller start, used to do the byte shifting
    ; a5: start of the rightmost word to feed in new data
    ; a4: new data (for now: first character in font)

    dcb.w   50,$4e71 ; total 368 cycles in the first line after sync
    ;dcb.w   85,$4e71 ; 340 cycles = total 368 cycles in the first line after sync

    ;nop
; every line of the scroller needs *2* lines of byte shifting, unfortunately
; so we start the shifting here and go on for the next 128 lines to have a 64 lines-scroller
; the following rept contains 2 lines
    rept 64
    
* LEFT HAND BORDER!
    move.b  d3,(a1)         ; to monochrome
    ;nop
    move.b  d4,(a1)         ; to lo-res

    nop
    nop
    
    move.l 8(a6),(a6)+ ; 1.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 2.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 3.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 4.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 5.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 6.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 7.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 8.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 9.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 10.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 11.
    addq #4,a6
    ; 356 cycles (88 of 224 bytes are handled (for 1 line))

* RIGHT AGAIN...
    move.b  d4,(a0)
    move.b  d3,(a0)

    ;dcb.w   13,$4e71 ; 52 cycles
    move.l 8(a6),(a6)+ ; 12.
    addq #4,a6
    move.w 8(a6),(a6)+ ; 12.5
    nop

* EXTRA!
    move.b  d3,(a1)
    nop
    move.b  d4,(a1)

    ;nop

    ; dcb.w   12,$4e71 ; 48 cycles
    move.w 8(a6),(a6)+ ; 13.
    addq #4,a6
    move.l 8(a6),(a6)+ ; 14./28, 14 to go
    ; need to adjust a6 addq #4,a6

; second line
    ;nop
* LEFT HAND BORDER!
    move.b  d3,(a1)         ; to monochrome
    ;nop
    move.b  d4,(a1)         ; to lo-res

    addq #4,a6 ; adjustment which was missing from above

    move.l 8(a6),(a6)+ ; 15.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 16.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 17.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 18.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 19.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 20.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 21.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 22.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 23.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 24.
    addq #4,a6

    move.l 8(a6),(a6)+ ; 25.
    nop
    nop

* RIGHT AGAIN...
    move.b  d4,(a0)
    move.b  d3,(a0)

    ; dcb.w   13,$4e71 ; 52 cycles
    addq #4,a6
    move.l 8(a6),(a6)+ ; 26.
    addq #4,a6
    nop
    nop
    nop

* EXTRA!
    move.b  d3,(a1)
    nop
    move.b  d4,(a1)

    ;dcb.w   12,$4e71 ; 48 cycles
    move.l 8(a6),(a6)+ ; 27.
    ;addq #4,a6
    ; 28. column is not there yet..., so we add 4, then 8 (to skip the last column completely)
    ;  and then 6 for the extra 6 bytes per line
    ; (the last column will then be filled by the code in the following lines, feeding character data from the right)
    lea 18(a6),a6
    ;move.l (a4)+,(a6)+ ; new data in a4...
    nop
    nop
    nop
    nop
    ;nop

    endr

    ; until the bottom border we have 227 lines to process, 128 are done, so there are 99 lines left

; feed in new font data from the right at the scroller position

; for the 8-bit-shift, try to replace this:
;    move.l (a4)+,(a5) ; 24 cycles
; with something like this:
;    move.l (a3)+,d0 ; 12 cycles a3 points to the (left-)shifted previous character
;    or.l (a4)+,d0   ; 16(14) cycles a4 points to the (right-)shifted new character
;    move.l d0,(a5) ; 12/16 cycles, total of 40/44 cycles (instead of 20/24)
; if a3=a4 as before, the result should be the same!

; 129.-136. line: feed in 8 lines at a time
    rept 8
    ; nop

* LEFT HAND BORDER!
    move.b  d3,(a1)         ; to monochrome 8 cycles
    move.b  d4,(a1)         ; to lo-res     8 cycles
    ; now we have 356 cycles to copy data
    ; 1. line
    move.l (a3)+,d0 ; 12 cycles a3 points to the (left-)shifted previous character
    or.l (a4)+,d0   ; 16(14) cycles a4 points to the (right-)shifted new character
    move.l d0,(a5) ; 12 cycles, total of 40 cycles (instead of 20)
    ; 40
    ; 2. line
    move.l (a3)+,d0 ; 12 cycles a3 points to the (left-)shifted previous character
    or.l (a4)+,d0   ; 16(14) cycles a4 points to the (right-)shifted new character
    move.l d0,230(a5) ; 16 cycles, total of 44 cycles (instead of 24)
    ; 84
    ; 3. line
    move.l (a3)+,d0 ; 12 cycles a3 points to the (left-)shifted previous character
    or.l (a4)+,d0   ; 16(14) cycles a4 points to the (right-)shifted new character
    move.l d0,2*230(a5) ; 16 cycles, total of 44 cycles (instead of 24)
    ; 128
    ; 4. line
    move.l (a3)+,d0 ; 12 cycles a3 points to the (left-)shifted previous character
    or.l (a4)+,d0   ; 16(14) cycles a4 points to the (right-)shifted new character
    move.l d0,3*230(a5) ; 16 cycles, total of 44 cycles (instead of 24)
    ; 172
    ; 5. line
    move.l (a3)+,d0 ; 12 cycles a3 points to the (left-)shifted previous character
    or.l (a4)+,d0   ; 16(14) cycles a4 points to the (right-)shifted new character
    move.l d0,4*230(a5) ; 16 cycles, total of 44 cycles (instead of 24)
    ; 216
    ; 6. line
    move.l (a3)+,d0 ; 12 cycles a3 points to the (left-)shifted previous character
    or.l (a4)+,d0   ; 16(14) cycles a4 points to the (right-)shifted new character
    move.l d0,5*230(a5) ; 16 cycles, total of 44 cycles (instead of 24)
    ; 260
    ; 7. line
    move.l (a3)+,d0 ; 12 cycles a3 points to the (left-)shifted previous character
    or.l (a4)+,d0   ; 16(14) cycles a4 points to the (right-)shifted new character
    move.l d0,6*230(a5) ; 16 cycles, total of 44 cycles (instead of 24)
    ; 304
    ; 8. line
    move.l (a3)+,d0 ; 12 cycles a3 points to the (left-)shifted previous character
    or.l (a4)+,d0   ; 16(14) cycles a4 points to the (right-)shifted new character
    move.l d0,7*230(a5) ; 16 cycles, total of 44 cycles (instead of 24)
    ; 348
    ; two nops to 356, or: advance the a5 address by 8 lines
    lea 8*230(a5),a5
    nop

* RIGHT AGAIN...
    move.b  d4,(a0) ; 8 cycles
    move.b  d3,(a0) ; 8 cycles

    dcb.w   13,$4e71 ; 13*4 = 52 cycles

* EXTRA!
    move.b  d3,(a1) ; 8 cycles
    nop ; 4 cycles
    move.b  d4,(a1) ; 8 cycles

    dcb.w   12,$4e71 ; 13*4 = 52 cycles
    endr

; 91 lines until the bottom border, we split this into the final 31 lines and the top 60 lines (the final 31 lines contain the scrolltext)!
    rept 91-64+bot_lines+1-1
    ;rept    60

* LEFT HAND BORDER!
    move.b  d3,(a1)         ; to monochrome 8 cycles
    move.b  d4,(a1)         ; to lo-res     8 cycles    

    dcb.w   90,$4e71 ; 89*4 = 356 cycles

* RIGHT AGAIN...
    move.b  d4,(a0) ; 8 cycles
    move.b  d3,(a0) ; 8 cycles

    dcb.w   13,$4e71 ; 13*4 = 52 cycles

* EXTRA!
    move.b  d3,(a1) ; 8 cycles
    nop ; 4 cycles
    move.b  d4,(a1) ; 8 cycles

    dcb.w   12,$4e71 ; 13*4 = 52 cycles
    endr ; 512 cycles per line

; here starts the scroller (actually, in the next line!), so we can adjust the palette in the following 64 lines
; first line is special as we load the address registers
* LEFT HAND BORDER!
    move.b  d3,(a1)         ; to monochrome 8 cycles
    move.b  d4,(a1)         ; to lo-res     8 cycles    

    ;dcb.w   89,$4e71 ; 89*4 = 356 cycles
    dcb.w   61,$4e71
    move.l current_scrollerpal_sequence_struct+2,a5
    move.l (a5)+,a2 ; 12c
    move.w #$8240,a6 ; 8c
    movem.l (a2),d0-d2/d5-d7/a3-a4 ; 76c
    

* RIGHT AGAIN...
    move.b  d4,(a0) ; 8 cycles
    move.b  d3,(a0) ; 8 cycles

    ;dcb.w   13,$4e71 ; 13*4 = 52 cycles
    nop
    move.l d7,24(a6) ; 16c
    move.l a3,28(a6) ; 16c
    move.l a4,32(a6) ; 16c
* EXTRA!
    move.b  d3,(a1) ; 8 cycles
    nop ; 4 cycles
    move.b  d4,(a1) ; 8 cycles

    ;dcb.w   13,$4e71 ; 13*4 = 52 cycles
    ;nop
    movem.l d0-d2/d5-d6,(a6) ; 48c

    rept    31
* LEFT HAND BORDER!
    move.b  d3,(a1)         ; to monochrome 8 cycles
    move.b  d4,(a1)         ; to lo-res     8 cycles    

    ;dcb.w   89,$4e71 ; 89*4 = 356 cycles
    dcb.w   65,$4e71
    move.l (a5)+,a2 ; 12c
    move.w #$8240,a6 ; 8c
    movem.l (a2),d0-d2/d5-d7/a3-a4 ; 76c
    nop
* RIGHT AGAIN...
    move.b  d4,(a0) ; 8 cycles
    move.b  d3,(a0) ; 8 cycles

    ;dcb.w   13,$4e71 ; 13*4 = 52 cycles
    nop
    move.l d7,20(a6) ; 16c
    move.l a3,24(a6) ; 16c
    move.l a4,28(a6) ; 16c
* EXTRA!
    move.b  d3,(a1) ; 8 cycles
    nop ; 4 cycles
    move.b  d4,(a1) ; 8 cycles

    ;dcb.w   13,$4e71 ; 13*4 = 52 cycles
    ;nop
    movem.l d0-d2/d5-d6,(a6) ; 48c
    endr ; 512 cycles per line


* FINAL LINE...
* LEFT HAND BORDER!
    move.b  d3,(a1)         ; to monochrome 8 cycles
    move.b  d4,(a1)         ; to lo-res 8 cycles

    ; dcb.w   89,$4e71 ; 89*4 = 356 cycles
    dcb.w   57,$4e71
    move.l (a5)+,a2 ; 12c
    move.w #$8240,a6 ; 8c
    movem.l (a2),d0-d2/d5-d7/a3-a4 ; 76c

    move.l d5,12(a6)
    move.l d6,16(a6)
    nop

* RIGHT AGAIN...
    move.b  d4,(a0) ; 8 cycles
    move.b  d3,(a0) ; 8 cycles

    ;dcb.w   13,$4e71 ; 13*4 = 52 cycles
    nop
    move.l d7,20(a6) ; 16c
    move.l a3,24(a6) ; 16c
    move.l a4,28(a6) ; 16c
* EXTRA!
    move.b  d3,(a1) ; 8 cycles
    nop ; 4 cycles
    move.b  d4,(a1) ; 8 cycles

* BUST BOTTOM BORDER...
; mh, the following seems to only work in wakestate 1 & 3
;    dcb.w   8,$4e71 ; 8*4 = 32 cycles
;    move.b  d4,(a0) ; 8 cycles
;    move.b  d3,(a0) ; 8 cycles
    movem.l d0-d2,(a6) ; 32c

    ;dcb.w   8,$4e71 ; 8*4 = 32 cycles
    move.b  d4,(a0) ; 8 cycles
    ;nop
    move.b  d3,(a0) ; 8 cycles

; total of 512 cycles here also

    rept    bot_lines-1

* LEFT HAND BORDER!
    move.b  d3,(a1)         ; to monochrome
    move.b  d4,(a1)         ; to lo-res

    ;dcb.w   89,$4e71 ; 356 cycles
    dcb.w   66,$4e71
    move.l (a5)+,a2 ; 12c
    move.w #$8240,a6 ; 8c
    movem.l (a2),d0-d2/d5-d7/a3-a4 ; 76c

* RIGHT AGAIN...
    move.b  d4,(a0)
    move.b  d3,(a0)

    ;dcb.w   13,$4e71 ; 52 cycles
    nop
    move.l d7,20(a6) ; 16c
    move.l a3,24(a6) ; 16c
    move.l a4,28(a6) ; 16c
* EXTRA!
    move.b  d3,(a1)
    nop
    move.b  d4,(a1)

    ;dcb.w   13,$4e71 ; 48 cycles
    ;nop
    movem.l d0-d2/d5-d6,(a6) ; 48c
    
    endr ; same as before, 512 cycles per line

; very last line to be displayed, we set the global palette here
* LEFT HAND BORDER!
    move.b  d3,(a1)         ; to monochrome
    move.b  d4,(a1)         ; to lo-res

    ;dcb.w   89,$4e71 ; 356 cycles
    dcb.w   64,$4e71
    move.l current_pal_sequence_struct+2,a2
    ;move.l (a5)+,a2 ; 12c
    move.w #$8240,a6 ; 8c
    movem.l (a2),d0-d2/d5-d7/a3-a4 ; 76c

* RIGHT AGAIN...
    move.b  d4,(a0)
    move.b  d3,(a0)

    ;dcb.w   13,$4e71 ; 52 cycles
    nop
    move.l d7,20(a6) ; 16c
    move.l a3,24(a6) ; 16c
    move.l a4,28(a6) ; 16c
* EXTRA!
    move.b  d3,(a1)
    nop
    move.b  d4,(a1)

    ;dcb.w   13,$4e71 ; 48 cycles
    ;nop
    movem.l d0-d2/d5-d6,(a6) ; 48c

; adapted code of the original dosound xbios routine (https://st-news.com/issues/st-news-volume-2-issue-3/education/the-xbios-dosound-function)
    ; now, the time critical stuff is done, and we still have a few cycles for sound...
    lea current_dosound_sequence_struct,a1
    ; counter in 0(a1)
    move.w 0(a1),d0
    subq.w #1,d0
    bge .dosndexit2 ; counter still > 0, continue in the next vbi

    ; counter <=0 - continue here
    clr.w d0 ; reset counter to 0
    move.l 2(a1),d5 ; address of current dosound command entry
    tst.l d5
    beq.s .dosndexit2
    move.l d5,a5
.dosndnext:
    move.b (a5)+,d5 ; command
    bmi.s .dosndspecial ; negative = bit 7 set
    move.b d5,$ffff8800
    cmpi.b #$07,d5 ; register 7?
    bne.s .dosndwrreg ; no
    ; it was register 7, so we do some special treatment
    move.b (a5)+,d1
    and.b #$3f,d1 ; isolate bits 0-5
    move.b $ffff8800,d5 ; read mixer
    and.b #$c0,d5 ; isolate bits 6-7
    or.b d1,d5 ; "or" them
    move.b d5,$ffff8802
    bra.s .dosndnext ; continue on to the next
.dosndwrreg:
    move.b (a5)+,$ffff8802 ; simply write the value to the register
    bra.s .dosndnext ; continue on to the next
.dosndspecial:
    addq.b #1,d5 ; was the command $ff
    bpl .dosndsettimer ; yes, set the delay timer
    cmpi.b #$81,d5 ; was the command $80 (set temp. reg.)
    bne.s .dosndspecial2 ; no
    ; set the temporary reg.
    move.b (a5)+,6(a1)
    bra.s .dosndnext

.dosndspecial2:
    cmpi.b  #$82,d5 ; was the command $81
    bne.s .dosndsettimer ; no, set the delay timer

    move.b (a5)+,$ffff8800 ; select register
    move.b (a5)+,d5 ; increment value
    add.b d5,6(a1) ; add increment to temp reg.
    move.b (a5)+,d5 ; end value
    move.b 6(a1),$ffff8802 ; value to chip
    cmp.b 6(a1),d5
    beq.s .dosndexit ; end value reached, store the new current entry
    subq.w #4,a5 ; pointer back to the same command
    bra.s .dosndexit ; the next iteration of the loop will happen in the next vbi, keep everything as is

.dosndsettimer:
    move.b (a5)+,d0
    bne.s .dosndexit ; advance to the next command if timer value >0!
    move.w #0,a5 ; delay value was $00 -> clear current address, stop sound

.dosndexit:
    move.l a5,2(a1) ; new current entry
.dosndexit2:
    move.w d0,0(a1) ; write back counter (it is acutally only a byte in d0.b, but the upper byte of d0.w is cleared, so this should't be a problem)


.nosound:
    move.l scrollpos,a2
    move.w (a2),d4
    bge.s .contscroll3

    lea scrolltextbuffer,a2 ; 12 c / 3 nops
.contscroll3:


; last thing before exiting: set new screen address in hw regs
    move.w hw_screen,d7
    move.w #$8201,a0
    movep.w d7,0(a0)
    ;bra.s exit_vbi

    move.w screen_toggle,d0 ; maybe it is still in d0, but probably not
    lea scrolleraddrtables,a0
    move.l 0(a0,d0.w),a0 ; address of the scrolleraddrtable. here: 0 - address where the scroller screen start address is stored, font1, font2, character offsets, offset to add to scrollerpos
    move.l 0(a0),a1
    move.l 0(a1),scrollscraddr

    move.l 4(a0),font_addr1
    move.l 8(a0),font_addr2
    
    move.w 12(a0),d4
    move.w 14(a0),d5
    move.w (a2,d4.w),d4
    move.w (a2,d5.w),d5
    move.w d4,fontoffset1
    move.w d5,fontoffset2
    add.w 16(a0),a2
    move.l a2,scrollpos

exit_vbi:
; restore registers
    movem.l (sp)+,d0-d7/a0-a6
    move.w  (a7)+,sr

    rte

; initialize screen
init_screen:
; mouse off
    move.w  #34,-(sp)
    trap    #14             ; get table
    addq.l  #2,sp    
    move.l  d0,a0
    move.l  16(a0),mouse_vec        ; store mouse vector
    pea     0.w
    pea     0.w
    pea     0.w
    trap    #14             ; mouse off
    lea     12(sp),sp

; get the logical screen address (mostly to make it easier to debug, as devpac's mon messes with the phys base)
    move.w  #3,-(sp)
    trap    #14
    addq.l  #2,sp
    move.l  d0,logbase      ; keep old screen address

; get the current resolution
    move.w  #4,-(sp)
    trap    #14             ; get res
    addq.l  #2,sp
    move.w  d0,res          ; store it

; now get the palette
    move.l  #$ffff8240,a0
    lea     pal,a1
    movem.l (a0),d0-d7
    movem.l d0-d7,(a1)       ; just 2 instructions store the palette!

; now put me into low res...
    moveq   #0,d0
    moveq   #-1,d1
    bsr     set_scrn

    move.w #0,-(sp) ; operand, unused
    move.w #5,-(sp) ; function, 5=curs_getrate
    move.w #$15,-(sp) ; cursconf xbios 21
    trap #14
    addq.l #6,sp
    ;move.w d0,blink_rate
    ;move.w d0,curr_blink

    rts

restore:
; restore screen to how it was!
; first the res & screen address
    
    move.w  res,d0
    move.l  logbase,d1
    bsr     set_scrn
    
; now the old palette back again!
    lea     pal,a0
    move.l  #$ffff8240,a1

    movem.l (a0),d0-7
    movem.l d0-7,(a1)
    
* turn the mouse back on...
    move.l  mouse_vec,-(a7)
    pea     mouse_params(pc)
    move.w  #1,-(a7)
    clr.w   -(a7)
    trap    #14             ; turn mouse on
    lea     12(a7),a7

    rts


; setscreen - xbios 5
set_scrn:
    move.w  d0,-(sp)
    move.l  d1,-(sp)
    move.l  d1,-(sp)
    move.w  #5,-(sp)
    trap    #14
    lea     12(sp),sp
    rts

; gemdos 7 crawcin - raw input from standard input
inp:
    move.w  #7,-(sp)
    trap    #1
    addq.l  #2,sp
    rts

; prepare 16x16 sprite data, i.e. create 16 shifted versions and reorder words to match the screen planes
; input: a0 - mask + sprite data (16x dc.w mask,plane1,plane2,plane3,plane4)
;        a1 - where to put the prepared mask+data
prepare_sprite:
    moveq #15,d7 ; 16 lines
shift_line:
    moveq.l #$ffffffff,d0 ; mask needs to be filled with $ffff
    moveq.l #0,d1
    moveq.l #0,d2
    moveq.l #0,d3
    moveq.l #0,d4
    move.w (a0)+,d0
    move.w (a0)+,d1
    move.w (a0)+,d2
    move.w (a0)+,d3
    move.w (a0)+,d4
    ;movem.w (a0)+,d0-d4
    ; d0.w: mask; d1..d4.w: 4 planes
    swap d0
    swap d1
    swap d2
    swap d3
    swap d4

    moveq #16-1,d6 ; 16 shifts
    moveq #0,d5 ; shift offset
shift_one:
; reorder the data to match the planes
; 1. mask (is somewhat redundant, repeats the mask pattern 2 times)
    swap d0
    move.w d0,0(a1,d5)
    move.w d0,2(a1,d5)
    swap d0
    move.w d0,4(a1,d5)
    move.w d0,6(a1,d5)
    swap d1
    move.w d1,8(a1,d5)
    swap d1
    move.w d1,16(a1,d5)
    swap d2
    move.w d2,10(a1,d5)
    swap d2
    move.w d2,18(a1,d5)
    swap d3
    move.w d3,12(a1,d5)
    swap d3
    move.w d3,20(a1,d5)
    swap d4
    move.w d4,14(a1,d5)
    swap d4
    move.w d4,22(a1,d5)

    ror.l #1,d0
    ror.l #1,d1
    ror.l #1,d2
    ror.l #1,d3
    ror.l #1,d4

sprite_size_per_shift equ 384 ; size in bytes, (8 mask+16 data)*16 lines

    add.w #sprite_size_per_shift,d5 ; 1 sprite shift uses 16 lines * (8 bytes + 16 bytes) 
    dbra d6,shift_one

    lea 24(a1),a1 ; next line, 24 bytes per line
    dbra d7,shift_line

    rts

init_sprite:
    ; fill the current_sprite_sequence_struct
    ; - 0w: counter
    ; - 2l: address of animated sprite definition
    ; - 6l: address of next entry in sequence
    lea current_sprite_sequence_struct,a0
    ; sprite sequence

    lea spr_sequence,a1
    ; - 0w: delay
    ; - 2l: address of animated sprite definition
    ; - 6w: screen address offset
    ; - 8w: sprite shift address offset
    ; - 10w: offset to next entry in sequence (0 = repeat forever)
    move.w 0(a1),0(a0)
    move.l 2(a1),2(a0) ; current ani spr
    move.w 6(a1),d0 ; screen offset
    move.w 8(a1),d1 ; sprite shift offset
    add.w 10(a1),a1 ; offset to next entry
    move.l a1,6(a0) ; set address of next entry in current struct

    ; fill current_ani_sprite_struct
    ; this struct needs to contain:
    ; - 0w: counter which counts to (including) 0 (delay value)
    ; - 2l: pointer to the sprite data (base address)
    ; - 6w: offset to the correct shift (sprite_size_per_shift(384) bytes * shift (x % 16))
    ; - 8w: offset to the screen address (230 * y coordinate + x offset (x // 16 * 8))
    ; - 10l: pointer to the *next* position in the animated sprite definition (f.e. ani_spr_cursor)
    move.l 2(a0),a2 ;
    lea current_ani_sprite_struct,a1
    move.w 0(a2),0(a1) ; delay
    move.l 2(a2),2(a1) ; sprite data address
    move.w d0,8(a1) ; screen offset
    move.w d1,6(a1) ; sprite shift offset
    add.w 6(a2),a2 ; 6(a2) is the offset in the animated sprite definition to the next sprite (can be negative to point to the beginning or so)
    move.l a2,10(a1)
    
    lea current_sprite_sequence_struct2,a0
    ; sprite sequence

    lea spr_sequence2,a1
    ; - 0w: delay
    ; - 2l: address of animated sprite definition
    ; - 6w: screen address offset
    ; - 8w: sprite shift address offset
    ; - 10w: offset to next entry in sequence (0 = repeat forever)
    move.w 0(a1),0(a0)
    move.l 2(a1),2(a0)
    move.w 6(a1),d0 ; screen offset
    move.w 8(a1),d1 ; sprite shift offset
    add.w 10(a1),a1 ; offset to next entry
    move.l a1,6(a0) ; set address of next entry in current struct

    move.l 2(a0),a2 ;
    lea current_ani_sprite_struct2,a1
    move.w 0(a2),0(a1) ; delay
    move.l 2(a2),2(a1) ; sprite data address
    move.w d0,8(a1) ; screen offset
    move.w d1,6(a1) ; sprite shift offset
    add.w 6(a2),a2 ; 6(a2) is the offset in the animated sprite definition to the next sprite (can be negative to point to the beginning or so)
    move.l a2,10(a1)

    ; initially save the sprite background (make it empty, this is to save a few bytes code instead of really storing the bg)
    lea spr_bg1,a1
    lea spr_bg2,a2
    move.l screen1,(a1)+ ; upper left border, we don't care
    move.l screen2,(a2)+
    rept 16
    move.l #0,(a1)+
    move.l #0,(a1)+
    move.l #0,(a1)+
    move.l #0,(a1)+
    move.l #0,(a2)+
    move.l #0,(a2)+
    move.l #0,(a2)+
    move.l #0,(a2)+
    endr

    lea spr_bg3,a1
    lea spr_bg4,a2
    move.l screen1,(a1)+ ; upper left border, we don't care
    move.l screen2,(a2)+
    rept 16
    move.l #0,(a1)+
    move.l #0,(a1)+
    move.l #0,(a1)+
    move.l #0,(a1)+
    move.l #0,(a2)+
    move.l #0,(a2)+
    move.l #0,(a2)+
    move.l #0,(a2)+
    endr

    ; init also the current pal and the current snd
    lea current_pal_sequence_struct,a0
    lea pal_sequence,a1
    move.w (a1),(a0) ; delay
    move.l 2(a1),2(a0) ; palette address
    add.w 6(a1),a1
    move.l a1,6(a0)

    ; the sound and dosound sequences work a little different, the delay is applied _before_ the sound is player, so we start with an empty current entry for both
    lea current_snd_sequence_struct,a0
    lea snd_sequence,a1
    move.w (a1),(a0) ; delay
    move.l #0,2(a0)
    move.l a1,6(a0)

    lea current_dosound_sequence_struct,a0
    move.w #0,(a0) ; counter (different from other counters!)
    move.l #0,2(a0)
    move.w #0,6(a0) ; temp var + filler

    lea current_scrollerpal_sequence_struct,a0
    lea scrollerpal_sequence,a1
    move.w (a1),(a0) ; delay
    lea scrollerpals,a2
    move.l a2,2(a0)
    add.w 6(a1),a1
    move.l a1,6(a0)

    rts

prepare_pal:
    ; pointer to the original pal in a0, target pal in a1
    ; we simply replace the bg color with white
    move.w #$0777,(a1)+ ; color #0
    addq #2,a0
    move.w (a0)+,(a1)+ ; color #1
    move.l (a0)+,(a1)+ ; color #2,#3
    move.l (a0)+,(a1)+ ; color #4,#5
    move.l (a0)+,(a1)+ ; color #6,#7
    move.l (a0)+,(a1)+ ; color #8,#9
    move.l (a0)+,(a1)+ ; color #10,#11
    move.l (a0)+,(a1)+ ; color #12,#13
    move.l (a0)+,(a1)+ ; color #14,#15
    rts

; bit zip algorithm from fxtbook for 2 16 bit values
; input d0.w [ a b c d e f g h i j k l m n o p ] d1.w [ A B C D E F G H I J K L M N O P ]
; output d0.l [ a A b B c C d D e E f F g G h H ...]
bit_zip16:
    movem.l d2-d7,-(sp)

    moveq #1,d3 ; m = 1
    moveq #0,d4 ; s = 0
    moveq #0,d2 ; x
    moveq #15,d7 ; d7 = k, BITS_PER_LONG/2 = 16
.bzloop:
    move.l d0,d5
    and.l d3,d5
    lsl.l d4,d5
    or.l d5,d2
    addq #1,d4
    move.l d1,d5
    and.l d3,d5
    lsl.l d4,d5
    or.l d5,d2
    lsl.l #1,d3

    dbra d7,.bzloop
    move.l d2,d0 ; return value
    movem.l (sp)+,d2-d7
    rts

; bit zip algorithm from fxtbook for 2 8 bit values
; input d0.b [ a b c d e f g h ] d1.b [ A B C D E F G H ]
; output d0.w [ a A b B c C d D e E f F g G h H ]
bit_zip8:
    movem.l d2-d7,-(sp)

    moveq #1,d3 ; m = 1
    moveq #0,d4 ; s = 0
    moveq #0,d2 ; x = 0
    moveq #7,d7 ; d7 = k, BITS_PER_LONG/2 = 8
.bzloop:
    move.w d0,d5
    and.w d3,d5
    lsl.w d4,d5
    or.w d5,d2
    addq #1,d4
    move.w d1,d5
    and.w d3,d5
    lsl.w d4,d5
    or.w d5,d2
    lsl.w #1,d3

    dbra d7,.bzloop
    move.w d2,d0 ; return value
    movem.l (sp)+,d2-d7
    rts

prepare_font:
    ; load the 8x8 font from the tos rom
    dc.w $a000
    ; in a0 (and d0) ptr to line-a structure
    ; in a1: pointer to address table to font headers of system fonts
    move.l 8(a1),a0 ; default font 8x16
    
    move.l 76(a0),a0 ; actual font data, which is 256 characters, 
    ; ordering is: 1 byte first line of first char, next byte is first line of second char, 
    ; ..., 256th byte is first line of 256th char, 257th byte is second line of 1st char, ... 
    ; so, it is a 256x16 image, where we f.e. pick the character at x-position 65*8 (for "A")
    lea font,a1
    ; we blow up the 8x16 font to 32x64 (basically: every bit becomes a nibble/byte), width is 32 bit/4 bytes/2 words/1 lw, height is 64 lines
    ; storage is 1. line left half, 1. plane, 2. plane, 2. line left half, 1. plane, 2. plane, ..., 64. line left half, 1. plane, 2. plane, 1. line right half, ...

    move.l a0,a2 ; save the font data
    lea pick_sysfont_chars,a3

    moveq #31,d6 ; 32 chars
.onechar:
    move.l a2,a0
    clr.w d0
    move.b (a3)+,d0
    add.w d0,a0
    moveq #15,d7 ; 16 lines, font is 8x16
.oneline:
    moveq #0,d0
    moveq #0,d1
    move.b (a0),d0
    add.l #256,a0 ; next line
    move.b d0,d1
    bsr bit_zip8
    ; d0.w is now the doubled first line of the char
    move.w d0,d1
    bsr bit_zip16
    ; d0.l is now the blown up line of the char

    ; save it in d4
    move.l d0,d4
    ; left part
    swap d0
    moveq #0,d1
    move.w d0,d1
    bsr bit_zip16
    ; d0.l left part blown up to 32 pixels
    ; save it to d5
    move.l d0,d5
    moveq #0,d0
    move.w d4,d0
    moveq #0,d1
    move.w d0,d1
    bsr bit_zip16

    ; now: d0.l is the right part blown up to 32 pixels, d5.l is the left part blown up to 32 pixels

    ; now the first line needs to be reordered to 1st plane/2nd plane of left part and then offset to the right part 1st/2nd plane (2w * 64 lines = 256 bytes)

    ; plane 1
    ; 1 line left
    swap d5
    move.w d5,0(a1) ; plane 1
    move.w d5,4(a1) ; plane 1
    move.w d5,8(a1) ; plane 1
    move.w d5,12(a1) ; plane 1
    ; 1 line left 2
    swap d5
    move.w d5,256(a1)
    move.w d5,260(a1)
    move.w d5,264(a1)
    move.w d5,268(a1)
    ; plane 2
    ; 1 line left
    swap d5
    asr.w #3,d5
    move.w d5,2(a1) ; plane 2
    move.w d5,6(a1) ; plane 2
    move.w d5,10(a1) ; plane 2
    move.w d5,14(a1) ; plane 2
    ; 1 line left 2
    swap d5
    asr.w #3,d5
    move.w d5,258(a1)
    move.w d5,262(a1)
    move.w d5,266(a1)
    move.w d5,270(a1)

    ; plane 1
    ; 1 line right
    swap d0
    move.w d0,512(a1) ; plane 1
    move.w d0,516(a1) ; plane 1
    move.w d0,520(a1) ; plane 1
    move.w d0,524(a1) ; plane 1
    ; 1 line right 2
    swap d0
    move.w d0,768(a1)
    move.w d0,772(a1)
    move.w d0,776(a1)
    move.w d0,780(a1)
    ; plane 2
    ; 1 line right
    swap d0
    asr.w #3,d0
    move.w d0,514(a1) ; plane 2
    move.w d0,518(a1) ; plane 2
    move.w d0,522(a1) ; plane 2
    move.w d0,526(a1) ; plane 2
    ; 1 line right 2
    swap d0
    asr.w #3,d0
    move.w d0,770(a1)
    move.w d0,774(a1)
    move.w d0,778(a1)
    move.w d0,782(a1)

    add.l #16,a1
    dbra d7,.oneline
    add.l #768,a1
    dbra d6,.onechar

    ; next: create the 8-bit shifted variants after the regular font
    lea font,a0
    lea font_shift_r,a1
    lea font_shift_l,a2

    move.w #4*32*64*2-1,d7 ; 4x32 characters,64 lines,2 words per line
.charshift:
    move.w (a0)+,d0
    move.w d0,d1
    lsr.w #8,d0
    move.w d0,(a1)+
    lsl.w #8,d1
    move.w d1,(a2)+
    dbra d7,.charshift

    rts

prepare_scrolltext:
    lea scrolltext,a0
    lea scrolltextbuffer,a1

    move.w #scrolltextsize-1,d7
.onechar:
    moveq #0,d0
    move.b (a0)+,d0
    ; sub.b #65,d0 ; subtract 'A'
    ; mulu #fontcharactersize,d0 ; i.e. *256, and then we need to multiply *4 (for all 4 parts) we can do this better:
    lsl.w #8,d0
    lsl.w #2,d0
    move.w d0,(a1)+
    add.w #256,d0
    move.w d0,(a1)+
    add.w #256,d0
    move.w d0,(a1)+
    add.w #256,d0
    move.w d0,(a1)+

    dbra d7,.onechar
    move.w #-1,(a1)
    ; move.w -2(a1),prev_scrolltextentry
    move.w #0,prev_scrolltextentry ; start with a space as the previous character
    rts

    data

pick_sysfont_chars:
    dc.b $20,$41,$42,$43,$44,$45,$46,$47,$48,$49,$4a,$4b,$4c,$4d,$4e,$4f ; [ ],A,B,C,D,E,...,O
    dc.b $50,$51,$52,$53,$54,$55,$56,$57,$58,$59,$5a,$2e,$2d,$21,$0e,$0f ; P,Q,...,Z,.,-,!,[atarileft],[atariright]

pal_sequence:
    dc.w 1000 ; delay
    dc.l pal_start ; address of the new palette
    dc.w 8 ; offset to the next entry
    dc.w 100 ; delay
    dc.l pal_black ; address of the new palette
    dc.w 8 ; offset to the next entry
    dc.w 5 ; delay
    dc.l pal_black1 ; address of the new palette
    dc.w 8 ; offset to the next entry
    dc.w 5 ; delay
    dc.l pal_black2 ; address of the new palette
    dc.w 8 ; offset to the next entry
    dc.w 100 ; delay
    dc.l pal_black ; address of the new palette
    dc.w 8 ; offset to the next entry
    dc.w 50 ; delay
    dc.l pal_black3 ; address of the new palette
    dc.w -8*4 ; offset to the next entry

snd_sequence: ; as opposed to the other sequences, the sound is played when the delay counter has run out. at the moment, the keyclick data is actually ignored and always the same click is played
    dc.w 50
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 25
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 25
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 25
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 25
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 25
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 25
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 25
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 25
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 25
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 25
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 25
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    
    dc.w 5
    dc.l snd_bell_dosound
    dc.w 8

    dc.w 50 ; going back
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 10
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8
    dc.w 5
    dc.l snd_keyclick_dosound
    dc.w 8

    dc.w 5
    dc.l snd_bell_dosound
    dc.w 8

    dc.w 15
    dc.l snd_bell_dosound
    dc.w 8

    dc.w 5
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 5
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 5
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 5
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 5
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 5
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 2
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 2
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 2
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 2
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 2
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 2
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 2
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 2
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 2
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 2
    dc.l snd_bell_dosound
    dc.w 8
    dc.w 2
    dc.l snd_bell_dosound
    dc.w 8

    dc.w 2
    dc.l snd_crash_dosound
    dc.w 8
  
    dc.w 10
    dc.l music
    dc.w 8  
    dc.w 3200  
    dc.l music
    dc.w 0

    ; the sprite sequence - sprite 1
    ; 2s start position, then moving a few steps to the right at increasing speed
spr_sequence:
    dc.w 100 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l ani_spr_cursor ; 2l: animated sprite definition
    dc.w 230*(28-4)+24 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 25 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+24 ; 6w: screen address offset
    dc.w 1*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 25 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+32 ; 6w: screen address offset
    dc.w 0*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 25 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+32 ; 6w: screen address offset
    dc.w 1*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 25 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+40 ; 6w: screen address offset
    dc.w 0*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 25 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+40 ; 6w: screen address offset
    dc.w 1*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 25 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+48 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 25 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+48 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 25 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+56 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 25 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+56 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 25 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+64 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 25 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+64 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+72 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+72 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+80 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+80 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+88 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+88 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+96 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+96 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+104 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+104 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+112 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+112 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+120 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+120 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+128 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+128 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+136 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+136 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+144 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+144 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+152 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+152 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+160 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+160 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+168 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+168 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+176 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+176 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)

; question mark
    dc.w 50 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l ani_spr_qm ; 2l: animated sprite definition
    dc.w 230*(28-4)+176 ; 6w: screen address offset
    dc.w sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)

; going back
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l ani_spr_cursor ; 2l: animated sprite definition
    dc.w 230*(28-4)+176 ; 6w: screen address offset
    dc.w 1*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+176 ; 6w: screen address offset
    dc.w 0*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+168 ; 6w: screen address offset
    dc.w 1*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+168 ; 6w: screen address offset
    dc.w 1*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+168 ; 6w: screen address offset
    dc.w 0*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+160 ; 6w: screen address offset
    dc.w 1*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+160 ; 6w: screen address offset
    dc.w 0*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+152 ; 6w: screen address offset
    dc.w 1*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 10 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+152 ; 6w: screen address offset
    dc.w 0*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)

    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+152 ; 6w: screen address offset
    dc.w 1*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+160 ; 6w: screen address offset
    dc.w 0*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+160 ; 6w: screen address offset
    dc.w 1*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+168 ; 6w: screen address offset
    dc.w 0*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+168 ; 6w: screen address offset
    dc.w 1*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+176 ; 6w: screen address offset
    dc.w 0*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+176 ; 6w: screen address offset
    dc.w 1*sprite_size_per_shift*8 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+176 ; 6w: screen address offset
    dc.w sprite_size_per_shift*9 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+176 ; 6w: screen address offset
    dc.w sprite_size_per_shift*10 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+176 ; 6w: screen address offset
    dc.w sprite_size_per_shift*11 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+176 ; 6w: screen address offset
    dc.w sprite_size_per_shift*12 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+176 ; 6w: screen address offset
    dc.w sprite_size_per_shift*13 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+176 ; 6w: screen address offset
    dc.w sprite_size_per_shift*14 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 5 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+176 ; 6w: screen address offset
    dc.w sprite_size_per_shift*15 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
    dc.w 50 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l 0 ; 2l: animated sprite definition
    dc.w 230*(28-4)+184 ; 6w: screen address offset
    dc.w sprite_size_per_shift*0 ; 8w: sprite shift address offset
    dc.w 24 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)

spr_sequence2:
    dc.w 700 ; 0w: delay (1000 = 20s, 500 = 10s, ...)
    dc.l ani_spr_cursor ; 2l: animated sprite definition
    dc.w 230*(28-4+16)+192 ; 6w: screen address offset
    dc.w 0 ; 8w: sprite shift address offset
    dc.w 12 ; 10w: offset to next entry in sequence (0 = repeat forever, 12 = next entry)
 
    include 'gen_lissajous.s'


ani_spr_cursor:
    dc.w 25 ; delay
    dc.l spr_cursor ; sprite data
    dc.w 8 ; offset to the next entry
    dc.w 25
    if DEBUG
    dc.l spr_cursor
    else
    dc.l spr_empty ; sprite data
    endif
    dc.w -8 ; affset to the next entry (go backwards)

ani_spr_qm:
    dc.w 25
    dc.l spr_qm1
    dc.w 8
    dc.w 25
    dc.l spr_qm3
    dc.w -8

ani_spr_empty:
    dc.w 10
    dc.l spr_empty
    dc.w 0

ani_spr_butterfly:
    dc.w 10
    dc.l spr_butterfly_0
    dc.w 8
    dc.w 10
    dc.l spr_butterfly_1
    dc.w -8

raw_sprites:
; 0
raw_spr_empty:
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000

    include 'gen_butterfly.s'

; 1
raw_spr_cursor:
    if DEBUG
    dc.w $0FFF,$f000,$f000,$0000,$0000
    else
    dc.w $FFFF,$0000,$0000,$0000,$0000
    endif
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $F00F,$0FF0,$0FF0,$0000,$0000
    dc.w $F00F,$0FF0,$0FF0,$0000,$0000
    dc.w $F00F,$0FF0,$0FF0,$0000,$0000
    dc.w $F00F,$0FF0,$0FF0,$0000,$0000
    dc.w $F00F,$0FF0,$0FF0,$0000,$0000
    dc.w $F00F,$0FF0,$0FF0,$0000,$0000
    dc.w $F00F,$0FF0,$0FF0,$0000,$0000
    dc.w $F00F,$0FF0,$0FF0,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    if DEBUG
    dc.w $0FFF,$f000,$0000,$f000,$0000
    else
    dc.w $FFFF,$0000,$0000,$0000,$0000
    endif

raw_spr_qm1: ; question mark small 8x8
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FC3F,$03C0,$03C0,$0000,$0000
    dc.w $F99F,$0660,$0660,$0000,$0000
    dc.w $FF9F,$0060,$0060,$0000,$0000
    dc.w $FF3F,$00C0,$00C0,$0000,$0000
    dc.w $FE7F,$0180,$0180,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FE7F,$0180,$0180,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000

raw_spr_qm3: ; question mark 16x16
    dc.w $F00F,$0FF0,$0FF0,$0000,$0000
    dc.w $F00F,$0FF0,$0FF0,$0000,$0000
    dc.w $C3C3,$3C3C,$3C3C,$0000,$0000
    dc.w $C3C3,$3C3C,$3C3C,$0000,$0000
    dc.w $FFC3,$003C,$003C,$0000,$0000
    dc.w $FFC3,$003C,$003C,$0000,$0000
    dc.w $FF0F,$00F0,$00F0,$0000,$0000
    dc.w $FF0F,$00F0,$00F0,$0000,$0000
    dc.w $FC3F,$03C0,$03C0,$0000,$0000
    dc.w $FC3F,$03C0,$03C0,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FC3F,$03C0,$03C0,$0000,$0000
    dc.w $FC3F,$03C0,$03C0,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000
    dc.w $FFFF,$0000,$0000,$0000,$0000

mouse_params:
    dc.b    0,1,1,1

pal_start: ; default palette. we start with a white bg, plane 1+2 are for the background, plane 3+4 are for the scroller
    ; plane 1+2 %0000,%1000,%0100,%1100 ->  4,8,12
    ; plane 3+4 %0000,%0010,%0001,%0011 ->  1,2,3
    dc.w $0777 ; 0 %0000 bg
    if DEBUG
    dc.w $0500 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0700 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    else
    dc.w $0777 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0777 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    endif
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0000 ; 3 inital cursor color (black)
    endif
    dc.w $0333 ; 4 scroller border left
    dc.w $0333 ; 5 scroller border left
    dc.w $0333 ; 6 scroller border left
    dc.w $0333 ; 7 scroller border left
    dc.w $0406 ; 8 scroller border right
    dc.w $0547 ; 9 scroller border right
    dc.w $0272 ; 10 scroller border right
    dc.w $0222 ; 11 scroller border right
    dc.w $0000 ; 12 scroller main color
    dc.w $0000 ; 13 scroller main color
    dc.w $0000 ; 14 scroller main color
    dc.w $0000 ; 15 scroller main color

pal_black: ; default palette. we start with a white bg, plane 1+2 are for the background, plane 3+4 are for the scroller
    ; plane 1+2 %0000,%1000,%0100,%1100 ->  4,8,12
    ; plane 3+4 %0000,%0010,%0001,%0011 ->  1,2,3
    dc.w $0000 ; 0 %0000 bg
    if DEBUG
    dc.w $0700 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0700 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    else
    dc.w $0000 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0000 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    endif
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0777 ; 3 inital cursor color (black)
    endif
    dc.w $0222 ; 4 scroller border left
    dc.w $0222 ; 5 scroller border left
    dc.w $0222 ; 6 scroller border left
    dc.w $0222 ; 7 scroller border left
    dc.w $0406 ; 8 scroller border right
    dc.w $0547 ; 9 scroller border right
    dc.w $0272 ; 10 scroller border right
    dc.w $0333 ; 11 scroller border right
    dc.w $0444 ; 12 scroller main color
    dc.w $0444 ; 13 scroller main color
    dc.w $0444 ; 14 scroller main color
    dc.w $0444 ; 15 scroller main color

pal_black1: ; default palette. we start with a white bg, plane 1+2 are for the background, plane 3+4 are for the scroller
    ; plane 1+2 %0000,%1000,%0100,%1100 ->  4,8,12
    ; plane 3+4 %0000,%0010,%0001,%0011 ->  1,2,3
    dc.w $0000 ; 0 %0000 bg
    if DEBUG
    dc.w $0501 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0000 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    else
    dc.w $0750
    ; dc.w $0501 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0000 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    endif
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0777 ; 3 inital cursor color (black)
    endif
    dc.w $0222 ; 4 scroller border left
    dc.w $0222 ; 5 scroller border left
    dc.w $0222 ; 6 scroller border left
    dc.w $0222 ; 7 scroller border left
    dc.w $0406 ; 8 scroller border right
    dc.w $0547 ; 9 scroller border right
    dc.w $0272 ; 10 scroller border right
    dc.w $0333 ; 11 scroller border right
    dc.w $0444 ; 12 scroller main color
    dc.w $0444 ; 13 scroller main color
    dc.w $0444 ; 14 scroller main color
    dc.w $0444 ; 15 scroller main color

pal_black2: ; default palette. we start with a white bg, plane 1+2 are for the background, plane 3+4 are for the scroller
    ; plane 1+2 %0000,%1000,%0100,%1100 ->  4,8,12
    ; plane 3+4 %0000,%0010,%0001,%0011 ->  1,2,3
    dc.w $0000 ; 0 %0000 bg
    if DEBUG
    dc.w $0700 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0700 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    else
    dc.w $0000 ; 1 initial border color (invisible, change to 777 later) (further out)
    ;dc.w $0302 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    dc.w $0730
    endif
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0777 ; 3 inital cursor color (black)
    endif
    dc.w $0222 ; 4 scroller border left
    dc.w $0222 ; 5 scroller border left
    dc.w $0222 ; 6 scroller border left
    dc.w $0222 ; 7 scroller border left
    dc.w $0406 ; 8 scroller border right
    dc.w $0547 ; 9 scroller border right
    dc.w $0272 ; 10 scroller border right
    dc.w $0333 ; 11 scroller border right
    dc.w $0444 ; 12 scroller main color
    dc.w $0444 ; 13 scroller main color
    dc.w $0444 ; 14 scroller main color
    dc.w $0444 ; 15 scroller main color

pal_black3: ; default palette. we start with a white bg, plane 1+2 are for the background, plane 3+4 are for the scroller
    ; plane 1+2 %0000,%1000,%0100,%1100 ->  4,8,12
    ; plane 3+4 %0000,%0010,%0001,%0011 ->  1,2,3
    dc.w $0000 ; 0 %0000 bg
    if DEBUG
    dc.w $0700 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0700 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    else
    dc.w $750
    dc.w $730
    endif
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0777 ; 3 inital cursor color (black)
    endif
    dc.w $0222 ; 4 scroller border left
    dc.w $0222 ; 5 scroller border left
    dc.w $0222 ; 6 scroller border left
    dc.w $0222 ; 7 scroller border left
    dc.w $0406 ; 8 scroller border right
    dc.w $0547 ; 9 scroller border right
    dc.w $0272 ; 10 scroller border right
    dc.w $0333 ; 11 scroller border right
    dc.w $0444 ; 12 scroller main color
    dc.w $0444 ; 13 scroller main color
    dc.w $0444 ; 14 scroller main color
    dc.w $0444 ; 15 scroller main color

pal_border1: ; default palette. we start with a white bg, plane 1+2 are for the background, plane 3+4 are for the scroller
    ; plane 1+2 %0000,%1000,%0100,%1100 ->  4,8,12
    ; plane 3+4 %0000,%0010,%0001,%0011 ->  1,2,3
    dc.w $0777 ; 0 %0000 bg
    dc.w $0501 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0777 ; $0301 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0000 ; 3 inital cursor color (black)
    endif
    dc.w $0333 ; 4 scroller border left
    dc.w $0333 ; 5 scroller border left
    dc.w $0333 ; 6 scroller border left
    dc.w $0333 ; 7 scroller border left
    dc.w $0222 ; 8 scroller border right
    dc.w $0222 ; 9 scroller border right
    dc.w $0222 ; 10 scroller border right
    dc.w $0222 ; 11 scroller border right
    dc.w $0000 ; 12 scroller main color
    dc.w $0000 ; 13 scroller main color
    dc.w $0000 ; 14 scroller main color
    dc.w $0000 ; 15 scroller main color

pal_border2: ; default palette. we start with a white bg, plane 1+2 are for the background, plane 3+4 are for the scroller
    ; plane 1+2 %0000,%1000,%0100,%1100 ->  4,8,12
    ; plane 3+4 %0000,%0010,%0001,%0011 ->  1,2,3
    dc.w $0777 ; 0 %0000 bg
    dc.w $0777 ; $0601 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0401 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0000 ; 3 inital cursor color (black)
    endif
    dc.w $0333 ; 4 scroller border left
    dc.w $0333 ; 5 scroller border left
    dc.w $0333 ; 6 scroller border left
    dc.w $0333 ; 7 scroller border left
    dc.w $0222 ; 8 scroller border right
    dc.w $0222 ; 9 scroller border right
    dc.w $0222 ; 10 scroller border right
    dc.w $0222 ; 11 scroller border right
    dc.w $0000 ; 12 scroller main color
    dc.w $0000 ; 13 scroller main color
    dc.w $0000 ; 14 scroller main color
    dc.w $0000 ; 15 scroller main color

pal_border3: ; default palette. we start with a white bg, plane 1+2 are for the background, plane 3+4 are for the scroller
    ; plane 1+2 %0000,%1000,%0100,%1100 ->  4,8,12
    ; plane 3+4 %0000,%0010,%0001,%0011 ->  1,2,3
    dc.w $0777 ; 0 %0000 bg
    dc.w $0701 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0601 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0000 ; 3 inital cursor color (black)
    endif
    dc.w $0333 ; 4 scroller border left
    dc.w $0333 ; 5 scroller border left
    dc.w $0333 ; 6 scroller border left
    dc.w $0333 ; 7 scroller border left
    dc.w $0222 ; 8 scroller border right
    dc.w $0222 ; 9 scroller border right
    dc.w $0222 ; 10 scroller border right
    dc.w $0222 ; 11 scroller border right
    dc.w $0000 ; 12 scroller main color
    dc.w $0000 ; 13 scroller main color
    dc.w $0000 ; 14 scroller main color
    dc.w $0000 ; 15 scroller main color

pal_border4: ; default palette. we start with a white bg, plane 1+2 are for the background, plane 3+4 are for the scroller
    ; plane 1+2 %0000,%1000,%0100,%1100 ->  4,8,12
    ; plane 3+4 %0000,%0010,%0001,%0011 ->  1,2,3
    dc.w $0777 ; 0 %0000 bg
    dc.w $0700 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0700 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0000 ; 3 inital cursor color (black)
    endif
    dc.w $0333 ; 4 scroller border left
    dc.w $0333 ; 5 scroller border left
    dc.w $0333 ; 6 scroller border left
    dc.w $0333 ; 7 scroller border left
    dc.w $0222 ; 8 scroller border right
    dc.w $0222 ; 9 scroller border right
    dc.w $0222 ; 10 scroller border right
    dc.w $0222 ; 11 scroller border right
    dc.w $0000 ; 12 scroller main color
    dc.w $0000 ; 13 scroller main color
    dc.w $0000 ; 14 scroller main color
    dc.w $0000 ; 15 scroller main color

scrollerpal_sequence:
    dc.w 1300
    dc.l 0 ; increment
    dc.w 8

    dc.w 2 ; 0w: delay <- repeat enters here
    dc.l 64*4 ; increment -> 64. entry, start of the red palette
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)

    dc.w 2 ; 0w: delay <- repeat enters here
    dc.l 4 ; increment (+4)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+8)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+12)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+16)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+20)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+24)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+28)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+32)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+36)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+40)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+44)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+48)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+52)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+56)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+60)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+64)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+68)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+72)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+76)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+80)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+84)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+88)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+92)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+96)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+16)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+100)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+104)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+108)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+112)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+116)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+120)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 4 ; increment (+124)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l 0 ; increment (+124)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+120)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+116)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+112)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+108)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+104)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+100)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+96)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+92)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+88)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+84)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+80)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+76)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+72)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+68)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+64)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+60)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+56)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+52)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+48)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+44)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+40)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+36)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+32)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+28)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+24)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+20)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+16)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+12)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+8)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+4)
    dc.w 8 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)
    dc.w 2 ; 0w: delay
    dc.l -4 ; increment (+0)
    dc.w -8*62 ; 6w: offset to the next entry (0: repeat forever, 8: next entry)  

scrollerpals_start: ; constant 64 palettes, same as the upper half of the screen
scrollerpals: ; offset 0
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start
    dc.l pal_start


scrollerpals_2: ; 64 palettes
    dc.l scrollerpalred1
    dc.l scrollerpalred1
    dc.l scrollerpalred1
    dc.l scrollerpalred1
    dc.l scrollerpalred2
    dc.l scrollerpalred2
    dc.l scrollerpalred2
    dc.l scrollerpalred2
    dc.l scrollerpalred3
    dc.l scrollerpalred3
    dc.l scrollerpalred3
    dc.l scrollerpalred3
    dc.l scrollerpalred4
    dc.l scrollerpalred4
    dc.l scrollerpalred4
    dc.l scrollerpalred4
    dc.l scrollerpalred4
    dc.l scrollerpalred4
    dc.l scrollerpalred4
    dc.l scrollerpalred4
    dc.l scrollerpalred3
    dc.l scrollerpalred3
    dc.l scrollerpalred3
    dc.l scrollerpalred3
    dc.l scrollerpalred2
    dc.l scrollerpalred2
    dc.l scrollerpalred2
    dc.l scrollerpalred2
    dc.l scrollerpalred1
    dc.l scrollerpalred1
    dc.l scrollerpalred1
    dc.l scrollerpalred1
    dc.l scrollerpalblue1
    dc.l scrollerpalblue1
    dc.l scrollerpalblue1
    dc.l scrollerpalblue1
    dc.l scrollerpalblue2
    dc.l scrollerpalblue2
    dc.l scrollerpalblue2
    dc.l scrollerpalblue2
    dc.l scrollerpalblue3
    dc.l scrollerpalblue3
    dc.l scrollerpalblue3
    dc.l scrollerpalblue3
    dc.l scrollerpalblue4
    dc.l scrollerpalblue4
    dc.l scrollerpalblue4
    dc.l scrollerpalblue4
    dc.l scrollerpalblue4
    dc.l scrollerpalblue4
    dc.l scrollerpalblue4
    dc.l scrollerpalblue4
    dc.l scrollerpalblue3
    dc.l scrollerpalblue3
    dc.l scrollerpalblue3
    dc.l scrollerpalblue3
    dc.l scrollerpalblue2
    dc.l scrollerpalblue2
    dc.l scrollerpalblue2
    dc.l scrollerpalblue2
    dc.l scrollerpalblue1
    dc.l scrollerpalblue1
    dc.l scrollerpalblue1
    dc.l scrollerpalblue1
    dc.l scrollerpalred1
    dc.l scrollerpalred1
    dc.l scrollerpalred1
    dc.l scrollerpalred1
    dc.l scrollerpalred2
    dc.l scrollerpalred2
    dc.l scrollerpalred2
    dc.l scrollerpalred2
    dc.l scrollerpalred3
    dc.l scrollerpalred3
    dc.l scrollerpalred3
    dc.l scrollerpalred3
    dc.l scrollerpalred4
    dc.l scrollerpalred4
    dc.l scrollerpalred4
    dc.l scrollerpalred4
    dc.l scrollerpalred4
    dc.l scrollerpalred4
    dc.l scrollerpalred4
    dc.l scrollerpalred4
    dc.l scrollerpalred3
    dc.l scrollerpalred3
    dc.l scrollerpalred3
    dc.l scrollerpalred3
    dc.l scrollerpalred2
    dc.l scrollerpalred2
    dc.l scrollerpalred2
    dc.l scrollerpalred2
    dc.l scrollerpalred1
    dc.l scrollerpalred1
    dc.l scrollerpalred1
    dc.l scrollerpalred1

scrollerpalred1:
    dc.w $0611 ; 0 %0000 bg
    dc.w $0611 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0611 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0000 ; 3 inital cursor color (black)
    endif
    dc.w $0300 ; 4 scroller border left
    dc.w $0300 ; 5 scroller border left
    dc.w $0300 ; 6 scroller border left
    dc.w $0300 ; 7 scroller border left
    dc.w $0200 ; 8 scroller border right
    dc.w $0200 ; 9 scroller border right
    dc.w $0200 ; 10 scroller border right
    dc.w $0200 ; 11 scroller border right
    dc.w $0401 ; 12 scroller main color
    dc.w $0401 ; 13 scroller main color
    dc.w $0401 ; 14 scroller main color
    dc.w $0401 ; 15 scroller main color

scrollerpalred2:
    dc.w $0711 ; 0 %0000 bg
    dc.w $0711 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0711 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0000 ; 3 inital cursor color (black)
    endif
    dc.w $0400 ; 4 scroller border left
    dc.w $0400 ; 5 scroller border left
    dc.w $0400 ; 6 scroller border left
    dc.w $0400 ; 7 scroller border left
    dc.w $0300 ; 8 scroller border right
    dc.w $0300 ; 9 scroller border right
    dc.w $0300 ; 10 scroller border right
    dc.w $0300 ; 11 scroller border right
    dc.w $0401 ; 12 scroller main color
    dc.w $0401 ; 13 scroller main color
    dc.w $0401 ; 14 scroller main color
    dc.w $0401 ; 15 scroller main color

scrollerpalred3:
    dc.w $0701 ; 0 %0000 bg
    dc.w $0701 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0701 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0000 ; 3 inital cursor color (black)
    endif
    dc.w $0500 ; 4 scroller border left
    dc.w $0500 ; 5 scroller border left
    dc.w $0500 ; 6 scroller border left
    dc.w $0500 ; 7 scroller border left
    dc.w $0400 ; 8 scroller border right
    dc.w $0400 ; 9 scroller border right
    dc.w $0400 ; 10 scroller border right
    dc.w $0400 ; 11 scroller border right
    dc.w $0401 ; 12 scroller main color
    dc.w $0401 ; 13 scroller main color
    dc.w $0401 ; 14 scroller main color
    dc.w $0401 ; 15 scroller main color

scrollerpalred4:
    dc.w $0700 ; 0 %0000 bg
    dc.w $0700 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0700 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0000 ; 3 inital cursor color (black)
    endif
    dc.w $0600 ; 4 scroller border left
    dc.w $0600 ; 5 scroller border left
    dc.w $0600 ; 6 scroller border left
    dc.w $0600 ; 7 scroller border left
    dc.w $0500 ; 8 scroller border right
    dc.w $0500 ; 9 scroller border right
    dc.w $0500 ; 10 scroller border right
    dc.w $0500 ; 11 scroller border right
    dc.w $0401 ; 12 scroller main color
    dc.w $0401 ; 13 scroller main color
    dc.w $0401 ; 14 scroller main color
    dc.w $0401 ; 15 scroller main color

scrollerpalblue1:
    dc.w $0730 ; 0 %0000 bg
    dc.w $0730 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0730 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0000 ; 3 inital cursor color (black)
    endif
    dc.w $0310 ; 4 scroller border left
    dc.w $0310 ; 5 scroller border left
    dc.w $0310 ; 6 scroller border left
    dc.w $0310 ; 7 scroller border left
    dc.w $0210 ; 8 scroller border right
    dc.w $0210 ; 9 scroller border right
    dc.w $0210 ; 10 scroller border right
    dc.w $0210 ; 11 scroller border right
    dc.w $0211 ; 12 scroller main color
    dc.w $0211 ; 13 scroller main color
    dc.w $0211 ; 14 scroller main color
    dc.w $0211 ; 15 scroller main color
        
scrollerpalblue2:
    dc.w $0740 ; 0 %0000 bg
    dc.w $0740 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0740 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0000 ; 3 inital cursor color (black)
    endif
    dc.w $0420 ; 4 scroller border left
    dc.w $0420 ; 5 scroller border left
    dc.w $0420 ; 6 scroller border left
    dc.w $0420 ; 7 scroller border left
    dc.w $0320 ; 8 scroller border right
    dc.w $0320 ; 9 scroller border right
    dc.w $0320 ; 10 scroller border right
    dc.w $0320 ; 11 scroller border right
    dc.w $0322 ; 12 scroller main color
    dc.w $0322 ; 13 scroller main color
    dc.w $0322 ; 14 scroller main color
    dc.w $0322 ; 15 scroller main color
    
scrollerpalblue3:
    dc.w $0750 ; 0 %0000 bg
    dc.w $0750 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0750 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0000 ; 3 inital cursor color (black)
    endif
    dc.w $0530 ; 4 scroller border left
    dc.w $0530 ; 5 scroller border left
    dc.w $0530 ; 6 scroller border left
    dc.w $0530 ; 7 scroller border left
    dc.w $0430 ; 8 scroller border right
    dc.w $0430 ; 9 scroller border right
    dc.w $0430 ; 10 scroller border right
    dc.w $0430 ; 11 scroller border right
    dc.w $0433 ; 12 scroller main color
    dc.w $0433 ; 13 scroller main color
    dc.w $0433 ; 14 scroller main color
    dc.w $0433 ; 15 scroller main color

scrollerpalblue4:
    dc.w $0760 ; 0 %0000 bg
    dc.w $0760 ; 1 initial border color (invisible, change to 777 later) (further out)
    dc.w $0760 ; 2 initial border color (invisible, change to 777 later) (closer to the middle)
    if DEBUG
    dc.w $0700 ; 3 inital cursor color (black)
    else
    dc.w $0000 ; 3 inital cursor color (black)
    endif
    dc.w $0640 ; 4 scroller border left
    dc.w $0640 ; 5 scroller border left
    dc.w $0640 ; 6 scroller border left
    dc.w $0640 ; 7 scroller border left
    dc.w $0540 ; 8 scroller border right
    dc.w $0540 ; 9 scroller border right
    dc.w $0540 ; 10 scroller border right
    dc.w $0540 ; 11 scroller border right
    dc.w $0544 ; 12 scroller main color
    dc.w $0544 ; 13 scroller main color
    dc.w $0544 ; 14 scroller main color
    dc.w $0544 ; 15 scroller main color

scrolltext:
    include 'gen_scrolltext.s'
scrolltextsize equ *-scrolltext
    even
screen_toggle:
    dc.b 0
screen_toggle_b:
    dc.b 0
    even

scrollpos: ; pointer to the current position inside scrolltextbuffer
    dc.l scrolltextbuffer

font_addr1:
    dc.l font_shift_r
font_addr2:
    dc.l font_shift_l

screentables:
    dc.l screentable1,screentable2

spr_bgs:
    dc.l spr_bg1,spr_bg2

spr_bgs2:
    dc.l spr_bg3,spr_bg4

;play_sound:
;    dc.l 0

; dosound (XBIOS32) definition:
; $0x,<byte>: write <byte> to register x
; $80,<byte>: write <byte> to temporary register
; $81,<byte1>,<byte2>,<byte3>: <byte1> register no to write temporary value to, <byte2> increment of the temporary value, <byte3> final value for breaking the loop
; $82-$ff <byte>: wait <byte> jiffies (20ms, 1 vbi if 50Hz), if 0: exit

snd_keyclick_dosound:
    dc.b $00,$3B ; register 0 (chan 1)
    dc.b $01,$00 ; register 1 (chan 1)
    dc.b $02,$00 ; register 2 (chan 2)
    dc.b $03,$00 ; register 3 (chan 2)
    dc.b $04,$00 ; register 4 (chan 3)
    dc.b $05,$00 ; register 5 (chan 3)
    dc.b $06,$00 ; register 6 (noise)
    dc.b $07,$FE ; register 7 (chan select)
    dc.b $08,$10 ; register 8 (amplitude chan 1)
    dc.b $09,$00 ; register 9 (amplitude chan 2)
    dc.b $0a,$00 ; register 10 (amplitude chan 3)
    dc.b $0b,$80 ; register 11 (envelope)
    dc.b $0c,$01 ; register 12
    dc.b $0d,$03 ; register 13
    dc.b $ff,$00 ; finish

snd_bell_dosound:
    dc.b 0,$34   ; /* channel A pitch */
    dc.b 1,0
    dc.b 2,0     ;  /* no channel B */
    dc.b 3,0
    dc.b 4,0     ;  /* no channel C */
    dc.b 5,0
    dc.b 6,0     ;  /* no noise */
    dc.b 7,$FE   ; /* no sound or noise except channel A */
    dc.b 8,$10  ;  /* channel A amplitude */
    dc.b 9,0
    dc.b 10,0
    dc.b 11,0    ;  /* envelope */
    dc.b 12,16
    dc.b 13,9
    dc.b $ff,$00

snd_crash_dosound:
    dc.b 0,112   ; /* channel A pitch */
    ;dc.b 1,0
    ;dc.b 2,0     ;  /* no channel B */
    ;dc.b 3,0
    ;dc.b 4,0     ;  /* no channel C */
    ;dc.b 5,0
    dc.b 6,$60     ;  /* noise */
    ;dc.b 7,$FE   ; /* no sound or noise except channel A */
    dc.b 8,$10  ;  /* channel A amplitude */
    ;dc.b 9,0
    ;dc.b 10,0
    dc.b 11,6    ;  /* envelope */
    dc.b 12,0
    dc.b 13,8
    dc.b $ff,$00

    include 'sound.s'

scrolleraddrtables:
    dc.l scrolleraddrtable1,scrolleraddrtable2

scrolleraddrtable1: ; contains: screen address, font address 1 / 2, offset 1 / 2
    dc.l scrollscraddr1 ; address where the screen address is stored (beginning of scroller)
    dc.l font ; font1
    dc.l font ; font2
    dc.w 0,0 ; offset of the scroll character (here: use the same character and the same font)
    dc.w 2 ; value to add to the scrollerpos

scrolleraddrtable2:
    dc.l scrollscraddr2
    dc.l font_shift_r
    dc.l font_shift_l
    dc.w 0,-2 ; offset of the scroll characters (here: use shift_r with the current character and shift_l with the previous character, those are ORed)
    dc.w 0

logo_data:
    include 'gen_logo.s'

    bss
current_scrollerpal_sequence_struct:
    ds.w 1 ; counter
    ds.l 1 ; address of the palettetable
    ds.l 1 ; address of the next entry in the sequence

current_pal_sequence_struct:
    ds.w 1 ; counter
    ds.l 1 ; address of the palette
    ds.l 1 ; address of the next entry in the sequence

current_snd_sequence_struct:
    ds.w 1 ; counter
    ds.l 1 ; address of the sounddata
    ds.l 1 ; address of the next entry in the sequence

current_dosound_sequence_struct:
    ds.w 1 ; counter
    ds.l 1 ; address of the current entry in dosound
    ds.b 1 ; temp value
    ds.b 1 ; filler
    ds.l 1 ; address of next entry in dosound (after delay!)

current_sprite_sequence_struct:
    ds.w 1 ; counter
    ds.l 1 ; address of animated sprite definition
    ds.l 1 ; address of next entry in sequence

current_sprite_sequence_struct2:
    ds.w 1 ; counter
    ds.l 1 ; address of animated sprite definition
    ds.l 1 ; address of next entry in sequence

current_ani_sprite_struct: ; holds data of the currently displayed animated sprite
    ; this struct needs to contain:
    ; - 0w: counter which counts to (including) 0 (delay value)
    ; - 2l: pointer to the sprite data (base address)
    ; - 6w: offset to the correct shift (sprite_size_per_shift(384) bytes * shift (x % 16))
    ; - 8w: offset to the screen address (230 * y coordinate + x offset (x // 16 * 8))
    ; - 10l: pointer to the *next* position in the animated sprite definition (f.e. ani_spr_cursor)
    ds.w 1 ; counter
    ds.l 1 ; base sprite data address
    ds.w 1 ; shift offset
    ds.w 1 ; screen address offset
    ds.l 1 ; next position in the definition

current_ani_sprite_struct2: ; holds data of the currently displayed animated sprite
    ; this struct needs to contain:
    ; - 0w: counter which counts to (including) 0 (delay value)
    ; - 2l: pointer to the sprite data (base address)
    ; - 6w: offset to the correct shift (sprite_size_per_shift(384) bytes * shift (x % 16))
    ; - 8w: offset to the screen address (230 * y coordinate + x offset (x // 16 * 8))
    ; - 10l: pointer to the *next* position in the animated sprite definition (f.e. ani_spr_cursor)
    ds.w 1 ; counter
    ds.l 1 ; base sprite data address
    ds.w 1 ; shift offset
    ds.w 1 ; screen address offset
    ds.l 1 ; next position in the definition


fontoffset1:
    ds.w 1
fontoffset2:
    ds.w 1
prev_scrolltextentry:
    ds.w 1 ; when looking back the previous entry...
scrolltextbuffer:
    ds.w 4*scrolltextsize+1 ; 4 entries per character, last one is -1 to indicate the end

; mouse vector
mouse_vec:
    ds.l 1

; log screen address
logbase:
    ds.l 1

; old resolution
res:
    ds.w 1

; old palette
pal:
    ds.w 16

spr_cursor:
    ds.l 6*16*16 ; 6 lw (2 mask+4 planes) * 16 lines * 16 shifts

spr_empty:
    ds.l 6*16*16 ; 6 lw (2 mask+4 planes) * 16 lines * 16 shifts

spr_butterfly_0:
    ds.l 6*16*16 ; 6 lw (2 mask+4 planes) * 16 lines * 16 shifts

spr_butterfly_1:
    ds.l 6*16*16 ; 6 lw (2 mask+4 planes) * 16 lines * 16 shifts

spr_qm1:
    ds.l 6*16*16 ; 6 lw (2 mask+4 planes) * 16 lines * 16 shifts

spr_qm3:
    ds.l 6*16*16 ; 6 lw (2 mask+4 planes) * 16 lines * 16 shifts

spr_bg1:
    ds.l 1+4*16 ; start address + 4 planes * 16 lines
spr_bg2:
    ds.l 1+4*16 ; start address + 4 planes * 16 lines
spr_bg3:
    ds.l 1+4*16 ; start address + 4 planes * 16 lines
spr_bg4:
    ds.l 1+4*16 ; start address + 4 planes * 16 lines

fontcharactersize equ 256 ; the char in the font (which is only part of the full character...) takes up that many bytes: 2 words(planes) * 64 lines = 128 words = 256 bytes
font:
    ; 64x64, i.e. 2 planes * 2 lw * 64 per character, 32 characters
    ; ordering is 1st word = 1st line 1st plane left, 2nd word is 1st line 2nd plane left
    ;  3rd word is 2nd line 1st plane left, 4th word is 2nd line 2nd plane left
    ; ...
    ; all of that x3 because we need three copies of the font:
    ; 1. normal: word1: (L1)(R1) word2: (L2)(R2) where Lx and Rx are bytes of the left half and the right half of the char in plane x
    ; 2. shifted to the right (zeroed out): word1: 00(L1) word2: 00(L2)
    ; 3. shifted to the left  (zeroed out): word1: (R1)00 word2: (R2)00
    ;  
    ds.l 2*2*64*32 ;
font_shift_r:
    ds.l 2*2*64*32
font_shift_l:
    ds.l 2*2*64*32

; the new screen address - theoretical resolution in pixels: (52 + 320 + 92) x (27 + 200 + bot_lines)
; visible area starts left at pixel number 6, and ends at pixel number 415, so it is 410 pixels wide, so typically 410 x 259 (not counting the first crippled line)
scrn:
    ds.b 256 ; byte boundary (word boundary (i.e. bit 0 = 0) in the msb!)
s:
    ds.b 28*230 ; top border area. actually, the first scanline is 160 though...
    ds.b 200*230 ; main screen
    ds.b 48*230 ; bottom border, theoretically up to 48 lines, 28 are quite safe to use
    ; functioning for fullscreen:
    ;ds.b 28*230 ; top border area. actually, the first scanline is 160 though...
    ;ds.b 200*230
    ;ds.b 32*230
    ;ds.b 32*160 ; top border area
    ;ds.b 32000 ; main screen
    ;ds.b 32*160 ; bottom border area
; total screen length in bytes
screen_len equ *-s

; the new screen address 2
scrn2:
    ds.b 256 ; byte boundary (word boundary (i.e. bit 0 = 0) in the msb!)
s2:
    ds.b 28*230 ; top border area. actually, the first scanline is 160 though...
    ds.b 200*230 ; main screen
    ds.b 48*230 ; bottom border, theoretically up to 48 lines, 28 are quite safe to use

; screen address (not really, we add 160 bytes for the first line already, because afterwards every line has 230 bytes)
screen:
    ds.l 1
screens:
screen1:
    ds.l 1
screen2:
    ds.l 1

;screenoffsettable:
;    ds.w 28+200+bot_lines

screentable1:
    ds.l 28+200+bot_lines ; address of every line in the screen, avoids repeated *230
screentable2:
    ds.l 28+200+bot_lines

hw_screen: ; screen address in format to slap into hw register with movep on the next sync
    ds.w 1
hw_screens:
    ds.w 1 ; filler
hw_screen1: ; screen 1 address in format to slap into hw register with movep
    ds.w 1
    ds.w 1 ; filler
hw_screen2: ; screen 2 address in format to slap into hw register with movep
    ds.w 1

;spr_position_addr:
;    ds.l 1
scrollscraddr:
    ds.l 1
scrollscraddrs:
scrollscraddr1:
    ds.l 1
scrollscraddr2:
    ds.l 1