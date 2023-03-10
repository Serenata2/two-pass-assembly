import sys
import string
import re
import struct

cond = {'eq': 0, 'ne': 1, 'hs': 2, 'cs': 2, 'lo': 3,
        'cc': 3, 'mi': 4, 'pl': 5, 'vs': 6, 'vc': 7,
        'hi': 8, 'ls': 9, 'ge': 10, 'lt': 11, 'gt': 12,
        'le': 13, 'al': 14, 'nv': 15}

registers = {'r0': 0, 'r1': 1, 'r2': 2, 'r3': 3, 'r4': 4,
             'r5': 5, 'r6': 6, 'r7': 7, 'r8': 8, 'r9': 9,
             'r10': 10, 'r11': 11, 'r12': 12, 'r13': 13,
             'r14': 14, 'r15': 15, 'sl': 10, 'fp': 11,
             'ip': 12, 'sp': 13, 'lr': 14, 'pc': 15}

opcode = {'sub': 0b0010, 'add': 0b0100, 'mov': 0b1101, 'mvn': 0b1111, 'and': 0b0000, 'bic': 0b1110}            
trans_opcode = {'add' : 'sub', 'sub' : 'add', 'mov' : 'mvn', 'mvn' : 'mov',
                'bic' : 'and', 'and' : 'bic'}
sh = {'lsl' : 0b00, 'lsr' : 0b01, 'asr' : 0b10, 'ror' : 0b11}

mul_opcode = {'mul': 0b0, 'mla': 0b1}

literl_pool = []             # 리터럴 풀

def is_digit(str):          # 문자열이 숫자인지 아닌지 판단하는 함수
   try:
     tmp = float(str)
     return True
   except ValueError:
    return False

def make_regexp(li):
    res = '('
    for elem in li:
        res += elem + '|'
    res = res.rstrip('|')
    res += ')'
    return res

cond_regexp = make_regexp(cond.keys())

def process_cond_field(mach_code, tok):             # condition field 확인 -> eq, le, ...
    cond_field = tok[:2]                            # 2개까지 가져온다 ex) moveqs -> eq만 
    if cond_field in cond:
        mach_code |= cond[cond_field] << 28         # "|=" 는 or 연산자
        tok = tok[2:]
#        print('\tCOND is set to ' + str(cond[cond_field]))
        #print('\tCOND is set to ' + str(bin(cond[cond_field])))
    else: # if cond is undefined
        mach_code |= 14 << 28                       # 1110(always)로 condition field 채움
        #print('\tCOND is undefined')
    return (mach_code, tok)                         # mach_code, tok 업데이트

def process_S_flag(mach_code, tok):
    if tok == 's':
        #print('\tS flag is set')
        mach_code |= 1 << 20                        # S 부분 업데이트
        tok = tok[1:]
    return (mach_code, tok)                         # mach_code, tok 업데이트

def process_cond_field(mach_code, tok):             # condition field 확인 -> eq, le, ...
    cond_field = tok[:2]                            # 2개까지 가져온다 ex) moveqs -> eq만 
    if cond_field in cond:
        mach_code |= cond[cond_field] << 28         # "|=" 는 or 연산자
        tok = tok[2:]

    else:                                           # if cond is undefined
        mach_code |= 14 << 28                       # 1110(always)로 condition field 채움
    return (mach_code, tok)                         # mach_code, tok 업데이트

def process_S_flag(mach_code, tok):
    if tok == 's':
        mach_code |= 1 << 20                        # S 부분 업데이트
        tok = tok[1:]
    return (mach_code, tok)                         # mach_code, tok 업데이트

