from assassyn.frontend import *

class PCMover(Downstream):
    
    def __init__(self):
        super().__init__()
        self.name = "PC"

    @downstream.combinational
    def build(
        self,
        is_jump_or_branch: Value,
        is_default: Value,
        result: Value,                 # 传入类型：Bits(32)
        fetch_valid: Value,            # 决定是否需要抓取下一条指令
        predict_result: Value          # 类型：Bits(1), 1 代表预测会跳转，0 代表预测不会跳转
    ):
        pc_reg = RegArray(Bits(32), 1, initializer=[0]) # 在这里定义 pc 寄存器
        
        with Condition(~fetch_valid):
            pc_reg[0] = pc_reg[0]
        
        with Condition(fetch_valid & is_default):
            pc_reg[0] = (pc_reg[0].bitcast(Int(32)) + Int(32)(4)).bitcast(Bits(32)) # 如果是默认指令则直接加 4

        with Condition(fetch_valid & is_jump_or_branch & predict_result == Bits(1)(1)):
            pc_reg[0] = result # 如果预测会跳转则直接赋值为跳转后的位置

        with Condition(fetch_valid & is_jump_or_branch & predict_result == Bits(1)(0)):
            pc_reg[0] = (pc_reg[0].bitcast(Int(32)) + Int(32)(4)).bitcast(Bits(32)) # 如果预测不会跳转则直接加 4
            
        return pc_reg # 返回 pc 寄存器