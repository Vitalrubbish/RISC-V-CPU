from assassyn.frontend import *

ROB_SIZE = 5

class ROB(Module):

    def __init__(self):
        super().__init__(ports = {
            "is_reg_write" : Port(Bits(1)),
            "is_memory_write" : Port(Bits(1)),
            "is_branch": Port(Bits(1)),
            "rd": Port(Bits(5)),
            "has_rd": Port(Bits(1)),
            "rs1": Port(Bits(5)),
            "has_rs1": Port(Bits(1)),
            "rs2": Port(Bits(5)),
            "has_rs2": Port(Bits(1)),
            "imm": Port(Bits(32)),
            "has_imm": Port(Bits(1)),
            "addr": Port(Bits(32))
        }, no_arbiter = True)
        self.name = "ROB"

    @module.combinational
    def build(self):

        # ROB 自身的性质
        allocated_array = RegArray(Bits(1), ROB_SIZE)         # ROB 中这一条有没有分配指令
        ready_array = RegArray(Bits(1), ROB_SIZE)             # ROB 中当前指令能不能 commit
        head = RegArray(Int(32), 1, initializer = [0])        # 存储 ROB 的头指针
        tail = RegArray(Int(32), 1, initializer = [0])        # 存储 ROB 的尾指针
        rob_size = RegArray(Bits(32), 1)                      # 存储 ROB 目前指令的条数
        rob_full = Bits(1)(0)                                 # 存储 ROB 是否已满

        # 指令有关的信息
        is_reg_write_array = RegArray(Bits(1), ROB_SIZE)      # 是否为写回到寄存器的指令
        is_memory_write_array = RegArray(Bits(1), ROB_SIZE)   # 是否为写回到内存的指令
        is_branch_array = RegArray(Bits(1), ROB_SIZE)         # 是否为分支指令

        rd_array = RegArray(Bits(5), ROB_SIZE)                # 存储指令的 rd
        rd_valid_array = RegArray(Bits(1), ROB_SIZE)          # 存储 rd 是否已经准备好

        rs1_array = RegArray(Bits(5), ROB_SIZE)               # 存储指令的 rs1
        rs1_valid_array = RegArray(Bits(1), ROB_SIZE)         # 存储 rs1 是否已经准备好

        rs2_array = RegArray(Bits(5), ROB_SIZE)               # 存储指令的 rs2
        rs2_valid_array = RegArray(Bits(1), ROB_SIZE)         # 存储 rs2 是否已经准备好

        imm_array = RegArray(Bits(32), ROB_SIZE)              # 存储立即数 imm

        calc_result_array = RegArray(Bits(32), ROB_SIZE)      # 存储 alu 计算出的 32 位结果
        load_result_array = RegArray(Bits(32), ROB_SIZE)      # 存储 load 出来的 32 位结果

        addr_array = RegArray(Bits(32), ROB_SIZE)             # 存储指令的地址

        rob_full = (rob_size[0].bitcast(Int(32)) == Int(32)(ROB_SIZE))

        (
            is_reg_write,
            is_memory_write,
            is_branch,
            rd,
            has_rd,
            rs1,
            has_rs1,
            rs2,
            has_rs2,
            imm,
            has_imm,
            addr
        ) = self.pop_all_ports(True)

        log("addr: 0x{:08x} | is_reg_write: {} | is_memory_write: {} | is_branch: {}", addr, is_reg_write, is_memory_write, is_branch)
        log("rd: 0x{:02x} | has_rd: {} | rs1: 0x{:02x} | has_rs1: {} | rs2: 0x{:02x} | has_rs2: {} | imm: 0x{:08x} | has_imm: {}",
            rd, has_rd, rs1, has_rs1, rs2, has_rs2, imm, has_imm)
        
        head_ptr = head[0]
        tail_ptr = tail[0]

        updated_tail_ptr = tail_ptr + Int(32)(1)
        updated_tail_ptr = (updated_tail_ptr == Int(32)(ROB_SIZE)).select(Int(32)(0), updated_tail_ptr)
        updated_rob_size = rob_size[0] + Int(32)(1)

        with Condition(~rob_full):
            allocated_array[tail_ptr] = Bits(1)(1)
            ready_array[tail_ptr] = Bits(1)(0)
            is_branch_array[tail_ptr] = is_branch
            is_memory_write_array[tail_ptr] = is_memory_write
            is_reg_write_array[tail_ptr] = is_reg_write

            # Need to implement Regsiter File First...

            tail[0] = updated_tail_ptr
            rob_size[0] = updated_rob_size