def check_imm_value(imm_value):
    if(imm_value > 255):
        mach_imm = 0
        bin_s = str(bin(imm_value))[1:]         # ex) imm_value = 4(0b100) -> bin_s = 'b100'
        second_one_index = 1

        for i in range(len(bin_s)-1, 1, -1):    # 역순
            if bin_s[i] == '1':
                second_one_index = i
                break

        num_zero = len(bin_s) - second_one_index - 1

        if second_one_index > 8 :                   # 1 과 1 사이가 8초과인 경우
            for i in range(32 - len(bin_s) + 1):    # 앞에 0 채워 놓기
                bin_s = bin_s[:1] + '0' + bin_s[1:]
            
            i_len = j_len = 16
            for i in range(16, 0, -1):      # 16번째 ~ 1번째 탐색하면서
                if bin_s[i] == '1':         # i_len 구하기
                    i_len = i
                    break
            
            for j in range(17, 33):         # 17번째 ~ 32 번째 탐색하면서
                if bin_s[j] == '1':         # j_len 구하기
                    j_len = 33 - j
                    break
            
            if (i_len + j_len) > 8 or ((i_len + j_len) == 8 and i_len % 2 == 1):
                return imm_value, False                    # imm_value로 표현 x

            else:
                if i_len % 2 == 0:          # i_len이 짝수
                    mach_imm |= int(('0' + bin_s[33 -j_len:]), 2) << i_len
                    mach_imm |= int(('0' + bin_s[1:i_len+1]), 2)
                    mach_imm |= (int(i_len/2)) << 8

                else:                       # i_len이 홀수이므로 '0'하나 더 붙인 것 rotate
                    mach_imm |= int(('0' + bin_s[33- j_len:]), 2) << (i_len + 1)
                    mach_imm |= int(('0' + bin_s[1:i_len+2]), 2)
                    mach_imm |= (int(i_len / 2) + 1) << 8

        # 길이가 8이 아니거나 8이면 뒤에 0의 개수가 짝수개 이면
        elif second_one_index != 8 or num_zero % 2 == 0:    
            if num_zero % 2 == 0:       # 마지막 '1' 뒤에 '0'의 개수가 짝수개 이면
                mach_imm |= int(('0' + bin_s[:second_one_index +1 ]), 2)
            else:                                               
                mach_imm |= int(('0' + bin_s[:second_one_index + 2]), 2)
                num_zero -= 1

            mach_imm |= (16 - int(num_zero/2)) << 8    
        
        else:
            return imm_value, False                    # im_value로 표현 x

        return mach_imm, True

    else:
        return imm_value, True

