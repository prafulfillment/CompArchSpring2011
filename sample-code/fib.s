ori $r1, $r0, 10    # counter = 10          0x1000

ori $r2, $r0, 1     # n1                    0x1004
ori $r3, $r0, 1     # n2                    0x1008

add $r4, $r2, $r3   # t = n1 + n2           0x100C
add $r2, $r3, $r0   # n1 = n2               0x1010
add $r3, $r4, $r0   # n2 = t                0x1014
subi $r1, $r1, 1    # counter -= 1          0x1018
bne $r1, $r0, -5    #                       0x101C
