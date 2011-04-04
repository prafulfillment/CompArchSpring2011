ori $r7, $r0, 100
ori $r2, $r0, 5
ori $r3, $r0, 7
sw $r2, 0($r7)
sw $r3, 4($r7)
add $r2, $r7, $r7
add $r3, $r7, $r7
lw $r2, 0($r7)
lw $r3, 4($r7)
add $r5, $r2, $r3