# 1. len(args) == 3 ex) mov r1, r2, add r1, r2
# 2. len(args) == 5 ex) add r1, r1, r2
# 3. len(args) == 6 ex) mov r0, r1, lsl #2
# 4. len(args) == 8 ex) add r1, r2, r2, lsl #3
def process_2_args(mach_code, args, op):                
    # match_reg is list of matching register
    if args[0] in registers:
        mach_code |= registers[args[0]] << 12       # Rd 업데이트
    else: # destination must be register            # 아니면 잘못 쓴거임!
        print('ERROR: Invalid operand')
        sys.exit(1)

    for i in range(len(args)):                      # 콤마가 올바른 자리에 없다면 
        if (i % 2 == 1) and args[i] != ',':         # 에러!!
            if i < 4:
                print("ERROR: Invalid operand -> " + str(i))
                sys.exit(1)
        
    if len(args) == 3:                      # ex) mov r1, r2, add r1, r2                        
        if op != 'mov' and op != 'mvn':             
            mach_code |= registers[args[0]] << 16  # Rn 업데이트

        if args[2] in registers:
            mach_code |= opcode[op] << 21           # opcode 업데이트
            mach_code |= registers[args[2]]         # operand 업데이트

        elif (args[2][0] == '#') and (is_digit(args[2][1:])):                        

            mach_code |= 1 << 25                    # I 업데이트

            imm_value = int(args[2][1:])            
            if imm_value >= 0:
                mach_code |= opcode[op] << 21       # opcode 업데이트

            else:                                   # imm_value가 음수
                if op in trans_opcode:              # 명령어를 반대로 바꿀 수 있으면 바꾼다.
                    mach_code |= opcode[trans_opcode[op]] << 21
                else:
                    mach_code |= opcode[op] << 21
                
                if op == 'mov' or op == 'mvn' or op == 'and' or op == 'bic':
                    imm_value += 1                  # 2의 보수 취하기
                imm_value = -imm_value

            imm_value, flag = check_imm_value(imm_value)
            if flag == False:                       # 12bit로 표현 x
                print("ERROR: IMM_VALUE")
            mach_code |= imm_value
        else:
            print("ERROR: Invalid operand")
            sys.exit(1)
        
    elif len(args) == 5:                   # ex) add r1, r1, r2                 
        if args[2] in registers:
            mach_code |= registers[args[2]] << 16   # Rn 업데이트, 어처피 레지스터밖에 올 수 없기에
            if args[4] in registers:
                mach_code |= opcode[op] << 21       # opcode 업데이트
                mach_code |= registers[args[4]]     # operand2 업데이트

            elif (args[4][0] == '#') and (is_digit(args[4][1:])):
                mach_code |= 1 << 25                # I 업데이트
                imm_value = int(args[4][1:])
                if imm_value >= 0:
                    mach_code |= opcode[op] << 21   # opcode 업데이트
                else:                               # imm_value가 음수
                    if op in trans_opcode:          # 명령어를 반대로 바꿀 수 있으면 바꾼다.    
                        mach_code |= opcode[trans_opcode[op]] << 21
                    else:
                        mach_code |= opcode[op] << 21
            
                    if op == 'mov' or op == 'mvn' or op == 'and' or op == 'bic':
                        imm_value += 1              # 2의 보수 취하기
                    imm_value = -imm_value          
     
                    imm_value, flag = check_imm_value(imm_value)
                    if flag == False:               # 12bit로 표현 x
                        print("ERROR: IMM_VALUE")
                mach_code |= imm_value
            else:
                print("ERROR: Invalid operand")
                sys.exit(1)
        else:
            print("ERROR: Invalid operand")
            sys.exit(1)
    
    elif len(args) == 6:                # ex) mov r0, r1, lsl #2          
        if (args[2] in registers) and (args[4] in sh):
            if(op != 'mov' and op != 'mvn'):
                mach_code |= registers[args[0]] << 16   # Rn 업데이트
            mach_code |= opcode[op] << 21       # opcode 업데이트
            mach_code |= registers[args[2]]     # operand2 Rm 업데이트
            mach_code |= sh[args[4]] << 5

            if args[5] in registers:
                mach_code |= 1 << 4                     # 4번 비트 업데이트
                mach_code |= registers[args[5]] << 8    # Rs 업데이트
            elif (args[5][0] == '#') and (is_digit(args[5][1:])):
                imm_value = int(args[5][1:])            # 7~11비트 업데이트
                if imm_value >= 0:
                    mach_code |= imm_value << 7
                else:
                    print("ERROR")
                    sys.exit(1)
            else:
                print("ERROR")
                sys.exit(1)

        else:
            print("ERROR: @Invalid operand")
            sys.exit(1)

    elif len(args) == 8:            # ex) add r1, r2, r2, lsl #3
        if (args[2] in registers) and (args[6] in sh):
            mach_code |= opcode[op] << 21           # opcode 업데이트
            mach_code |= registers[args[2]] << 16   # Rn 업데이트

            if args[4] in registers:                # operand가 레지스터인 경우
                mach_code |= registers[args[4]]     # operand2 Rm 업데이트
                mach_code |= sh[args[6]] << 5

                if args[7] in registers:
                    mach_code |= 1<< 4                      # 4번 비트 업데이트
                    mach_code |= registers[args[7]] << 8    # Rs 업데이트
                
                elif (args[7][0] == '#') and (is_digit(args[7][1:])):
                    imm_value = int(args[7][1:])
                    if imm_value >= 0:
                        mach_code |= imm_value << 7         # 7~11비트 업데이트
                else:
                    print("ERROR")
                    sys.exit(1)
            else:
                print("ERROR")
                sys.exit(1)
        
        else:
            print("ERROR: Invalid operand")
            sys.exit(1)

    return mach_code

def process_mul_args(mach_code, args):
    for i in range(len(args)):
        if (i % 2 == 1) and args[i] != ',':         # 콤마가 올바른 자리에 없다면 
            if i < 6:                               # 에러
                print("ERROR: Invalid operand -> " + str(i))
                sys.exit(1)
        elif (args[i] =='pc') and (not args[i] in registers):
            print("ERROR: Invalid operand -> " + str(i))
            sys.exit(1)                             # pc 레지스터를 쓴다면 에러

    if args[0] == args[1]:
        print("ERROR: Invalid operand")             # Rd와 Rn이 같으면 에러
        sys.exit(1)
    
    mach_code |= registers[args[0]] << 16       # Rd 업데이트
    mach_code |= 0b1001 << 4                    # 4~7비트 업데이트

    # mul r1, r2 -> mul r1, r2, r1
    if len(args) == 3:
        mach_code |= registers[args[2]]         # Rm 업데이트
        mach_code |= registers[args[0]] << 8    # Rs 업데이트

    # mul r1, r2, r3
    elif len(args) == 5:
        mach_code |= registers[args[2]]         # Rm 업데이트
        mach_code |= registers[args[4]] << 8    # Rs 업데이트

    # mla r1, r2, r3, r4
    elif len(args) == 7:
        mach_code |= registers[args[6]] << 12   # Rn 업데이트
        mach_code |= registers[args[2]]         # Rm 업데이트
        mach_code |= registers[args[4]] << 8    # Rs 업데이트

    return mach_code


