from assassyn.frontend import *

def write1hot(arrs, index, value):
    for i, arr in enumerate(arrs):
        with Condition(index.bitcast(Bits(5)) == Bits(5)(i)):
            arr[0] = value

def read_mux(arrs, idx_val, size, width):
    return_value = Bits(width)(0)
    for i in range(size):
        return_value = (Bits(5)(i) == idx_val.bitcast(Bits(5))).select(arrs[i][0], return_value)
    return return_value