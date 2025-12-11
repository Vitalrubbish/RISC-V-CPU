from assassyn.frontend import *

ROB_SIZE = 5

class ROB(Module):

    def __init__(self):
        super().__init__(ports = {}, no_arbiter = True)
        self.name = "ROB"

    @module.combinational
    def build(self):
        allocated = RegArray(Bits(1), ROB_SIZE)         # ROB 中这一条有没有分配指令
        ready = RegArray(Bits(1), ROB_SIZE)             # ROB 中当前指令能不能 commit
        is_reg_write = RegArray(Bits(1), ROB_SIZE)      # 是否为写回到寄存器的指令
        is_memory_write = RegArray(Bits(1), ROB_SIZE)   # 是否为写回到内存的指令
        is_branch = RegArray(Bits(1), ROB_SIZE)         # 是否为分支指令

        rd = RegArray(Bits(5), ROB_SIZE)                # 存储指令的 rd
        rd_valid = RegArray(Bits(1), ROB_SIZE)          # 存储 rd 是否已经准备好

        rs1 = RegArray(Bits(5), ROB_SIZE)               # 存储指令的 rs1
        rs1_valid = RegArray(Bits(1), ROB_SIZE)         # 存储 rs1 是否已经准备好

        rs2 = RegArray(Bits(5), ROB_SIZE)               # 存储指令的 rs2
        rs2_valid = RegArray(Bits(1), ROB_SIZE)         # 存储 rs2 是否已经准备好

