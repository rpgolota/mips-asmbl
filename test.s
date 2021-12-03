.text
.globl main

main:
    addi $t0, $zero, 1
    srbr0
    lw2 $t0, 5[$t4]
    test