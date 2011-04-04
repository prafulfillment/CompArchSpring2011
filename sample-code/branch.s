ori $r2, $r0, 17
ori $r3, $r0, 9
ori $r4, $r0, 1
slt $r1, $r2, $r3
bne $r0, $r1, -1
ori $r4, $r0, 0
beq $r0, $r4, 2
ori $r5, $r0, 1
j 0x101c
ori $r5, $r0, 2

