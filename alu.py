from assassyn.frontend import *
from instruction import *

class ALU(Module):

    def __init__(self):
        super().__init__(ports = {
            "rob_index": Bits(32),
            "alu_a": Bits(32),
            "alu_b": Bits(32),
            "calc_type": Bits(RV32I_ALU.CNT)
        })
        self.name = "ALU"

    @module.combinational
    def build(self):
        alu_a, alu_b, calc_type = self.pop_all_ports(True)

        results = [Bits(32)(0)] * RV32I_ALU.CNT

        adder_result = (alu_a.bitcast(Int(32)) + alu_b.bitcast(Int(32))).bitcast(Bits(32))
        le_result = (alu_a.bitcast(Int(32)) < alu_b.bitcast(Int(32))).select(Bits(32)(1), Bits(32)(0))
        eq_result = (alu_a == alu_b).select(Bits(32)(1), Bits(32)(0))
        leu_result = (alu_a < alu_b).select(Bits(32)(1), Bits(32)(0))
        sra_signed_result = (alu_a.bitcast(Int(32)) >> alu_b[0:4].bitcast(Int(5))).bitcast(Bits(32))
        sub_result = (alu_a.bitcast(Int(32)) - alu_b.bitcast(Int(32))).bitcast(Bits(32))

        results[RV32I_ALU.ALU_ADD] = adder_result
        results[RV32I_ALU.ALU_SUB] = sub_result
        results[RV32I_ALU.ALU_CMP_LT] = le_result
        results[RV32I_ALU.ALU_CMP_EQ] = eq_result
        results[RV32I_ALU.ALU_CMP_LTU] = leu_result
        results[RV32I_ALU.ALU_XOR] = alu_a ^ alu_b
        results[RV32I_ALU.ALU_OR] = alu_a | alu_b
        results[RV32I_ALU.ALU_ORI] = alu_a | alu_b
        results[RV32I_ALU.ALU_AND] = alu_a & alu_b
        results[RV32I_ALU.ALU_TRUE] = Bits(32)(1)
        results[RV32I_ALU.ALU_SLL] = alu_a << alu_b[0:4]
        results[RV32I_ALU.ALU_SRA] = sra_signed_result 
        results[RV32I_ALU.ALU_SRA_U] = alu_a >> alu_b[0:4]
        results[RV32I_ALU.ALU_NONE] = Bits(32)(0)

        alu = calc_type
        result = alu.select1hot(*results)

        
