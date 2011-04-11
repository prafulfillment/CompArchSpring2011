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

        if any(item == sim.pipeline[n_min1_stage].destination()
               for item in self.source()):
            self.forwarded = None
        else:
            self.forwarded = {}
            dest_register, dest_value = sim.results['execute']
            if dest_register.is_register() and \
               dest_register.register_number != 0 and \
               dest_register in self.source():
                self.forwarded[item.register_number] = dest_value
        else:
            self.forwarded = None


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
    
    def source(self):
        raise RuntimeError

    def destination(self):
        raise RuntimeError
    
    def put_result(self, sim, result):
        self.result = self.destination(), result
        sim.results['execute'] = self.result
    
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
    
    def source(self):
        return self.rs, self.rt

    def destination(self):
        return self.rd
    
    def result(self):
        return self.result
    
    def write(self, sim):
        sim.write_register(*self.result)
    
    def __str__(self):
        return '%s %s, %s, %s' % (self.name(), self.rd, self.rs, self.rt)

class Add(RType):
    def encode(self):
        out = 0
        for piece, size in format:
            pass

    def execute(self, sim):
        self.put_result(self.rs.value(sim) + self.rt.value(sim))

class Sub(RType):
    def execute(self, sim):
        self.put_result(self.rs.value(sim) - self.rt.value(sim))

class And(RType):
    def execute(self, sim):
        self.put_result(self.rs.value(sim) & self.rt.value(sim))

class Or(RType):
    def execute(self, sim):
        self.put_result(self.rs.value(sim) | self.rt.value(sim))

class Nor(RType):
    def execute(self, sim):
        self.put_result(~(self.rs.value(sim) | self.rt.value(sim)))

class Slt(RType):
    def execute(self, sim):
        self.put_result(int(self.rs.value(sim) < self.rt.value(sim)))

class JR(RType):
    def __init__(self, rt):
        assert rt.is_register()
        self.rt = rt
    
    def source(self):
        return (self.rt,)

    def destination(self):
        return None
    
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
    
    def source(self):
        return self.rs, self.immediate

    def destination(self):
        return self.rt
    
    def __str__(self):
        return '%s %s, %s, %s' % (self.name(), self.rt, self.rs, self.immediate)

class AddI(IType):
    def execute(self, sim):
        self.put_result(self.rs.value(sim) + self.immediate.value(sim))

class AndI(IType):
    def execute(self, sim):
        self.put_result(self.rs.value(sim) & self.immediate.value(sim))

class OrI(IType):
    def execute(self, sim):
        self.put_result(self.rs.value(sim) | self.immediate.value(sim))

class SltI(IType):
    def execute(self, sim):
        self.put_result(self.rs.value(sim) < self.immediate.value(sim))

class Beq(IType):
    def destination(self):
        return None

    def execute(self, sim):
        if self.rs.value(sim) == self.rt.value(sim):
            sim.pc += 4 * self.immediate.value(sim)

class Bne(IType):
    def destination(self):
        return None

    def execute(self, sim):
        if not self.rs.value(sim) == self.rt.value(sim):
            sim.pc += 4 * self.immediate.value(sim)

class MemIType(IType):
    def __init__(self, rt, offset):
        assert rt.is_register()
        assert offset.is_offset()
        self.rt = rt
        self.offset = offset

    def __str__(self):
        return '%s %s, %s' % (self.name(), self.rt, self.offset)

class LW(MemIType):
    def destination(self):
        return self.rt
    
    def source(self):
        return [self.offset]

class SW(MemIType):
    def destination(self):
        return None
    
    def source(self):
        return [self.rt]

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
    pass

def decode_instruction(n):
    pass
