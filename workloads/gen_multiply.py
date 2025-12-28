def encode_r(opcode, rd, funct3, rs1, rs2, funct7):
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

def encode_i(opcode, rd, funct3, rs1, imm):
    if imm < 0: imm += (1 << 12)
    return (imm << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode

def encode_s(opcode, funct3, rs1, rs2, imm):
    if imm < 0: imm += (1 << 12)
    imm_11_5 = (imm >> 5) & 0x7F
    imm_4_0 = imm & 0x1F
    return (imm_11_5 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (imm_4_0 << 7) | opcode

def encode_b(opcode, funct3, rs1, rs2, imm):
    if imm < 0: imm += (1 << 13)
    imm_12 = (imm >> 12) & 1
    imm_10_5 = (imm >> 5) & 0x3F
    imm_4_1 = (imm >> 1) & 0xF
    imm_11 = (imm >> 11) & 1
    return (imm_12 << 31) | (imm_10_5 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (imm_11 << 7) | (imm_4_1 << 8) | opcode

def to_hex(val):
    return f"{val:08x}"

instructions = []

# 0: addi x5, x0, 0
instructions.append(encode_i(0x13, 5, 0, 0, 0))
# 4: addi x6, x0, 20
instructions.append(encode_i(0x13, 6, 0, 0, 20))
# 8: addi x7, x0, 0
instructions.append(encode_i(0x13, 7, 0, 0, 0))
# 12: addi x28, x0, 80
instructions.append(encode_i(0x13, 28, 0, 0, 80))
# 16: addi x29, x0, 160
instructions.append(encode_i(0x13, 29, 0, 0, 160))
# 20: addi x10, x0, 0
instructions.append(encode_i(0x13, 10, 0, 0, 0))

# 24: lw x30, 0(x7)
instructions.append(encode_i(0x03, 30, 2, 7, 0))
# 28: lw x31, 0(x28)
instructions.append(encode_i(0x03, 31, 2, 28, 0))
# 32: mul x30, x30, x31
# Opcode 0x33 (0110011), funct3 0, funct7 1
instructions.append(encode_r(0x33, 30, 0, 30, 31, 1))
# 36: lw x31, 0(x29)
instructions.append(encode_i(0x03, 31, 2, 29, 0))
# 40: beq x30, x31, 8
instructions.append(encode_b(0x63, 0, 30, 31, 8))
# 44: addi x10, x10, 1
instructions.append(encode_i(0x13, 10, 0, 10, 1))
# 48: addi x7, x7, 4
instructions.append(encode_i(0x13, 7, 0, 7, 4))
# 52: addi x28, x28, 4
instructions.append(encode_i(0x13, 28, 0, 28, 4))
# 56: addi x29, x29, 4
instructions.append(encode_i(0x13, 29, 0, 29, 4))
# 60: addi x5, x5, 1
instructions.append(encode_i(0x13, 5, 0, 5, 1))
# 64: blt x5, x6, -40
instructions.append(encode_b(0x63, 4, 5, 6, -40))

# 68: ebreak
instructions.append(0x00100073)
# 72: nop (addi x0, x0, 0)
instructions.append(encode_i(0x13, 0, 0, 0, 0))
# 76: nop
instructions.append(encode_i(0x13, 0, 0, 0, 0))

comments = [
    "addi x5, x0, 0      i = 0",
    "addi x6, x0, 20     limit = 20",
    "addi x7, x0, 0      base_a = 0",
    "addi x28, x0, 80    base_b = 80",
    "addi x29, x0, 160   base_result = 160",
    "addi x10, x0, 0     error = 0",
    "lw x30, 0(x7)       x30 = a[i]",
    "lw x31, 0(x28)      x31 = b[i]",
    "mul x30, x30, x31   x30 = a[i] * b[i]",
    "lw x31, 0(x29)      x31 = result[i]",
    "beq x30, x31, 8     if x30 == x31 goto PC+8",
    "addi x10, x10, 1    error++",
    "addi x7, x7, 4      base_a++",
    "addi x28, x28, 4    base_b++",
    "addi x29, x29, 4    base_result++",
    "addi x5, x5, 1      i++",
    "blt x5, x6, -40     if i < 20 goto PC-40",
    "ebreak",
    "nop",
    "nop"
]

print("EXE FILE CONTENT:")
for i, inst in enumerate(instructions):
    print(f"{to_hex(inst)} // {i*4:2}: {comments[i]}")

a = [32, 45, 23, 67, 89, 12, 90, 34, 56, 78, -11, -22, -33, -44, -55, -66, -77, -88, -99, -100]
b = [21, 43, 65, 87, 9, -10, -11, -12, -13, -14, 15, 16, 17, 18, 19, -20, -21, -22, -23, -24]
result = [x * y for x, y in zip(a, b)]

def to_hex_data(val):
    return f"{val & 0xffffffff:x}"

print("\nDATA FILE CONTENT:")
for x in a: print(to_hex_data(x))
for x in b: print(to_hex_data(x))
for x in result: print(to_hex_data(x))