def process_instruction(tokens, addr):            # 명령어를 기계어로 변환 하는 함수
    mach_code = 0                           # ex) tokens = ["mov", "r1", "," "#2"]
    tok = tokens[0]                         
    args = tokens[1:]

    # adr family
    if tok[:3] == 'adr':                        
        adr_re = 'adr' + cond_regexp + '?'      
        
        if re.match(adr_re, tok):               # offset 값에 따라 add, sub로 바꿈          
            temp_addr = symbol_table[args[2]][1] - (addr + 8)
            if temp_addr >= 0:                  # add로 바꾼다
                tok = 'add' + tok[3:]
                args = args[:2] + ['pc', ',', ('#'+str(temp_addr))]
            else:
                tok = 'sub' + tok[3:]           # sub로 바꾼다
                temp_addr = -temp_addr
                args = args[:2] + ['pc', ',', ('#'+str(temp_addr))]

        else:
            print("ERROR worng instruction")
            sys.exit(1)

    # ldr/str family
    elif tok[:3] == 'ldr' or tok[:3] == 'str':
        ldr_re = '(ldr|str)' + 'b' + '?' + cond_regexp + '?'
        flag = False
        if re.match(ldr_re, tok):
            if args[2].startswith('='):         # ldr r1, =format
                if is_digit(args[2][1:]) and tok[:3] == 'ldr':     # ldr r1, =constant 형태
                    temp_value = imm_value = int(tokens[3][1:])
                    if imm_value < 0:
                        imm_value += 1          # 음수의 경우 2의 보수를 취한다.
                        imm_value = -imm_value

                    imm_value, flag = check_imm_value(imm_value)
                    if flag == False:           # 12bit로 표현할 수 없다면
                        k = 0                  
                        for i in range(len(literl_pool)):   # 한번 리터럴 풀에 같은 값 있는지 확인
                            if literl_pool[i][0] == 'word' and literl_pool[i][1] == temp_value:
                                k = 1       # label과 값을 비교한다.
                                break
                        # pool_addr는 imm_value가 저장될 혹은 된 상대 주소를 가지게 한다.
                        if k == 0:               # 리터럴 풀에 없는 경우
                            pool_addr = literl_pool[0][1] + (len(literl_pool) - 1) * 4
                            literl_pool.append(['word',  temp_value]) # 리터럴 풀에 저장

                        else:                    # 리터럴 풀에 값이 있는 경우
                            pool_addr = literl_pool[0][1] + (i - 1) * 4

                        # pc 상대 주소값으로 바꾸다. ex) ldr r1, [pc, #4]
                        args[2] = '[pc'
                        args.append(',')
                        temp_str = str(pool_addr - (addr + 8))
                        if temp_str == '0':     # offset이 0이면 앞에 '-' 붙이기
                            temp_str = '-0'
                        args.append('#' + temp_str + ']')

                    else:  # 12bit로 표현 가능하면 mov로 전환하고 아래 mov family에서 바꿀 수 있게 한다.
                        tok = 'mov' + tok[3:]
                        args[2] = '#' + str(temp_value)
            
                elif args[2][1:] in symbol_table:           # ldr r1, =lable 형태   
                    args[2] = args[2][1:]   # '=' 제거

                    k = 0
                    for i in range(len(literl_pool)):        # 한번 리터럴 풀에 같은 값 있는 지 확인
                        if literl_pool[i][0] == args[2] + 'addr':    # label을 검사한다
                            k = 1
                            break

                    if k == 0:      # 풀에 값이 없는 경우
                        pool_addr = literl_pool[0][1] + (len(literl_pool) - 1) * 4
                        literl_pool.append([args[2] + 'addr', symbol_table[args[2]][1]])

                    else:           # 풀에 값이 있는 경우
                        pool_addr = literl_pool[0][1] + (i - 1) * 4

                    args.append(',')
                    temp_str = str(pool_addr - (addr + 8))
                    if temp_str == '0':     # offset이 0이면 앞에 '-' 붙이기
                        temp_str = '-0'
                    args.append('#' + temp_str + ']')
                    args[2] = '[pc'         # args[2]를 써야하기에 마지막에 초기화

                else:
                    print("ERROR wrong ldr instruction")
                    sys.exit(1)

            elif args[2] in symbol_table:               # ldr r1, label 형식
                temp_addr = symbol_table[args[2]][1]
                args.append(',')
                temp_str = str(temp_addr - (addr + 8))
                if temp_str == '0':
                    temp_str = '-0'
                args.append('#' + temp_str + ']')
                args[2] = '[pc'         # args[2]를 써야하기에 마지막에 초기화

            
            if flag == False:       # mov로 바꾸지 않는 경우 -> I ,P, U, B, W, L, 등 업데이트
                mach_code |= 1 << 26
                if tok[:3] == 'ldr':
                    mach_code |= 1 << 20                # L 업데이트
                tok = tok[3:]
            
                (mach_code, tok) = process_cond_field(mach_code, tok)   # cond 업데이트

                if len(tok) > 0 and tok[0] == 'b':      # B 업데이트
                    mach_code |= 1 << 22
                    tok = tok[1:]

                mach_code |= registers[args[0]] << 12   # Rd 업데이트
                i = 2
                while i < len(args) and args[i] != ',':
                    temp_str = args[i].strip('[]!')
                    if temp_str in registers:
                        mach_code |= registers[temp_str] << 16     # Rn 업데이트
                    i += 1
                i += 1
                # 이제 i는 ldr r1, [r2, r4]를 예로 'r4' 혹은 'r4]'를 가리킨다.
                # 혹은 ldr r1, [r2]에서 [r2]를 가리킬 수도 있다.
                # prefix
                if args[len(args)-1].endswith('!') or args[len(args)-1].endswith(']') or i > len(args):
                    mach_code |= 1 << 24            # P 업데이트
                 
                    if args[len(args)-1].endswith('!'):
                        mach_code |= 1 << 21        # W 업데이트

                    if i > len(args):      # ex) ldr r1, [r2]
                        mach_code |= 1 << 23        # U 업데이트

                    else:
                        if args[i].find('-') == -1:
                            mach_code |= 1 << 23        # U 업데이트

                        args[i] = args[i].strip('#-]!')

                        # ex) ldr r1, [r2, r4, lsl #4]
                        if len(args) - 1 > i and args[i+1] == ',':
                            args[i] = args[i].strip('-')
                            mach_code |= registers[args[i]]     # offset 업데이트
                            mach_code |= 1 << 25                # I 업데이트
                            mach_code |= sh[args[i+2]] << 5     # sh 업데이트
                            args[i+3] = args[i+3].strip('#]!') 
                            mach_code |= int(args[i+3]) << 7

                        elif is_digit(args[i]):         # ex) ldr r1, [r2, #4]
                            mach_code |= int(args[i])   # offset 지정
                    
                        elif args[i] in registers:      # ex) ldr r1, [r2, r4]
                            mach_code |= registers[args[i]]
                            mach_code |= 1 << 25        # I 업데이트

                        else:
                            print("EROR, ldr")
                            sys.exit(1)

                else:   #post fix
                    if args[i].find('-') == -1:
                        mach_code |= 1 << 23        # U 업데이트

                    if args[i].startswith('#'):     # ex) ldr r1, [r2], #4
                        args[i]=args[i].strip('#-')
                        mach_code |= int(args[i])
                    
                    elif len(args) - 1 > i:         # ex) ldr r1, [r2], r1, lsl r4
                        mach_code |= 1 << 25              # I 업데이트
                        mach_code |= registers[args[i]]   # Rm 업데이트
                        mach_code |= sh[args[i+2]] << 5   # sh 업데이트
                        
                        if args[i+3].startswith('#'):
                            mach_code |= (int(args[i+3][1:])) << 7

                        else:
                            print("ERROR ldr r1, [r2], r3, lsl #4")
                            sys.exit(1)
                    else:                           # ex) ldr r1, [r2], r4
                        mach_code |= 1 << 25              # I 업데이트  
                        args[i] = args[i].strip('-')
                        mach_code |= registers[args[i]]                


    # data processing family
    if tok[:3] in opcode:
        # mov, mvn, add, sub, and, bic family
        mov_re = '(mov|mvn|add|sub|and|bic)' + cond_regexp + '?' + 's' + '?'
        processing = tok[:3]
        if re.match(mov_re, tok):
            (mach_code, tok) = process_cond_field(mach_code, tok[3:]) # cond 업데이트
            (mach_code, tok) = process_S_flag(mach_code, tok)         # S 업데이트
            mach_code = process_2_args(mach_code, args, processing)   # opcode, Rn, Rd, operand2 업데이트

    # swi family
    elif tok[:3] == 'swi':
        swi_re = 'swi' + cond_regexp + '?'

        if re.match(swi_re, tok) and is_digit(args[0]) and len(args) == 1:
            (mach_code, tok) = process_cond_field(mach_code, tok[3:])       # cond 업데이트
            mach_code |= 0b1111 << 24
            mach_code |= int(args[0])

        else:
            print("ERROR: Invalid operand")
            sys.exit(1)

    # mul, mla family
    elif tok[:3] in mul_opcode:
        mul_re = '(mul|mla)' + cond_regexp + '?' + 's' + '?'

        if re.match(mul_re, tok):
            if tok[:3] == 'mla' and len(args) != 7:     # mla의 args의 길이는 7이어야 한다.
                print("ERROR: Invalid operand")
                sys.exit(1)
            mach_code |= int(mul_opcode[tok[:3]]) << 21     # A 업데이트
            (mach_code, tok) = process_cond_field(mach_code, tok[3:])  # cond 업데이트
            mach_code |= 0b000000 << 22

            if tok == 's':
                mach_code |= 1 << 20                        # S 부분 업데이트
                tok = tok[1:]
            mach_code = process_mul_args(mach_code, args)   # 나머지 업데이트
        else:
            print("ERROR: Invalid operand")
            sys.exit(1)

    # b family
    elif tok[:1] == 'b':
        b_re = 'b' + 'l' + '?' + cond_regexp + '?'

        if re.match(b_re, tok):
            mach_code |= 0b101 << 25    
            if len(tok) > 1 and tok[1] == 'l':
                mach_code |= 1 << 24    # L 업데이트
            (mach_code, tok) = process_cond_field(mach_code, tok[2:])   # cond 업데이트
            
            if len(args) == 1:  # b 명령어의 args의 길이는 1이어야 한다.
                a = symbol_table[args[0]][1] - (addr + 8)   # offset 계산
                if a >= 0:      # offset 양수
                    mach_code |= int(a / 4)
                else:           # offset 음수
                    b = int(1 << 24)
                    mach_code |= int(bin(b + int(a/4)), 2)
            else:
                print("ERROR: Invalid operand")
                sys.exit(1)
                        
    return mach_code


