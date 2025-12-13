from assassyn.frontend import *
from instruction import *
from RS import *
from opcodes import *

ROB_SIZE = 5

class ROB(Module):

    def __init__(self):
        super().__init__(ports = {
            "signals": Port(decoder_signals),
            "addr": Port(Bits(32))
        }, no_arbiter = True)
        self.name = "ROB"

    @module.combinational
    def build(
        self, 
        rob_full_array: Array, 
        rf_value_array: Array, 
        rf_recorder_array: Array, 
        rf_has_recorder_array: Array,

        rob_index_array_from_alu: Array,
        result_array_from_alu: Array,
        pc_result_array_from_alu: Array,

        rs: RS
    ):
        # 参数解析： 
        # rob_full_array: Array(Bits(1), 1)                     判定 rob 是否已满
        # rf_value_array: Array(Bits(32), 32)                   存储 rf 中各个寄存器的值
        # rf_recorder_array: Array(Bits(5), 32)                 存储 rf 中各个寄存器 recorder 的编号
        # rf_has_recorder_array: Array(Bits(1), 32)             存储当前 rf 中各个寄存器是否有 recorder

        # ROB 自身的性质
        allocated_array = RegArray(Bits(1), ROB_SIZE)         # ROB 中这一条有没有分配指令
        ready_array = RegArray(Bits(1), ROB_SIZE)             # ROB 中当前指令能不能 commit
        head = RegArray(Int(32), 1, initializer = [0])        # 存储 ROB 的头指针
        tail = RegArray(Int(32), 1, initializer = [0])        # 存储 ROB 的尾指针
        rob_size = RegArray(Bits(32), 1)                      # 存储 ROB 目前指令的条数
        rob_full = Bits(1)(0)                                 # 存储 ROB 是否已满
        rob_empty = Bits(1)(0)

        # 指令有关的信息
        is_reg_write_array = RegArray(Bits(1), ROB_SIZE)      # 是否为写回到寄存器的指令
        is_memory_write_array = RegArray(Bits(1), ROB_SIZE)   # 是否为写回到内存的指令
        is_branch_array = RegArray(Bits(1), ROB_SIZE)         # 是否为分支指令
        is_load_or_store_array = RegArray(Bits(1), ROB_SIZE)  # 是否为 load/store 指令

        rd_array = RegArray(Bits(5), ROB_SIZE)                # 存储指令的 rd
        rd_valid_array = RegArray(Bits(1), ROB_SIZE)          # 存储 rd 是否已经准备好

        rs1_array = RegArray(Bits(5), ROB_SIZE)               # 存储指令的 rs1
        rs1_valid_array = RegArray(Bits(1), ROB_SIZE)         # 存储 rs1 是否已经准备好

        rs2_array = RegArray(Bits(5), ROB_SIZE)               # 存储指令的 rs2
        rs2_valid_array = RegArray(Bits(1), ROB_SIZE)         # 存储 rs2 是否已经准备好

        imm_array = RegArray(Bits(32), ROB_SIZE)              # 存储立即数 imm

        calc_result_array = RegArray(Bits(32), ROB_SIZE)      # 存储 alu 计算出的 32 位结果
        load_result_array = RegArray(Bits(32), ROB_SIZE)      # 存储 load 出来的 32 位结果
        pc_result_array = RegArray(Bits(32), ROB_SIZE)

        addr_array = RegArray(Bits(32), ROB_SIZE)             # 存储指令的地址

        rob_full = (rob_size[0].bitcast(Int(32)) == Int(32)(ROB_SIZE))
        rob_full_array[0] = rob_full

        rob_empty = (rob_size[0].bitcast(Int(32)) == Int(32)(0))

        signals, addr = self.pop_all_ports(True)

        rd = signals.rd
        has_rd = signals.rd_valid
        rs1 = signals.rs1
        has_rs1 = signals.rs1_valid
        rs2 = signals.rs2
        has_rs2 = signals.rs2_valid
        imm = signals.imm
        has_imm = signals.has_imm
        is_branch = signals.is_branch,
        is_reg_write = signals.is_reg_write
        is_memory_write = signals.is_memory_write,
        is_load_or_store = signals.is_load_or_store

        log("rob_full: {} | rob_size: {}", rob_full, rob_size[0])
        log("addr: 0x{:08x} | is_reg_write: {} | is_memory_write: {} | is_branch: {}", addr, is_reg_write, is_memory_write, is_branch)
        log("rd: 0x{:02x} | has_rd: {} | rs1: 0x{:02x} | has_rs1: {} | rs2: 0x{:02x} | has_rs2: {} | imm: 0x{:08x} | has_imm: {}",
            rd, has_rd, rs1, has_rs1, rs2, has_rs2, imm, has_imm)
        
        head_ptr = head[0]
        tail_ptr = tail[0]

        updated_tail_ptr = tail_ptr + Int(32)(1)
        updated_tail_ptr = (updated_tail_ptr == Int(32)(ROB_SIZE)).select(Int(32)(0), updated_tail_ptr)
        updated_rob_size = rob_size[0] + Int(32)(1)

        with Condition(~rob_full & has_rd):
            rf_recorder_array[rd] = tail_ptr
            rf_has_recorder_array[rd] = Bits(1)(1)
            rd_array[tail_ptr] = rd

        with Condition(~rob_full & has_rs1):
            rs1_array[tail_ptr] = rs1

        with Condition(~rob_full & has_rs2):
            rs2_array[tail_ptr] = rs2
    
        with Condition(~rob_full & has_imm):
            imm_array[tail_ptr] = imm

        rs_write = (~rob_full) & (~is_load_or_store)
        rs_modify_recorder = ~rob_empty & ready_array[head_ptr]

        # 把信息发送到 rs 中
        rs.async_called(
            rs_write = rs_write,
            rs_modify_recorder = rs_modify_recorder,
            rob_index = tail_ptr,
            signals = signals,
            rs1_value = rf_value_array[rs1],
            rs1_recorder = rf_recorder_array[rs1],
            rs1_has_recorder = rf_has_recorder_array[rs1],
            rs2_value = rf_value_array[rs2],
            rs2_recorder = rf_recorder_array[rs2],
            rs2_has_recorder = rf_has_recorder_array[rs2],
            addr = addr
        )

        with Condition(~rob_full):
            allocated_array[tail_ptr] = Bits(1)(1)
            ready_array[tail_ptr] = Bits(1)(0)
            is_branch_array[tail_ptr] = is_branch
            is_memory_write_array[tail_ptr] = is_memory_write
            is_reg_write_array[tail_ptr] = is_reg_write
            addr_array[tail_ptr] = addr
            ready_array[tail_ptr] = Bits(1)(0)
            tail[0] = updated_tail_ptr
            rob_size[0] = updated_rob_size

        rob_index_from_alu = rob_index_array_from_alu[0]
        modify_recorder = allocated_array[rob_index_from_alu]
        with Condition(modify_recorder):
            calc_result_array[rob_index_from_alu] = result_array_from_alu[0]
            pc_result_array[rob_index_from_alu] = pc_result_array_from_alu[0]
        

        with Condition(~rob_empty & ready_array[head_ptr]):
            log("ROB entry {} committed", head_ptr)
            # Need to be completed, commit entry and bypass the result to rs and lsq


        return rob_full 
