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

        #if sim.pipeline[n_min1_stage] is not None and \
        #   any(item == sim.pipeline[n_min1_stage].destination()
        #       for item in self.source()):
        #    self.forwarded = None
        #else:
        self.forwarded = None
        dest_register, dest_value = sim.results['execute']
        print 'X->X Checking forwarding', dest_register, self.source()

        if dest_register.is_register() and \
           dest_register.register_number != 0 and \
           dest_register in self.source():
            print 'Forwarding enabled'
            self.forwarded = dest_register, dest_value
        return func(self, sim, *args, **kwargs)
    return wrapper

def accept_forwarding(func):
    def wrapper(self, *args, **kwargs):
        print '%s accepting forwarding' % self
        if self.forwarded is not None:
            forwarded_register, forwarded_value = self.forwarded
            
            old_values = {}
            for source in self.source():
                if source == forwarded_register:
                    old_values[source] = source.value
                    source.value = lambda sim: forwarded_value
                    print 'Rewriting register %s to return %d' % (source, forwarded_value)
            
            return_value = func(self, *args, **kwargs)
            
            for source in old_values:
                source.value = old_values[source]
            
            return return_value
        
        return func(self, *args, **kwargs)
    return wrapper


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
        if self.destination() is not None:
            print self.result()
            dest_register, value = self.result()
            dest_register.write(sim, value)
    
    def source(self):
        raise RuntimeError

    def destination(self):
        raise RuntimeError
    
    def put_result(self, sim, result):
        print 'Putting result,', result
        self._result = self.destination(), result
        sim.results['execute'] = self.result()
    
    def name(self):
        return self.__class__.__name__
    
    def result(self):
        if hasattr(self, '_result'):
            return self._result
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
        self._result = None
    
    def source(self):
        return self.rs, self.rt

    def destination(self):
        return self.rd
    
    def result(self):
        return self._result
    
    def __str__(self):
        return '%s %s, %s, %s' % (self.name(), self.rd, self.rs, self.rt)

class Add(RType):
    def encode(self):
        out = 0
        for piece, size in format:
            pass

    @x_to_x
    @accept_forwarding
    def execute(self, sim):
        self.put_result(sim, self.rs.value(sim) + self.rt.value(sim))

class Sub(RType):
    @x_to_x
    @accept_forwarding
    def execute(self, sim):
        self.put_result(sim, self.rs.value(sim) - self.rt.value(sim))

class And(RType):
    @x_to_x
    @accept_forwarding
    def execute(self, sim):
        self.put_result(sim, self.rs.value(sim) & self.rt.value(sim))

class Or(RType):
    @x_to_x
    @accept_forwarding
    def execute(self, sim):
        self.put_result(sim, self.rs.value(sim) | self.rt.value(sim))

class Nor(RType):
    @x_to_x
    @accept_forwarding
    def execute(self, sim):
        self.put_result(sim, ~(self.rs.value(sim) | self.rt.value(sim)))

class Slt(RType):
    @x_to_x
    @accept_forwarding
    def execute(self, sim):
        self.put_result(sim, int(self.rs.value(sim) < self.rt.value(sim)))

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
        self._result = None
    
    def source(self):
        return self.rs, self.immediate

    def destination(self):
        return self.rt
    
    def __str__(self):
        return '%s %s, %s, %s' % (self.name(), self.rt, self.rs, self.immediate)

class AddI(IType):
    def execute(self, sim):
        self.put_result(sim, self.rs.value(sim) + self.immediate.value(sim))


class AndI(IType):
    pass

class OrI(IType):
    pass

class SltI(IType):
    pass

class Beq(IType):
    def destination(self):
        return None

class Bne(IType):
    def destination(self):
        return None

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