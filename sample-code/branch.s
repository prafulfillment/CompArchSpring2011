ori $r2, $r0, 17	#0x1000
ori $r3, $r0, 9		#0x1004
ori $r4, $r0, 1		#0x1008
slt $r1, $r2, $r3	#0x100C
bne $r0, $r1, -1	#0x1010
ori $r4, $r0, 0		#0x1014
beq $r0, $r4, 2		#0x1018
ori $r5, $r0, 1		#0x101C
j 0x101c			#0x1020
ori $r5, $r0, 2		#0x1024

#sup