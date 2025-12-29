#!/usr/bin/env python3
"""
Convert hex memory dump file (like 1.in) to separate instruction (.exe) and data (.data) files.
"""

import sys
import argparse
from typing import Dict, List, Tuple


def parse_hex_file(filename: str) -> Dict[int, bytes]:
    """
    Parse hex file with format:
    @ADDRESS
    HEX HEX HEX ...
    
    Returns a dictionary mapping start address to a contiguous bytes object.
    Note: The hex file uses little-endian format (RISC-V standard).
    """
    segments = {}
    current_addr = None
    current_data = bytearray()
    start_addr = None
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('@'):
                # Save previous segment if exists
                if start_addr is not None and current_data:
                    segments[start_addr] = bytes(current_data)
                    current_data = bytearray()
                
                # Parse new address
                current_addr = int(line[1:], 16)
                start_addr = current_addr
            else:
                # Parse hex bytes
                if current_addr is None:
                    raise ValueError("Hex data before address declaration")
                
                hex_bytes = line.split()
                for hex_byte in hex_bytes:
                    byte_val = int(hex_byte, 16)
                    current_data.append(byte_val)
                    current_addr += 1
        
        # Save last segment
        if start_addr is not None and current_data:
            segments[start_addr] = bytes(current_data)
    
    return segments


def fill_memory(segments: Dict[int, bytes], start_addr: int, end_addr: int) -> bytes:
    """
    Fill memory from start_addr to end_addr, padding gaps with zeros.
    """
    memory = bytearray(end_addr - start_addr)
    
    for addr, data in segments.items():
        if start_addr <= addr < end_addr:
            offset = addr - start_addr
            end_offset = offset + len(data)
            if end_offset > len(memory):
                end_offset = len(memory)
                data = data[:end_offset - offset]
            memory[offset:end_offset] = data
    
    return bytes(memory)


