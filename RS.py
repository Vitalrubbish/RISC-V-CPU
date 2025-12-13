from assassyn.frontend import *
from instruction import *
from alu import *

RS_SIZE = 5

class RS(Module):

    def __init__(self):
        super().__init__(
            ports = {
                "rs_write": Port(Bits(1)),
                "rs_modify_recorder": Port(Bits(1)),
                "rob_index": Port(Bits(5)),                # 当前这个 entry 在 rs 中的下标
                "signals": Port(decoder_signals),
                "rs1_value": Port(Bits(32)),
                "rs1_recorder": Port(Bits(5)),
                "rs1_has_recorder": Port(Bits(1)),
                "rs2_value": Port(Bits(32)),
                "rs2_recorder": Port(Bits(5)),
                "rs2_has_recorder": Port(Bits(1)),
                "addr": Port(Bits(32)),                    # 计算对应的指令的地址
                # 先保留这些，后面一定会添加更多的端口
            }
        )
        self.name = "RS"

    @module.combinational
    def build(self, alu: ALU):
        # RS 自身的性质
        allocated_array = RegArray(Bits(1), RS_SIZE)          # RS 中这一条有没有分配指令


        # 传入的端口对应的寄存器数组
        rob_index_array = RegArray(Bits(5), RS_SIZE)
        rs1_array = RegArray(Bits(5), RS_SIZE)
        rs1_value_array = RegArray(Bits(32), RS_SIZE)
        has_rs1_array = RegArray(Bits(1), RS_SIZE)
        rs2_array = RegArray(Bits(5), RS_SIZE)
        rs2_value_array = RegArray(Bits(32), RS_SIZE)
        has_rs2_array = RegArray(Bits(1), RS_SIZE)  
        rs1_recorder_array = RegArray(Bits(5), RS_SIZE)
        has_rs1_recorder_array = RegArray(Bits(1), RS_SIZE)
        rs2_recorder_array = RegArray(Bits(5), RS_SIZE)
        has_rs2_recorder_array = RegArray(Bits(1), RS_SIZE)
        imm_array = RegArray(Bits(32), RS_SIZE)
        has_imm_array = RegArray(Bits(1), RS_SIZE)
        alu_type_array = RegArray(Bits(RV32I_ALU.CNT), RS_SIZE)
        cond_array = RegArray(Bits(RV32I_ALU.CNT), RS_SIZE)
        flip_array = RegArray(Bits(1), RS_SIZE)
        is_branch_array = RegArray(Bits(1), RS_SIZE)
        addr_array = RegArray(Bits(32), RS_SIZE)
                                  
        (
            rs_write,
            rs_modify_recorder,
            rob_index,
            signals,
            rs1_value,
            rs1_recorder,
            rs1_has_recorder,
            rs2_value,
            rs2_recorder,
            rs2_has_recorder,
            addr
        ) = self.pop_all_ports(True)

        allocated = allocated[rob_index].select(Bits(1), Bits(0))

        with Condition(rs_write & ~allocated):
            log("RS entry {} allocated", rob_index)
            rob_index_array[rob_index] = rob_index
            rs1_array[rob_index] = signals.rs1
            has_rs1_array[rob_index] = signals.rs1_valid
            rs1_value_array[rob_index] = rs1_value
            rs2_array[rob_index] = signals.rs2
            has_rs2_array[rob_index] = signals.rs2_valid
            rs2_value_array[rob_index] = rs2_value
            rs1_recorder_array[rob_index] = rs1_recorder
            has_rs1_recorder_array[rob_index] = rs1_has_recorder
            rs2_recorder_array[rob_index] = rs2_recorder
            has_rs2_recorder_array[rob_index] = rs2_has_recorder
            imm_array[rob_index] = signals.imm
            has_imm_array[rob_index] = signals.imm_valid
            alu_type_array[rob_index] = signals.alu
            addr_array[rob_index] = addr
            cond_array[rob_index] = signals.cond
            flip_array[rob_index] = signals.flip
            is_branch_array[rob_index] = signals.is_branch
            allocated_array[rob_index] = Bits(1)(1)

        send_index = Bits(5)(0)
        send = Bits(1)(0)
        for i in range(RS_SIZE):
            allocated = allocated_array[i].select(Bits(1), Bits(0))
            rs1_valid = (~has_rs1_array[i]) | (has_rs1_array[i] & (~has_rs1_recorder_array[i]))
            rs2_valid = (~has_rs2_array[i]) | (has_rs2_array[i] & (~has_rs2_recorder_array[i]))
            valid = allocated & rs1_valid & rs2_valid
            send_index = ((~send) & valid).select(Bits(5)(i), send_index)
            send = valid.select(Bits(1)(1), Bits(1)(0))

        a = (rs1_array[send_index] == Bits(5)(0)).select(Bits(32)(0), rs1_value_array[send_index])
        b = (rs2_array[send_index] == Bits(5)(0)).select(Bits(32)(0), rs2_value_array[send_index])

        alu_a = (signals.is_offset_br | signals.is_pc_calc).select(addr_array[send_index], a)
        alu_b = signals.imm_valid.select(signals.imm, b)

        with Condition(send):
            # 这里需要实现把已经准备好的第一条指令送去 alu 执行
            alu.async_called(
                rob_index = rob_index_array[send_index],
                alu_a = alu_a,
                alu_b = alu_b,
                cond = cond_array[send_index],
                flip = flip_array[send_index],
                is_branch = is_branch_array[send_index],
                calc_type = alu_type_array[send_index]
            )
            allocated_array[send_index] = Bits(1)(0)