from arguments import *

# ---------------------------------------------------------------------------- #
# The Instruction Constructs                                                   #
# ---------------------------------------------------------------------------- #
# add, sub, and, or, nor, slt;
# addi, andi, ori, slti
# beq, bne, j, jr
# lw, sw

def init_forwarding(func):
    def wrapper(self, *args, **kwargs):
        self.forwarded = {}
        return func(self, *args, **kwargs)
    return wrapper

def x_to_x(func):
    def wrapper(self, sim, *args, **kwargs):
        if sim.verbose: 'X->X %s' % self
        if sim.results['memory'] is not None:
            n_min1_stage = sim.stages[sim.stages.index('execute') - 1]

            dest_register, dest_value = sim.results['memory']
            if sim.verbose:  'X->X Checking forwarding'

            if dest_register.is_register() and \
               dest_register.register_number != 0 and \
               dest_register in self.source() and \
               dest_register not in self.forwarded:
                if sim.verbose:  'X->X Forwarding enabled for %s' % self
                self.forwarded[dest_register] = dest_value
                #self.forwarded = sim.results['execute']
        return func(self, sim, *args, **kwargs)
    wrapper.__name__ = 'x-to-x-wrapper'
    return wrapper

def m_to_x(func):
    def wrapper(self, sim, *args, **kwargs):
        if sim.results['write'] is not None:
            if sim.verbose:  'Checking M->X'
            #n_min2_stage = sim.stages[sim.stages.index('execute') + 2]

            dest_register, dest_value = sim.results['write']

            if dest_register.is_register() and \
               dest_register.register_number != 0 and \
               dest_register in self.source() and \
               dest_register not in self.forwarded:
                if sim.verbose:  'M->X Forwarding enabled for %s' % self
                #self.forwarded = sim.results['memory']
                self.forwarded[dest_register] = dest_value
            if sim.verbose:  self.forwarded
            
        return func(self, sim, *args, **kwargs)
    return wrapper

def m_to_m(func):
    def wrapper(self, sim, *args, **kwargs):
        if sim.results['write'] is not None:
            if sim.verbose:  'Checking M->M'
            n_min1_stage = sim.stages[sim.stages.index('memory') + 1]

            dest_register, dest_value = sim.results['write']

            if dest_register.is_register() and \
               dest_register.register_number != 0 and \
               dest_register in self.source() and \
               isinstance(sim.pipeline[n_min1_stage], LW):
                if sim.verbose:  'M->M Forwarding enabled for %s' % self
                #self.forwarded = sim.results['memory']
                self.forwarded[dest_register] = dest_value
            if sim.verbose:  self.forwarded
            
        return func(self, sim, *args, **kwargs)
    return wrapper

def accept_forwarding(func):
    def wrapper(self, sim, *args, **kwargs):
        for stage in sim.stages[sim.stages.index(sim.current_stage) + 1:-1]:
            instruction = sim.pipeline[stage]
            if instruction is None: continue
            if instruction.destination() in self.source() and instruction.destination() not in self.forwarded:
                if sim.verbose:  'STALLING!'
                sim.stall(sim.current_stage)
                return None


        if sim.verbose:  '%s accepting forwarding' % self
        if hasattr(self, 'forwarded') and self.forwarded is not None:
            old_values = {}
            if sim.verbose:  self.forwarded
            for forwarded_register in self.forwarded:
                for source in self.source():
                    if sim.verbose:  source, forwarded_register
                    if source == forwarded_register:
                        old_values[source] = source.value
                        source.value = lambda sim, forwarded_register=forwarded_register: self.forwarded[forwarded_register]
                        if sim.verbose:  'Rewriting register %s to return %d' % (source, self.forwarded[forwarded_register])
                        #break
            
            return_value = func(self, sim, *args, **kwargs)
            
            for source in old_values:
                source.value = old_values[source]
            
            return return_value
        
        return func(self, sim, *args, **kwargs)
    return wrapper

