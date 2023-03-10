# two-pass-assembly
python을 이용해 ARM 명령어를 기계어로 변환하는 코드 작성

# 구현 내용
- Basic Level
1. immediate value 구현
2. shift immediate value 구현
3. shift Register 구현
4. OPCODE 6개 이상 + COND 7개 이상 구현
5. SWI 구현
6. MUL 구현

- Advanced Level
1. Symbol Talbe 구현
2. B 구현
3. LDR/STR/LDRB/STRB 구현

- Challenging Level
1. pseudo instruction 구현

# 실행방법
test.s 파일에는 ARM 명령어를 입력하고

"""
$python two_pass_assembly.py < test.s
"""
