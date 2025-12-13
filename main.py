import os
import shutil

from assassyn.frontend import *
from assassyn.backend import *
from assassyn import utils

from decode_logic import *
from decoder import *
from fetcher import *
from opcodes import *
from ROB import *

current_path = os.path.dirname(os.path.abspath(__file__))
workspace = f"{current_path}/.workspace/"

class Driver(Module):
    
    def __init__(self):
        super().__init__(ports={})

    @module.combinational
    def build(self, fetcher: Module):
        init_reg = RegArray(UInt(1), 1, initializer=[1])
        # init_cache = SRAM(width = 32, depth = 32, init_file = f"{workspace}/workload.init")
        # init_cache.name = "init_cache"
        # init_cache.build(we = Bits(1)(0), re = init_reg[0].bitcast(Bits(1)), wdata = Bits(32)(0), addr = Bits(5)(0))

        with Condition(init_reg[0] == UInt(1)(1)):
            # user.async_called()
            init_reg[0] = UInt(1)(0)
        
        with Condition(init_reg[0] == UInt(1)(0)):
            d_call = fetcher.async_called()
        # return init_cache

def cp_if_exists(src, dst, required):
    if os.path.exists(src):
        shutil.copy(src, dst)
    elif required:
        raise FileNotFoundError(f"File {src} not found")

def init_workspace(base_path, case):
    if os.path.exists(f'{workspace}'):
        shutil.rmtree(f'{workspace}')
    os.mkdir(f'{workspace}')
    cp_if_exists(f'{base_path}/{case}.exe', f'{workspace}/workload.exe', False)
    cp_if_exists(f'{base_path}/{case}.data', f'{workspace}/workload.data', True)
    cp_if_exists(f'{base_path}/{case}.config', f'{workspace}/workload.config', False)
    cp_if_exists(f'{base_path}/{case}.sh', f'{workspace}/workload.sh', False)

def build_cpu(depth_log: int):
    init_workspace(f"{current_path}/workloads", "0to100")

    with open(f'{workspace}/workload.config') as f:
        raw = f.readline()
        raw = raw.replace('offset:', "'offset':").replace('data_offset:', "'data_offset':")
        offsets = eval(raw)
        value = hex(offsets['data_offset'])
        value = value[1:] if value[0] == '-' else value
        value = value[2:]
        open(f'{workspace}/workload.init', 'w').write(value)

    sys = SysBuilder("Tomasulo-CPU")

    with sys:
        # implementing register file
        rf_value = RegArray(Bits(32), 32)
        rf_recorder = RegArray(Bits(5), 32)
        rf_has_recorder = RegArray(Bits(1), 32)

        decode_valid = RegArray(Bits(1), 1)
        rob_full = RegArray(Bits(1), 1)

        icache = SRAM(width=32, depth = 1<<depth_log, init_file = f"{workspace}/workload.exe") # 存储指令
        icache.name = "icache"
        
        rob = ROB()
        rob.build(rob_full, rf_value_array = rf_value, rf_recorder_array = rf_recorder, rf_has_recorder_array = rf_has_recorder)

        decoder = Decoder()
        fetcher = Fetcher()
        fetcher_impl = FetcherImpl()

        pc_reg, pc_addr = fetcher.build()

        fetch_valid = fetcher_impl.build(
            depth_log = depth_log,
            pc_reg = pc_reg,
            pc_addr = pc_addr,
            decoder = decoder,
            decode_valid_arr = decode_valid,
            icache = icache
        )

        decoder.build(rob = rob, rdata = icache.dout, rob_full_array = rob_full, decode_valid_array = decode_valid)

        driver = Driver()
        driver.build(fetcher)
    
    print(sys)
    conf = config(
        verilog=utils.has_verilator(),
        sim_threshold=20,
        idle_threshold=20,
        resource_base='',
        fifo_depth=1,
    ) 

    simulator_path, verilog_path = elaborate(sys, **conf)

    raw = utils.run_simulator(simulator_path)
    with open(f'{workspace}/simulation.log', 'w') as f:
        f.write(raw)
    print(f"Simulation log saved to {workspace}/simulation.log")

depth_log = 16
if __name__ == "__main__":
    build_cpu(depth_log)