from instructions import *

# ---------------------------------------------------------------------------- #
# The Simulator and Helper Functions                                           #
# ---------------------------------------------------------------------------- #

def decode_register(func):
    """ Decorator for simulator functions that take a register in.  Decodes the
    register into a register number.
    """
    def wrapper(self, register, *args, **kwargs):
        original_register = register

        while register in self.register_map:
            register = self.register_map[register]
        
        if 0 <= register < 32:
            return func(self, register_number, *args, **kwargs)
        else:
            raise RuntimeError('Invalid register given: %s' % original_register)
    return wrapper

def addr_check(func):
    def wrapper(self, addr, *args, **kwargs):
        if addr & 0x3 != 0:
            raise RuntimeError("Can't access memory at a non-word boundary.")
        return func(self, addr >> 2, *args, **kwargs)
    return wrapper

class Simulator(object):
    def __init__(self):
        self.pc = None
        self.registers = [0 for x in xrange(32)]
        
        #self.instructions = None
        self.stages = 'fetch', 'decode', 'execute', 'memory', 'write'
        self.results = {}
        self.reset_memory()
    
    def reset_memory(self):
        self.memory = [0 for _ in xrange(0x1000 >> 2)]
    
    @addr_check
    def read_word(self, addr):
        return self.memory[addr]
    
    @addr_check
    def write_word(self, addr, word):
        if not isinstance(word, (int, long, Instruction, str)):
            raise RuntimeError("Can't put item of type %s into memory." % type(word))
        elif isinstance(word, str) and len(word) > 4:
            raise RuntimeError("Words are only 4 bytes long.  Can't accept a word of length %d." % len(word))
        elif isinstance(word, str):
            value = 0
            for char in word:
                value *= 256
                value += ord(char)
            word = value
        
        while addr >= len(self.memory):
            self.memory.append(0)

        self.memory[addr] = word
    
    def memory_size(self):
        return len(self.memory) << 2
    
    def load(self, instructions):
        for idx, instruction in enumerate(instructions):
            addr = idx * 4 + 0x1000
            self.write_word(instruction)
    
    def run(self):
        self.pc = 0x1000

    def do_stage(self, stage):
        if stage not in self.stages:
            raise RuntimeError("Invalid stage: %s" % stage)
        
        getattr(self, stage)()

    def fetch(self):
        pass
    
    def decode(self):
        pass
    
    def execute(self):
        pass
    
    def memory(self):
        pass
    
    def write(self):
        pass
    
    #@decode_register
    def write_register(self, register, data):
        if register == 0:
            return
        
        self.registers[register] = data
    
    #@decode_register
    def read_register(self, register):
        return self.registers[register]