def forwarding(func):
    return init_forwarding(x_to_x(m_to_x(accept_forwarding(func))))

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
            if sim.verbose:  'result:', self.result()
            dest_register, value = self.result()
            dest_register.write(sim, value)
    
    def source(self):
        raise RuntimeError

    def destination(self):
        raise RuntimeError
    
    def put_result(self, sim, result, stage='execute'):
        if sim.verbose:  'Putting result,', result
        self._result = self.destination(), result
        sim.results[stage] = self.result()
    
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

    @forwarding
    def execute(self, sim):
        self.put_result(sim, self.rs.value(sim) + self.rt.value(sim))

class Sub(RType):
    @forwarding
    def execute(self, sim):
        self.put_result(sim, self.rs.value(sim) - self.rt.value(sim))

class And(RType):
    @forwarding
    def execute(self, sim):
        self.put_result(sim, self.rs.value(sim) & self.rt.value(sim))

class Or(RType):
    @forwarding
    def execute(self, sim):
        self.put_result(sim, self.rs.value(sim) | self.rt.value(sim))

class Nor(RType):
    @forwarding
    def execute(self, sim):
        self.put_result(sim, ~(self.rs.value(sim) | self.rt.value(sim)))

class Slt(RType):
    @forwarding
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
    
    @forwarding
    def execute(self, sim):
        sim.jump_to(self.rt.value(sim))
        sim.flush_before('execute')
    
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
    @forwarding
    def execute(self, sim):
        self.put_result(sim, self.rs.value(sim) + self.immediate.value(sim))

class SubI(IType):
    @forwarding
    def execute(self, sim):
        self.put_result(sim, self.rs.value(sim) - self.immediate.value(sim))

class AndI(IType):
    @forwarding
    def execute(self, sim):
        self.put_result(sim, self.rs.value(sim) + self.immediate.value(sim))

class OrI(IType):
    @forwarding
    def execute(self, sim):
        self.put_result(sim, self.rs.value(sim) + self.immediate.value(sim))

class SltI(IType):
    @forwarding
    def execute(self, sim):
        self.put_result(sim, self.rs.value(sim) + self.immediate.value(sim))

class Beq(IType):
    @forwarding
    def execute(self, sim):
        if self.rs.value(sim) == self.rt.value(sim):
            sim.jump_relative_to(self.immediate.value(sim) << 2)
            sim.flush_before('execute')

    def destination(self):
        return None
    
    def source(self):
        return self.rs, self.rt

class Bne(IType):
    @forwarding
    def execute(self, sim):
        if self.rs.value(sim) != self.rt.value(sim):
            sim.jump_relative_to(self.immediate.value(sim) << 2)
            sim.flush_before('execute')

    def destination(self):
        return None
    
    def source(self):
        return self.rs, self.rt

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
        return [self.offset.offset_from]
    
    @init_forwarding
    @x_to_x
    @m_to_x
    def execute(self, sim):
        pass

    @accept_forwarding
    def memory(self, sim):
        self.put_result(sim, sim.read_word(self.offset.value(sim)), stage='memory')

class SW(MemIType):
    def destination(self):
        return None
    
    def source(self):
        return [self.rt]
    
    @init_forwarding
    @x_to_x
    @m_to_x
    def execute(self, sim):
        pass

    @m_to_m
    @accept_forwarding
    def memory(self, sim):
        sim.write_word(self.offset.value(sim), self.rt.value(sim))

class JType(Instruction):
    def __init__(self, target):
        assert target.is_immediate()
        self.target = target
    
    def __str__(self):
        return '%s %s' % (self.__class__.__name__, self.target)

class J(JType):
    def destination(self):
        return None
    
    def source(self):
        return (self.target,)
    
    def execute(self, sim):
        sim.jump_to(self.target.value(sim))
        sim.flush_before('execute')



supported_instructions = {
    'add':  Add,
    'sub':  Sub,
    'and':  And,
    'or':   Or,
    'nor':  Nor,
    'slt':  Slt,
    'addi': AddI,
    'subi': SubI,
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
        if sim.verbose:  'Instruction parsing failed for %s' % instruction_name
        raise

def encode_instruction(instruction):
    pass


def decode_instruction(n):
    pass
