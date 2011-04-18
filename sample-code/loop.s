ori $r7, $r0, 5		#0x1000
ori $r2, $r0, 0		#0x1004
ori $r3, $r0, 0		#0x1008
ori $r4, $r0, 0		#0x100c
ori $r5, $r0, 1		#0x1010

addi $r2, $r2, 1	#0x1014
or $r3, $r4, $r0
or $r4, $r5, $r0
add $r5, $r4, $r3
slt $r6, $r2, $r7
bne $r6, $r0, -6
ori $r10, $r0, 1

