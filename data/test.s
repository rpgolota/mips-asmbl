.data
d0: .word 3

.text
.globl main

main:
l0:    addi $t0, $zero, 1
l1:    srbr0
l2:    lw2 $t0, 5[$t4]
l3:    test
l4:    addi $t0, $zero, 1
l5:    inc $t0
l6:    abs $t0, $t0 # takes 3 slots
l9:    inci $t0, %9 * 2%