### main() starts here ###

instruc_fech_addr = 0
symbol_table = {}

lines = sys.stdin.readlines()
splitter = re.compile(r'([ \t\n,])')

directives = {'byte' : 1, '2byte' : 2, 'hword' : 2, 'word' : 4}
section = 0
section_addr = {'.start' : 0, '.data' : 0, '.end' : 0}

# one pass
for i in range(len(lines)):
    tokens = splitter.split(lines[i])         # mov r1, #2 -> ["mov", " ", "r1", ",", " ", "#2", "\n", ""]
    tokens = [tok for tok in tokens
              if re.match('\s*$', tok) == None]
    mach_code = 0
    while len(tokens) > 0:
        # ex) msg: .asc 
        if tokens[0].endswith(':'): # process label
            symbol_table[tokens[0][:-1]] = (section, instruc_fech_addr)
            tokens = tokens[1:]
        # ex) mag : .asciz "1234" or msg:.asciz "1234"
        elif tokens[0].find(':') != -1 or (len(tokens) > 1 and tokens[1].startswith(':')):
            i = tokens[0].find(':')
            if i != -1:
                symbol_table[tokens[0][:i]] = (section, instruc_fech_addr)
                tokens[0] = tokens[0][i+1:]
            else:
                symbol_table[tokens[0]] = (section, instruc_fech_addr)
                if len(tokens[1]) == 1:
                    tokens = tokens[2:]
                else:
                    tokens[1] = tokens[1][1:]
                    tokens = tokens[1:]

        elif tokens[0].startswith('.'): # process directive
            data_type = tokens[0][1:]
            addr_len = 0
            if tokens[0] == '.text':
                section_addr['.text'] = instruc_fech_addr
                instruc_fech_addr = 0   # 상대주소 초기화
                section = 0
                break

            elif tokens[0] == '.data':
                section_addr['.data'] = instruc_fech_addr
                instruc_fech_addr = 0   # 상대주소 초기화
                section = 1
                break

            elif data_type in directives:
                data_len = directives[data_type]
                tokens = tokens[1:]
                for i in range(0, len(tokens), 2):
                    addr_len += data_len

                if addr_len % 2 != 0 and section == 0:  # .text section에서 
                    print("data len ERROR")             # 짝수 길이가 아니면 에러
                    sys.exit(1)
                instruc_fech_addr += addr_len           # 주소 길이 더하기
                break

            elif data_type == 'asciz' or data_type == 'ascii':
                asc_str = lines[i].strip('"')
                temp = asc_str[asc_str.find('"') : ]
                temp = temp.strip('"\n')
                
                control_char = {'0' :0, 'a' :7, 'b':8, 't':9, 'n':10, 'v':11, 
                                'f':12, 'r':13, '"':34, "'":39, '\\':92 }

                i = 0
                addr_len = 0
                while i < len(temp):
                    if temp[i] == '\\':
                        if i+1 < len(temp) and temp[i+1] in control_char:
                            i += 1
                    i += 1
                    addr_len += 1
                
                if data_type == 'asciz':     # 마지막 null 문자 고려
                    addr_len += 1

                if addr_len % 2 != 0 and section == 0:  # 짝수 길이가 아니면 에러
                    print("data len ERROR " + str(addr_len))
                    sys.exit(1)

                instruc_fech_addr += addr_len       # 주소 길이 더하기
                break

            else: 
                break
        
        elif len(tokens) > 0:
            instruc_fech_addr += 0x4
            break

