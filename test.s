.text
_start: .global _start
    mov r1, #296
    moveqs r1, #636
    movle r1, #144
    mov r1, #4227858435
    moveq r1, #805306371
    mov r1, #3758096389

c:.word 5
    addeq r1, r2
    sub r1, r2, #-4
    add r1, r2, r3, lsl #4
    add r1, r2, r3, lsl r4

loop :
    swi 0
    mul r1, r2

loop2:mla r1, r2, r3, r4
    mul r1, r3, r4
    bl loop2
    b loop
    ldr r1, =msg2
    ldr r1, =1234
    ldr r3, =1234
    ldr r1, =-123
    ldr r1, =msg
    ldr r1, =d
    ldr r1, =a

d: .word 34, 12
    adr r5, msg2
    ldr r1, [r2]!
    str r1, [r3 ] !
    ldreq r0, [ r1, #12]
    ldrleb r2, [r3, r4 ]

msg2 :
    .asciz "abc"
    str r5, [r6, r7, lsl #2]
    ldr r0, [r1, #-12 ] !
    ldreq r0, [ r1 ], #12
    ldrleb r2, [ r3], r4
    ldrb r2, [r3 ], #-4
    ldr r3, =msg2
    str r5, [ r6 ], r7, ror #2
.data
msg: .asciz "Hello, world!\n"
a: .word 4, 4, 2 
b: .word 1