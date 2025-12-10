import os
import shutil

from assassyn.frontend import *
from assassyn.backend import *
from assassyn import utils

from decode_logic import *
from decoder import *
from fetcher import *
from opcodes import *
from PCMover import *

current_path = os.path.dirname(os.path.abspath(__file__))
workspace = f"{current_path}/.workspace/"

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

def build_cpu():
    init_workspace(f"{current_path}/workloads", "0to100")

    with open(f'{workspace}/workload.config') as f:
        raw = f.readline()
        raw = raw.replace('offset:', "'offset':").replace('data_offset:', "'data_offset':")
        offsets = eval(raw)
        value = hex(offsets['data_offset'])
        value = value[1:] if value[0] == '-' else value
        value = value[2:]
        open(f'{workspace}/workload.init', 'w').write(value)

    sys = SysBuilder("Tomasulo CPU")

    with sys:
        is_jump_or_branch = Bits(1)(0)
        is_default = Bits(1)(1)
        result = Bits(32)(0)
        fetch_valid = Bits(1)(0)
        predict_result = Bits(1)(0)
        decode_valid = Bits(1)(0)

        pcMover = PCMover()
        pc_reg = pcMover.build(
            is_jump_or_branch = is_jump_or_branch,
            is_default = is_default,
            result = result,
            fetch_valid = fetch_valid,
            predict_result = predict_result
            )
        
        decoder = Decoder()
        decode_valid = decoder.build()

        fetcher = Fetcher()
        fetch_valid = fetcher.build(
            pc_addr = pc_reg[0],
            decoder = decoder,
            decode_valid = decode_valid
        )
