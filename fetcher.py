from assassyn.frontend import *
from decoder import *

class Fetcher(Module):

    def __init__(self):
        super().__init__(ports = {}, no_arbiter = True)
        self.name = "F"

    @module.combinational
    def build(
        self,
        pc_addr: Value,
        decoder: Decoder,
        decode_valid: Value
    ):
        FD_buffer_size = RegArray(Bits(32), 1, initializer = [0])
        
        with Condition(decode_valid):
            FD_buffer_size[0] = (FD_buffer_size[0].bitcast(Int(32)) - Int(32)(1)).bitcast(Bits(32))
        with Condition(~decode_valid):
            FD_buffer_size[0] = FD_buffer_size[0]

        fetch_valid = (FD_buffer_size[0] < 5)

        log("fetch_valid : {} | fetch_addr: {}", fetch_valid, pc_addr) # 是否抓取指令，正在抓取的指令地址是什么

        with Condition(fetch_valid):
            decoder.async_called(pc_addr)
            FD_buffer_size[0] = (FD_buffer_size[0].bitcast(Int(32)) + Int(32)(1)).bitcast(Bits(32))
        with Condition(~fetch_valid):
            FD_buffer_size[0] = FD_buffer_size[0]
        
        return fetch_valid

