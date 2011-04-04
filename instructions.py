# ---------------------------------------------------------------------------- #
# The Instruction Constructs                                                   #
# ---------------------------------------------------------------------------- #
# add, sub, and, or, nor, slt;
# addi, andi, ori, slti
# beq, bne, j, jr
# lw, sw

class Instruction(object):
    def fetch(sim):
        pass
    
    def decode(sim):
        pass
    
    def execute(sim):
        pass
    
    def memory(sim):
        pass
    
    def write(sim):
        pass
    
    def __repr__(self):
        return str(self)

class RType(Instruction):
    def __init__(self, rd, rs, rt):
        self.rd = rd
        self.rs = rs
        self.rt = rt
    
    def __str__(self):
        return '%s %s, %s, %s' % (self.__class__.__name__, self.rd, self.rs, self.rt)

class Add(RType):
    def execute(sim):
        pass

class Sub(RType):
    pass

class And(RType):
    pass

class Or(RType):
    pass

class Nor(RType):
    pass

class Slt(RType):
    pass

class JR(RType):
    def __init__(self, rt):
        self.rt = rt



class IType(Instruction):
    def __init__(self, rt, rs, immediate):
        self.rt = rt
        self.rs = rs
        self.immediate = immediate
    
    def __str__(self):
        return '%s %s, %s, %s' % (self.__class__.__name__, self.rt, self.rs, self.immediate)

class AddI(IType):
    pass

class AndI(IType):
    pass

class OrI(IType):
    pass

class SltI(IType):
    pass

class Beq(IType):
    pass

class Bne(IType):
    pass

class LW(IType):
    pass

class SW(IType):
    pass



class JType(Instruction):
    def __init__(self, target):
        self.target = target
    
    def __str__(self):
        return '%s %s' % (self.__class__.__name__, self.target)

class J(JType):
    pass


supported_instructions = {
    'add':  Add,
    'sub':  Sub,
    'and':  And,
    'or':   Or,
    'nor':  Nor,
    'slt':  Slt,
    'addi': AddI,
    'andi': AndI,
    'ori':  OrI,
    'slti': SltI,
    'beq':  Beq,
    'bne':  Bne,
    'j':    J,
    'jr':   JR,
    'lw':   LW,
    'sw':   SW,
}

def parse_instruction(instruction_name, args):
    instruction_name = instruction_name.lower()
    if instruction_name not in supported_instructions:
        raise RuntimeError("The %s instruction is unsupported at this time." % instruction_name)
    
    return supported_instructions[instruction_name](*args)