section_addr['.end'] = instruc_fech_addr

if section_addr['.data'] == 0:   # .text 섹션이 먼저 나온 경우
    literl_pool.append(['start', section_addr['.end']])
else:                            # .data 섹션이 먼저 나온 경우
    literl_pool.append(['start', section_addr['.data']])

# .text 마지막 주소값 4의 배수로 맞추기
if literl_pool[0][1] % 4 == 2:
    literl_pool[0][1] += 2

section_flag = True
addr = 0
result = []

# two pass
for line in lines:
    if re.match('.data', line):
        section_flag = False

    elif re.match('.text', line):
        #result.append(["Disassembly of section", ".text:"])
        section_flag = True

    elif section_flag == True:
        tokens = splitter.split(line)               # mov r1, #2 -> ["mov", " ", "r1", ",", " ", "#2", "\n", ""]
        tokens = [tok for tok in tokens
                  if re.match('\s*$', tok) == None]
        mach_code = 0

        while len(tokens) > 0:
            if tokens[0].endswith(':'): # process label          
                tokens = tokens[1:]
        
             # mag : .asciz "1234" | msg:.asciz "1234"
            elif tokens[0].find(':') != -1 or (len(tokens) > 1 and tokens[1].startswith(':')):  
                i = tokens[0].find(':')
                if i != -1:
                    tokens[0] = tokens[0][i+1:]
                else:
                    if len(tokens[1]) == 1:
                        tokens = tokens[2:]
                    else:
                        tokens[1] = tokens[1][1:]
                        tokens = tokens[1:]

            elif tokens[0].startswith('.'): # process directive 
                data_type = tokens[0][1:]
                addr_len = 0

                if data_type in directives:
                    data_len = directives[data_type]
                    tokens = tokens[1:]

                    # magaddr : .word msg 형태 고려
                    if data_len == 4 and tokens[0] in symbol_table:
                        while len(tokens) > 0 and tokens[0] in symbol_table:
                            result.append([addr, symbol_table[tokens[0]][1]])
                            addr += 4
                            tokens = tokens[1:]

                    temp_value = 0  # 4byte 단위로 메모리에 들어갈 값

                    i = 0
                    while i < len(tokens):
                        j = 0
                        while j < 4 and i < len(tokens):
                            addr_len += data_len
                            temp_value |= int(tokens[i]) << (j * 8)
                            j += data_len
                            i += 2
                        # 4byte가 초과되면 result에 추가
                        result.append([addr, temp_value])
                        addr += j
                        temp_value = 0
                    break

                elif data_type == 'asciz' or data_type == 'ascii':
                    asc_str = line[line.find('"') : ]
                    temp = line[line.find('"') : ]
                    temp = temp.rstrip('\n')
                    temp = temp.strip('"')
                    
                    control_char = {'0' :0, 'a' :7, 'b':8, 't':9, 'n':10, 
                                    'v':11, 'f':12, 'r':13, '"':34, "'":39, '\\':92 }
                    temp_value = 0  # 4byte 단위로 메모리에 들어갈 값

                    i = 0
                    while i < len(temp):
                        j = 0
                        while j < 4 and i < len(temp):  # 길이가 4이거나 len(temp)까지 반복
                            if temp[i] == '\\':
                                if i+1 < len(temp) and temp[i+1] in control_char:
                                    temp_value |= control_char[temp[i+1]] << (j * 8)
                                    i += 1
                            else:
                                temp_value |= ord(temp[i]) << (j * 8)
                            i += 1
                            j += 1

                        result.append([addr, temp_value])   # 4byte 초과되면 result에 추가
                        addr += j
                        temp_value = 0

                    if data_type == 'asciz':                # asciz이면 마지막에 null 추가 계산
                        addr += 1                           # 하고 0값 넣기
                        result[-1][1] |= 0b00000000 << (j * 8)
                    break

                else:
                    break

            elif len(tokens) > 0: # process instruction(명령어 변환)
                mach_code = process_instruction(tokens, addr)     # 16진수로 표현된 기계어 코드 문자열 출력
                result.append([addr, mach_code])
                addr += 4
                break

