ori $r2, $r0, 1      
ori $r9, $r0, 0x1024   
j 0x1014
ori $r2, $r0, 0xbeef0
ori $r9, $r0, 0x1000
ori $r3, $r0, 2
jr $r9
ori $r9, $r0, 0x1000
ori $r2, $r0, 0xdead0
add $r3, $r2, $r3
