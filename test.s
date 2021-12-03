.text
.globl main

main:
0:    addi $t0, $zero, 1
1:    srbr0
2:    lw2 $t0, 5[$t4]
3:    test
4:    addi $t0, $zero, 1
5:    inc $t0
6:    abs $t0, $t0 # takes 3 slots
9:    inci $t0, 4