def decode_riscv_instruction(word: int) -> str:
    """
    Decode a RISC-V instruction word and return its mnemonic.
    This is a basic decoder for common RV32I instructions.
    """
    opcode = word & 0x7F
    funct3 = (word >> 12) & 0x7
    funct7 = (word >> 25) & 0x7F
    rd = (word >> 7) & 0x1F
    rs1 = (word >> 15) & 0x1F
    rs2 = (word >> 20) & 0x1F
    
    # Use direct register numbering (x0, x1, x2, ...)
    def reg(idx):
        return f"x{idx}"
    
    # R-type
    if opcode == 0x33:  # OP
        if funct7 == 0x00:
            if funct3 == 0x0: return f"add {reg(rd)}, {reg(rs1)}, {reg(rs2)}"
            elif funct3 == 0x1: return f"sll {reg(rd)}, {reg(rs1)}, {reg(rs2)}"
            elif funct3 == 0x2: return f"slt {reg(rd)}, {reg(rs1)}, {reg(rs2)}"
            elif funct3 == 0x3: return f"sltu {reg(rd)}, {reg(rs1)}, {reg(rs2)}"
            elif funct3 == 0x4: return f"xor {reg(rd)}, {reg(rs1)}, {reg(rs2)}"
            elif funct3 == 0x5: return f"srl {reg(rd)}, {reg(rs1)}, {reg(rs2)}"
            elif funct3 == 0x6: return f"or {reg(rd)}, {reg(rs1)}, {reg(rs2)}"
            elif funct3 == 0x7: return f"and {reg(rd)}, {reg(rs1)}, {reg(rs2)}"
        elif funct7 == 0x20:
            if funct3 == 0x0: return f"sub {reg(rd)}, {reg(rs1)}, {reg(rs2)}"
            elif funct3 == 0x5: return f"sra {reg(rd)}, {reg(rs1)}, {reg(rs2)}"
    
    # I-type
    elif opcode == 0x13:  # OP-IMM
        imm = (word >> 20)
        if imm & 0x800:  # Sign extend
            imm = imm | 0xFFFFF000
        imm = imm & 0xFFFFFFFF
        if imm & 0x80000000:
            imm = imm - 0x100000000
            
        if funct3 == 0x0: return f"addi {reg(rd)}, {reg(rs1)}, {imm}"
        elif funct3 == 0x2: return f"slti {reg(rd)}, {reg(rs1)}, {imm}"
        elif funct3 == 0x3: return f"sltiu {reg(rd)}, {reg(rs1)}, {imm}"
        elif funct3 == 0x4: return f"xori {reg(rd)}, {reg(rs1)}, {imm}"
        elif funct3 == 0x6: return f"ori {reg(rd)}, {reg(rs1)}, {imm}"
        elif funct3 == 0x7: return f"andi {reg(rd)}, {reg(rs1)}, {imm}"
        elif funct3 == 0x1: return f"slli {reg(rd)}, {reg(rs1)}, {rs2}"
        elif funct3 == 0x5:
            if funct7 == 0x00: return f"srli {reg(rd)}, {reg(rs1)}, {rs2}"
            elif funct7 == 0x20: return f"srai {reg(rd)}, {reg(rs1)}, {rs2}"
    
    elif opcode == 0x03:  # LOAD
        imm = (word >> 20)
        if imm & 0x800:
            imm = imm | 0xFFFFF000
        imm = imm & 0xFFFFFFFF
        if imm & 0x80000000:
            imm = imm - 0x100000000
            
        if funct3 == 0x0: return f"lb {reg(rd)}, {imm}({reg(rs1)})"
        elif funct3 == 0x1: return f"lh {reg(rd)}, {imm}({reg(rs1)})"
        elif funct3 == 0x2: return f"lw {reg(rd)}, {imm}({reg(rs1)})"
        elif funct3 == 0x4: return f"lbu {reg(rd)}, {imm}({reg(rs1)})"
        elif funct3 == 0x5: return f"lhu {reg(rd)}, {imm}({reg(rs1)})"
    
    elif opcode == 0x67:  # JALR
        imm = (word >> 20)
        if imm & 0x800:
            imm = imm | 0xFFFFF000
        imm = imm & 0xFFFFFFFF
        if imm & 0x80000000:
            imm = imm - 0x100000000
        return f"jalr {reg(rd)}, {imm}({reg(rs1)})"
    
    elif opcode == 0x73:  # SYSTEM
        if word == 0x00100073:
            return "ebreak"
        elif word == 0x00000073:
            return "ecall"
        else:
            return f"system 0x{word:08x}"
    
    # S-type
    elif opcode == 0x23:  # STORE
        imm = ((word >> 25) << 5) | ((word >> 7) & 0x1F)
        if imm & 0x800:
            imm = imm | 0xFFFFF000
        imm = imm & 0xFFFFFFFF
        if imm & 0x80000000:
            imm = imm - 0x100000000
            
        if funct3 == 0x0: return f"sb {reg(rs2)}, {imm}({reg(rs1)})"
        elif funct3 == 0x1: return f"sh {reg(rs2)}, {imm}({reg(rs1)})"
        elif funct3 == 0x2: return f"sw {reg(rs2)}, {imm}({reg(rs1)})"
    
    # B-type
    elif opcode == 0x63:  # BRANCH
        imm = (((word >> 31) & 0x1) << 12) | (((word >> 7) & 0x1) << 11) | \
              (((word >> 25) & 0x3F) << 5) | (((word >> 8) & 0xF) << 1)
        if imm & 0x1000:
            imm = imm | 0xFFFFE000
        imm = imm & 0xFFFFFFFF
        if imm & 0x80000000:
            imm = imm - 0x100000000
            
        if funct3 == 0x0: return f"beq {reg(rs1)}, {reg(rs2)}, {imm}"
        elif funct3 == 0x1: return f"bne {reg(rs1)}, {reg(rs2)}, {imm}"
        elif funct3 == 0x4: return f"blt {reg(rs1)}, {reg(rs2)}, {imm}"
        elif funct3 == 0x5: return f"bge {reg(rs1)}, {reg(rs2)}, {imm}"
        elif funct3 == 0x6: return f"bltu {reg(rs1)}, {reg(rs2)}, {imm}"
        elif funct3 == 0x7: return f"bgeu {reg(rs1)}, {reg(rs2)}, {imm}"
    
    # U-type
    elif opcode == 0x37:  # LUI
        imm = (word >> 12) & 0xFFFFF
        return f"lui {reg(rd)}, 0x{imm:x}"
    
    elif opcode == 0x17:  # AUIPC
        imm = (word >> 12) & 0xFFFFF
        return f"auipc {reg(rd)}, 0x{imm:x}"
    
    # J-type
    elif opcode == 0x6F:  # JAL
        imm = (((word >> 31) & 0x1) << 20) | (((word >> 12) & 0xFF) << 12) | \
              (((word >> 20) & 0x1) << 11) | (((word >> 21) & 0x3FF) << 1)
        if imm & 0x100000:
            imm = imm | 0xFFE00000
        imm = imm & 0xFFFFFFFF
        if imm & 0x80000000:
            imm = imm - 0x100000000
        return f"jal {reg(rd)}, {imm}"
    
    # Unknown instruction
    return f"unknown 0x{word:08x}"


