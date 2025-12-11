from assassyn.frontend import *
from opcodes import *
from instruction import *
from decode_logic import *
from ROB import *

class Decoder(Module):

    def __init__(self):
        super().__init__(ports = {
            "fetch_addr": Port(Bits(32))
        })
        self.name = "D"

    @module.combinational
    def build(self, rob: ROB, rdata: Array):
        fetch_addr = self.pop_all_ports(True)
        inst = rdata[0].bitcast(Bits(32))
        decode_valid = Bits(1)(1)

        log("raw: 0x{:08x}  | addr: 0x{:05x} | decode_valid: {}", inst, fetch_addr, decode_valid) # 正在解码的指令

        signals = decode_logic(inst)
        is_ebreak_type = (signals.alu == Bits(16)(1 << RV32I_ALU.ALU_NONE))

        with Condition(is_ebreak_type):
            log("ebreak")
            finish()

        rob.async_called(
            is_reg_write = signals.is_reg_write,
            is_memory_write = signals.is_memory_write,
            is_branch = signals.is_branch,
            rd = signals.rd,
            has_rd = signals.rd_valid,
            rs1 = signals.rs1,
            has_rs1 = signals.rs1_valid,
            rs2 = signals.rs2,
            has_rs2 = signals.rs2_valid,
            imm = signals.imm,
            has_imm = signals.imm_valid,
            addr = fetch_addr
        )

        return decode_valid

