from assassyn.frontend import *

class ROB(Module):

    def __init__(self):
        super().__init__(ports = {}, no_arbiter = True)

    