def bytes_to_words(data: bytes, little_endian: bool = True) -> List[int]:
    """
    Convert bytes to 32-bit words.
    RISC-V uses little-endian by default.
    """
    words = []
    for i in range(0, len(data), 4):
        if i + 4 <= len(data):
            if little_endian:
                word = int.from_bytes(data[i:i+4], byteorder='little')
            else:
                word = int.from_bytes(data[i:i+4], byteorder='big')
            words.append(word)
    return words


def write_exe_file(words: List[int], filename: str, start_addr: int = 0):
    """
    Write instructions to .exe file with decoded instruction mnemonics.
    Format: XXXXXXXX // 0xADDRESS: mnemonic
    For unknown instructions, only show address without mnemonic.
    """
    with open(filename, 'w') as f:
        for i, word in enumerate(words):
            addr = start_addr + i * 4
            mnemonic = decode_riscv_instruction(word)
            if mnemonic.startswith("unknown"):
                f.write(f"{word:08x} // 0x{addr:04x}:\n")
            else:
                f.write(f"{word:08x} // 0x{addr:04x}: {mnemonic}\n")


def write_data_file(words: List[int], filename: str):
    """
    Write data to .data file.
    Format: one hex value per line (without 0x prefix).
    """
    with open(filename, 'w') as f:
        for word in words:
            # Format as hex without 0x prefix
            # Based on 0to100.data, it seems to use minimal hex digits
            f.write(f"{word:x}\n")


def get_memory_range(segments: Dict[int, bytes]) -> Tuple[int, int]:
    """
    Get the full memory range from the segments.
    
    Returns: (min_addr, max_addr)
    """
    if not segments:
        return 0, 0
    
    min_addr = min(segments.keys())
    max_addr = max(addr + len(segments[addr]) for addr in segments.keys())
    
    return min_addr, max_addr


def main():
    parser = argparse.ArgumentParser(
        description='Convert hex memory dump to .exe and .data files. '
                    'Both files will contain the same memory content in different formats.'
    )
    parser.add_argument('input', help='Input hex file (e.g., 1.in)')
    parser.add_argument('--output-base', '-o', default='output',
                        help='Base name for output files (default: output)')
    parser.add_argument('--start', type=lambda x: int(x, 0), default=None,
                        help='Memory start address (hex or decimal). Auto-detected if not specified.')
    parser.add_argument('--end', type=lambda x: int(x, 0), default=None,
                        help='Memory end address (hex or decimal). Auto-detected if not specified.')
    parser.add_argument('--little-endian', action='store_true', default=True,
                        help='Use little-endian byte order (default for RISC-V)')
    parser.add_argument('--big-endian', action='store_true',
                        help='Use big-endian byte order')
    
    args = parser.parse_args()
    
    # Parse input file
    print(f"Parsing {args.input}...")
    segments = parse_hex_file(args.input)
    
    if not segments:
        print("Error: No data found in input file")
        return 1
    
    # Determine byte order
    little_endian = not args.big_endian
    endian_str = "little-endian" if little_endian else "big-endian"
    print(f"Using {endian_str} byte order")
    
    # Print memory map
    print("\nMemory segments in input file:")
    for addr in sorted(segments.keys()):
        size = len(segments[addr])
        print(f"  0x{addr:08x} - 0x{addr+size:08x} ({size} bytes)")
    
    # Determine memory range
    if args.start is not None and args.end is not None:
        start_addr = args.start
        end_addr = args.end
        print(f"\nUsing specified memory range: 0x{start_addr:08x} - 0x{end_addr:08x}")
    else:
        start_addr, end_addr = get_memory_range(segments)
        print(f"\nAuto-detected memory range: 0x{start_addr:08x} - 0x{end_addr:08x}")
    
    # Fill memory (with zeros for gaps)
    memory = fill_memory(segments, start_addr, end_addr)
    words = bytes_to_words(memory, little_endian)
    
    # Write .exe file (instruction format)
    exe_file = f"{args.output_base}.exe"
    print(f"\nWriting {len(words)} words to {exe_file} (instruction format)...")
    write_exe_file(words, exe_file, start_addr)
    
    # Write .data file (data format)
    data_file = f"{args.output_base}.data"
    print(f"Writing {len(words)} words to {data_file} (data format)...")
    write_data_file(words, data_file)
    
    print("\nConversion completed successfully!")
    print(f"Both files contain the same memory content (0x{start_addr:08x} - 0x{end_addr:08x})")
    print(f"  - {exe_file}: formatted as instructions")
    print(f"  - {data_file}: formatted as data")
    return 0


if __name__ == '__main__':
    sys.exit(main())
