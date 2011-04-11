from arguments import *

# ---------------------------------------------------------------------------- #
# The Instruction Constructs                                                   #
# ---------------------------------------------------------------------------- #
# add, sub, and, or, nor, slt;
# addi, andi, ori, slti
# beq, bne, j, jr
# lw, sw

def x_to_x(func):
    def wrapper(self, sim, *args, **kwargs):
        n_min1_stage = sim.stages[sim.stages.index('execute') - 1]

        if hasattr(self, 'rt') and self.rt == sim.pipeline[n_min1_stage].rd

class Instruction(object):
    def fetch(self, sim):
        pass
    
    def decode(self, sim):
        pass
    
    def execute(self, sim):
        pass
    
    def memory(self, sim):
        pass
    
    def write(self, sim):
        pass
    
    def destination(self):
        raise RuntimeError
    
    def name(self):
        return self.__class__.__name__
    
    def result(self):
        raise RuntimeError
    
    def __repr__(self):
        return str(self)

class RType(Instruction):
    format = [
        ('opcode', 6),
        ('rs', 5),
        ('rt', 5),
        ('rd', 5),
        ('sa', 5),
        ('function', 6)
    ]

    def __init__(self, rd, rs, rt):
        assert rd.is_register()
        assert rs.is_register()
        assert rt.is_register()
        self.opcode = 0
        self.rd = rd
        self.rs = rs
        self.rt = rt
        self.result = None
    
    def destination(self):
        return self.rd
    
    def result(self):
        return self.result
    
    def __str__(self):
        return '%s %s, %s, %s' % (self.name(), self.rd, self.rs, self.rt)

class Add(RType):
    def encode(self):
        out = 0
        for piece, size in format:
            pass

    def execute(self, sim):
        self.result = self.rd, sim.read_register(self.rs) + sim.read_register(self.rt)
        sim.results['execute'] = self.result
    
    def write(self, sim):
        sim.write_register(*self.rd)

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
        assert rt.is_register()
        self.rt = rt
    
    def __str__(self):
        return '%s %s' % (self.name(), self.rt)


class IType(Instruction):
    def __init__(self, rt, rs, immediate):
        assert rt.is_register()
        assert rs.is_register()
        assert immediate.is_immediate()
        self.rt = rt
        self.rs = rs
        self.immediate = immediate
    
    def __str__(self):
        return '%s %s, %s, %s' % (self.name(), self.rt, self.rs, self.immediate)

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

class MemIType(IType):
    def __init__(self, rt, offset):
        assert rt.is_register()
        assert offset.is_offset()
        self.rt = rt
        self.offset = offset
    
    def __str__(self):
        return '%s %s, %s' % (self.name(), self.rt, self.offset)

class LW(MemIType):
    pass

class SW(MemIType):
    pass



class JType(Instruction):
    def __init__(self, target):
        assert isinstance(target, Register)
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
    
    try:
        return supported_instructions[instruction_name](*args)
    except Exception, e:
        print 'Instruction parsing failed for %s' % instruction_name
        raise

def encode_instruction(instruction):
    if isinstance


def decode_instruction(n):
