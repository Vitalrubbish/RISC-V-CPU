from assassyn.frontend import *
from opcodes import *
from instruction import *
from decode_logic import *

class Decoder(Module):

    def __init__(self):
        super().__init__(ports = {
            "fetch_addr": Port(Bits(32))
        })
        self.name = "D"

    def build(self, ROB: Module, rdata: Array):
        fetch_addr = self.pop_all_ports(True)
        inst = rdata[0].bitcast(Bits(32))
        decode_valid = Bits(1)(1)

        log("raw: 0x{:08x}  | addr: 0x{:05x} |", inst, fetch_addr) # 正在解码的指令

        signals = decode_logic(inst)
        is_ebreak_type = (signals.alu == Bits(16) << RV32I_ALU.ALU_NONE)

        with Condition(is_ebreak_type):
            log("ebreak")
            finish()

        return decode_valid