start_addr = 0x8080

print("Disassembly of section .text:")
# .text 섹션 출력
for (i, r) in enumerate(result, 0):

    machine_code = hex(r[1])        # 출력할 16진수 기계어
    print_len = 10                  # 출력할 최대 길이
    # 만약 기계어의 길이가 4이거나, .text 섹션의 마지막이 4byte 단위로 끝나지 않을 때
    if i+1 < len(result) and (result[i+1][0] - r[0] == 2) or (literl_pool[0][1] - r[0]) == 2:
        print_len = 6               # 출력할 최대 길이는 6

    for i in range(print_len - len(machine_code)):
        machine_code = machine_code[:2] + '0' + machine_code[2:]

    for symbol in symbol_table:
        # .text 섹션이면서 simbol의 주소값이랑 result[0]이 같다면
        if symbol_table[symbol][0] == 0 and symbol_table[symbol][1] == r[0]:
            print()
            label_str = '0' * (8 - len(hex(r[0]+start_addr)[2:]))
            print(label_str + hex(r[0]+start_addr)[2:] + ' <' + symbol + '>:')
            break
    
    print(' ' * (5- len(hex(r[0]+start_addr)[2:])) + 
          hex(r[0]+start_addr)[2:] + ":   " + machine_code[2:])

literl_pool_start_addr = literl_pool[0][1] + start_addr

# 리터럴 풀 출력
for i in range(1, len(literl_pool)):
    machine_code = literl_pool[i][1]
    if machine_code >= 0:
        machine_code = hex(literl_pool[i][1])
        for i in range(10 - len(machine_code)):
            machine_code = machine_code[:2] + '0' + machine_code[2:]
    else:   # 음수이면 2의 보수를 취하고 출력하기
        temp = int(1 << 32)
        machine_code = hex(int(bin(temp + int(machine_code)), 2))

    print(' ' * (5- len(hex(literl_pool_start_addr)[2:])) + 
          hex(literl_pool_start_addr)[2:] + ":   " + machine_code[2:])
    literl_pool_start_addr += 4
