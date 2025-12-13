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
    def build(self, rob: ROB, rdata: Array, rob_full_array: Array, decode_valid_array: Array):
        fetch_addr = self.pop_all_ports(True)
        inst = rdata[0].bitcast(Bits(32))

        decode_valid = ~rob_full_array[0]
        decode_valid_array[0] = decode_valid

        log("raw: 0x{:08x}  | addr: 0x{:05x} | decode_valid: {}", inst, fetch_addr, decode_valid) # 正在解码的指令

        signals = decode_logic(inst)
        is_ebreak_type = (signals.alu == Bits(16)(1 << RV32I_ALU.ALU_NONE))

        # with Condition(is_ebreak_type):
        #    log("ebreak")
        #    finish()

        with Condition(decode_valid):
            rob.async_called(
                signals = signals,
                addr = fetch_addr,
            )

        return decode_valid

