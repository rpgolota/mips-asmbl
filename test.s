.text
.globl main

main:
    addi $t0, $zero, 1
    srbr0
    lw2 $t0, 5[$t4]
    test
    addi $t0, $zero, 1
    inc $t0
    inci $t0, 4