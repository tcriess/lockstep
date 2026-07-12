music:

	; Z ==

	dc.b $7,$1c       ; MX T+T+N

;	dc.b $8,$0        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$0        ; VC

	; ====

	; A 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; A 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; A 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; A 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; A 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; A 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; B 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; B 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; B 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; B 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; B 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; B 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; B 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; B 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; B 08

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; B 09

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; B 0A

	dc.b $1,$1,$0,$92 ; TA D#4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; B 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; B 0C

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; B 0D

	dc.b $1,$1,$0,$92 ; TA D#4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; B 0E

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; B 0F

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; I 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; I 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $6,$A        ; NS
	dc.b $8,$C        ; VA
	dc.b $6,$A        ; NS
	dc.b $A,$A        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $6,$8        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $6,$4        ; NS
	dc.b $A,$D        ; VC
	dc.b $ff,1        ; DL 2

	; I 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $6,$3        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $6,$2        ; NS
	dc.b $A,$F        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $6,$3        ; NS
	dc.b $A,$F        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $6,$4        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2

	; I 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$D        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $6,$7        ; NS
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $6,$8        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $6,$A        ; NS
	dc.b $A,$A        ; VC
	dc.b $ff,1        ; DL 2

	; I 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $6,$C        ; NS
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $6,$E        ; NS
	dc.b $A,$8        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $6,$10       ; NS
	dc.b $A,$7        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $6,$12       ; NS
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; I 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; I 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; I 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; I 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; I 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; I 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; I 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; I 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; I 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; I 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; I 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; A 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; A 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; A 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; A 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; A 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; A 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; C 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; C 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; C 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; C 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; C 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; C 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; C 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; C 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $3,$8,$2,$e1 ; TB A-1
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; C 08

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS 6
	dc.b $A,$5        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; C 09

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $3,$8,$2,$e1 ; TB A-1
	dc.b $9,$C        ; VB
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; C 0A

	dc.b $1,$1,$0,$92 ; TA D#4
	dc.b $8,$E        ; VA
	dc.b $3,$8,$2,$e1 ; TB A-1
	dc.b $9,$E        ; VB
	dc.b $A,$7        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; C 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $A,$8        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; C 0C

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $3,$7,$2,$77 ; TB C-2
	dc.b $9,$E        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; C 0D

	dc.b $1,$1,$0,$92 ; TA D#4
	dc.b $8,$C        ; VA
	dc.b $A,$A        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; C 0E

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $3,$7,$2,$77 ; TB C-2
	dc.b $9,$E        ; VB
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; C 0F

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $A,$A        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; D 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; D 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; D 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; D 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $3,$7,$2,$77 ; TB C-2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; D 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; D 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; D 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; D 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $3,$7,$2,$77 ; TB C-2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; D 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; D 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; D 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; D 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $3,$7,$2,$77 ; TB C-2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; E 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; E 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; E 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; E 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; E 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; E 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; E 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; E 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; E 08

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; E 09

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; E 0A

	dc.b $1,$1,$0,$92 ; TA D#4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; E 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; E 0C

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $3,$6,$2,$47 ; TB D#2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; E 0D

	dc.b $1,$1,$0,$92 ; TA D#4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; E 0E

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $3,$6,$2,$47 ; TB D#2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; E 0F

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; D 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; D 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; D 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; D 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $3,$7,$2,$77 ; TB C-2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; D 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; D 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; D 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; D 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $3,$7,$2,$77 ; TB C-2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; D 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; D 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; D 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; D 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; D 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; D 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $3,$7,$2,$77 ; TB C-2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; D 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; E 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; E 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; E 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; E 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; E 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; E 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; E 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; E 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; E 08

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; E 09

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; E 0A

	dc.b $1,$1,$0,$92 ; TA D#4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; E 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; E 0C

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $3,$6,$2,$47 ; TB D#2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; E 0D

	dc.b $1,$1,$0,$92 ; TA D#4
	dc.b $8,$E        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,3        ; DL 4

	; E 0E

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $3,$6,$2,$47 ; TB D#2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2

	; E 0F

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,3        ; DL 4

	; ====

	; ====

	; F 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$B        ; VB
	dc.b $6,$A        ; NS
	dc.b $A,$A        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $6,$9        ; NS
	dc.b $A,$A        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $6,$8        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2

	; F 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $6,$4        ; NS
	dc.b $A,$D        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $6,$3        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $6,$2        ; NS
	dc.b $A,$F        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $6,$3        ; NS
	dc.b $ff,1        ; DL 2

	; F 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$4        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $6,$6        ; NS
	dc.b $A,$D        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $6,$7        ; NS
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $6,$8        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2

	; F 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $6,$A        ; NS
	dc.b $A,$A        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $6,$C        ; NS
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $6,$E        ; NS
	dc.b $A,$8        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $6,$10       ; NS
	dc.b $A,$7        ; VC
	dc.b $ff,1        ; DL 2

	; F 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $6,$12       ; NS
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; F 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; F 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; F 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; F 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; F 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; F 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; F 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; F 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; F 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; F 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $3,$7,$2,$77 ; TB C-2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; F 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; ====

	; G 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$B        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; G 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $3,$7,$2,$77 ; TB C-2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; ====
	
	; G 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$B        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; G 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $3,$7,$2,$77 ; TB C-2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; ====

	; H 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$B        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; H 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; H 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; H 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; H 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 08

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 09

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; H 0A

	dc.b $1,$1,$0,$92 ; TA D#4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 0C

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $3,$6,$2,$47 ; TB D#2
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 0D

	dc.b $1,$1,$0,$92 ; TA D#4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; H 0E

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $3,$6,$2,$47 ; TB D#2
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 0F

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; ====
	
	; G 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$B        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; G 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $3,$7,$2,$77 ; TB C-2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; ====
	
	; G 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$B        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; G 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $3,$7,$2,$77 ; TB C-2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; ====
	
	; G 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$B        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; G 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 08

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 09

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 0A

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0C

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0D

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; G 0E

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $3,$7,$2,$77 ; TB C-2
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; G 0F

	dc.b $1,$1,$0,$de ; TA C-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; ====

	; H 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$B        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$2        ; VA
	dc.b $ff,1        ; DL 2

	; H 01

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; H 02

	dc.b $1,$0,$0,$d5 ; TA D-5
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 03

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; H 04

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 05

	dc.b $1,$0,$0,$ef ; TA C-5
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 06

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; H 07

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 08

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 09

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; H 0A

	dc.b $1,$1,$0,$92 ; TA D#4
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 0B

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 0C

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $3,$6,$2,$47 ; TB D#2
	dc.b $8,$E        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 0D

	dc.b $1,$1,$0,$92 ; TA D#4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $A,$0        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; H 0E

	dc.b $1,$1,$0,$0c ; TA A#4
	dc.b $3,$6,$2,$47 ; TB D#2
	dc.b $8,$E        ; VA
	dc.b $9,$E        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$A        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$6        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $9,$0        ; VB
	dc.b $ff,1        ; DL 2

	; H 0F

	dc.b $1,$1,$0,$1c ; TA A-4
	dc.b $8,$C        ; VA
	dc.b $9,$C        ; VB
	dc.b $ff,1        ; DL 2
	dc.b $8,$8        ; VA
	dc.b $ff,1        ; DL 2
	dc.b $8,$4        ; VA
	dc.b $9,$0        ; VB
	dc.b $ff,3        ; DL 4

	; ====

	; J 00

	dc.b $1,$1,$0,$aa ; TA D-4
	dc.b $3,$6,$2,$a7 ; TB D-2
	dc.b $8,$C        ; VA
	dc.b $9,$B        ; VB
	dc.b $6,$A        ; NS
	dc.b $A,$A        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $6,$8        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$B        ; VA
	dc.b $9,$A        ; VB
	dc.b $6,$6        ; NS
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $6,$4        ; NS
	dc.b $A,$D        ; VC
	dc.b $ff,1        ; DL 2

	; J 01

	dc.b $8,$A        ; VA
	dc.b $9,$9        ; VB
	dc.b $6,$3        ; NS
	dc.b $A,$E        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $6,$6        ; NS
	dc.b $A,$D        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$9        ; VA
	dc.b $9,$8        ; VB
	dc.b $6,$7        ; NS
	dc.b $A,$C        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $6,$8        ; NS
	dc.b $A,$B        ; VC
	dc.b $ff,1        ; DL 2

	; J 02

	dc.b $8,$8        ; VA
	dc.b $9,$7        ; VB
	dc.b $6,$A        ; NS
	dc.b $A,$A        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $6,$C        ; NS
	dc.b $A,$9        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$7        ; VA
	dc.b $9,$6        ; VB
	dc.b $6,$E        ; NS
	dc.b $A,$8        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $6,$10       ; NS
	dc.b $A,$7        ; VC
	dc.b $ff,1        ; DL 2

	; J 03

	dc.b $8,$6        ; VA
	dc.b $9,$5        ; VB
	dc.b $6,$12       ; NS
	dc.b $A,$6        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $6,$13       ; NS
	dc.b $A,$5        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $8,$5        ; VA
	dc.b $9,$4        ; VB
	dc.b $6,$14       ; NS
	dc.b $A,$4        ; VC
	dc.b $ff,1        ; DL 2
	dc.b $6,$15       ; NS
	dc.b $A,$3        ; VC
	dc.b $ff,1        ; DL 2

	; J 04-0F

	dc.b $8,$0        ; VA
	dc.b $9,$0        ; VB
	dc.b $A,$0        ; VC
	dc.b $ff,95       ; DL 96

	; ====

	; END

	dc.b $8,$0        ; VA
	dc.b $9,$0        ; VA
	dc.b $A,$0        ; VA

	dc.b $ff,0

