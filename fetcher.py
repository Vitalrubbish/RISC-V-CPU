from assassyn.frontend import *
from decoder import *

class Fetcher(Module):

    def __init__(self):
        super().__init__(ports = {}, no_arbiter=True)
        self.name = "F"

    @module.combinational
    def build(self):
        pc_reg = RegArray(Bits(32), 1)
        addr = pc_reg[0]
        return pc_reg, addr

class FetcherImpl(Downstream):

    def __init__(self):
        super().__init__()
        self.name = "FI"

    @downstream.combinational
    def build(
        self,
        depth_log: int,
        pc_reg: Value,
        pc_addr: Value,
        decoder: Decoder,
        decode_valid_arr: Array,
        icache: SRAM
    ):
        decode_valid = decode_valid_arr[0]
        FD_buffer_size = RegArray(Bits(32), 1, initializer = [0])
        
        current_size = FD_buffer_size[0].bitcast(Int(32))
        fetch_valid = (current_size < Int(32)(3))

        log("fetch_valid : {} | decode_valid : {} | fetch_addr: 0x{:05x}", fetch_valid, decode_valid, pc_addr) # 是否抓取指令，正在抓取的指令地址是什么        

        delta = Int(32)(0)
        delta = (decode_valid).select(delta - Int(32)(1), delta)
        delta = (fetch_valid).select(delta + Int(32)(1), delta)
        
        next_size = current_size + delta
        FD_buffer_size[0] = next_size.bitcast(Bits(32))

        with Condition(fetch_valid):
            d_call = decoder.async_called(fetch_addr = pc_addr)
            d_call.bind.set_fifo_depth(fetch_addr = 3)
            pc_reg[0] = (pc_addr.bitcast(Int(32)) + Int(32)(4)).bitcast(Bits(32))
        with Condition(~fetch_valid):
            pc_reg[0] = pc_addr

        icache.build(Bits(1)(0), fetch_valid, pc_addr[2:2+depth_log - 1].bitcast(Int(depth_log)), Bits(32)(0))
        return fetch_valid

