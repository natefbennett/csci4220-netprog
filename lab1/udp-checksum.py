# Nate Bennett
# 09-10-2021
# given a file of 16 bit hex numbers on each line,
# compute the sum and print the one's complement
# if addition causes the number to exceed 16 bits
# ignore the carry and add 1 instead

def OnesComplement( s ):

    s_ret = ''
    for c in s:
        if c == '1':
            s_ret += '0'
        elif c == '0':
            s_ret += '1'
        else:
            print('Something went wrong!!')

    return s_ret

# source: https://www.geeksforgeeks.org/python-program-to-add-two-binary-numbers/
def Add( a, b, max_len ):

    result = ''
  
    # Initialize the carry
    carry = 0
    
    # Traverse the string
    for i in range(max_len - 1, -1, -1):
        r = carry
        r += 1 if a[i] == '1' else 0
        r += 1 if b[i] == '1' else 0
        result = ('1' if r % 2 == 1 else '0') + result
    
        # Compute the carry.
        carry = 0 if r < 2 else 1
    
    # over 16 bits, drop the carry and add one
    if carry != 0:
        result = Add(result,'0000000000000001', max_len)

    return result

f = open('data.txt', 'r')

sum = int(f.readline().strip(), 16)
for line in f:

    cur_int = int(line.strip(), 16)
    old_sum = sum

    # calculate new sum
    sum = int(Add( bin(sum)[2:].zfill(16), bin(cur_int)[2:].zfill(16), 16 ), 2)

    # print addition
    buffer = f'{bin(old_sum)[2:].zfill(16)} + {bin(cur_int)[2:].zfill(16)} = {bin(sum)[2:].zfill(16)}'
    if old_sum > sum:
        buffer += ' (overflow)'
    print(buffer)

checksum = OnesComplement(bin(sum)[2:])
print( f'\nOnesComplement( {bin(sum)[2:].zfill(16)} ) = {checksum}' )
print(f'Checksum = {hex(int(OnesComplement(checksum),2))}')