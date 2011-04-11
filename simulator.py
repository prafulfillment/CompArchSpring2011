from instructions import *

# ---------------------------------------------------------------------------- #
# The Simulator and Helper Functions                                           #
# ---------------------------------------------------------------------------- #

BASE_MEMORY = 0x1000

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
        self.instruction_count = 0
        self.cycle_count = 0
        self.stages = 'fetch', 'decode', 'execute', 'memory', 'write'
        self.pipeline = {}
        self.results = {}
        for stage in self.stages:
            self.pipeline[stage] = None
            self.results[stage] = None
        
        self.reset_memory()
    
    def reset_memory(self):
        self.memory_data = [0 for _ in xrange(BASE_MEMORY >> 2)]
    
    @addr_check
    def read_word(self, addr):
        return self.memory_data[addr]
    
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
        
        while addr >= len(self.memory_data):
            self.memory_data.append(0)

        self.memory_data[addr] = word
    
    def memory_size(self):
        return len(self.memory_data) << 2
    
    def flush_after(self, from_stage):
        for stage in self.stages[self.stages.index(from_stage)+1:]:
            print 'Flushing %s' % self.pipeline[stage]
            self.pipeline[stage] = self.results[stage] = None
            self.pc -= 4
    
    def flush_before(self, from_stage):
        for stage in self.stages[:self.stages.index(from_stage)]:
            print 'Flushing %s' % self.pipeline[stage]
            self.pipeline[stage] = self.results[stage] = None
            self.pc -= 4
    
    def jump_to(self, addr):
        print 'Jumping to 0x%x' % addr
        self.pc = addr
    
    def jump_relative_to(self, addr):
        print 'Jumping relative to 0x%x' % addr
        self.pc += addr
        print 'PC is now %x' % self.pc
    
    def load(self, instructions):
        for idx, instruction in enumerate(instructions):
            addr = idx * 4 + BASE_MEMORY
            self.write_word(addr, instruction)
    
    def run(self, start_pc=BASE_MEMORY):
        print 'Run'
        self.instruction_count = 0
        self.cycle_count = 0
        self.pc = start_pc
        while self.pc == BASE_MEMORY or any(self.pipeline[stage] is not None for stage in self.pipeline):
            #BASE_MEMORY <= self.pc <= self.memory_size():
            self.cycle()
            self.pc += 4
            print hex(self.pc), self.registers
        
        print 'Execution finished'
        print '%d instructions were run in %d cycles' % (self.instruction_count, self.cycle_count)
        print self.registers
    
    def cycle(self):
        print '=' * 40, 'NEW CYCLE', '=' * 40
        self.cycle_count += 1
        for stage in self.stages:
            self.do_stage(stage)

    def do_stage(self, stage):
        if stage not in self.stages:
            raise RuntimeError("Invalid stage: %s" % stage)
        
        getattr(self, stage)()

    def fetch(self):
        for idx, stage in reversed(list(enumerate(self.stages))):
            if idx > 0:
                instruction = self.pipeline[self.stages[idx - 1]]
                if instruction is not None:
                    print 'Moved %s from %s to %s' % (instruction, self.stages[idx - 1], stage)
                self.pipeline[stage] = instruction
                self.results[stage] = self.results[self.stages[idx - 1]]

        if BASE_MEMORY <= self.pc < self.memory_size():
            self.pipeline['fetch'] = self.read_word(self.pc)
            print 'Fetched new instruction: %s' % self.pipeline['fetch']
        else:
            self.pipeline['fetch'] = None
        self.results['fetch'] = None
    
    def decode(self):
        if self.pipeline['decode'] is not None:
            print '-' * 30, 'decode stage for %s' % self.pipeline['decode'], '-' * 30
            self.pipeline['decode'].decode(self)
    
    def execute(self):
        if self.pipeline['execute'] is not None:
            print '-' * 30, 'execute stage for %s' % self.pipeline['execute'], '-' * 30
            self.pipeline['execute'].execute(self)
    
    def memory(self):
        if self.pipeline['memory'] is not None:
            print '-' * 30, 'memory stage for %s' % self.pipeline['memory'], '-' * 30
            self.pipeline['memory'].memory(self)
    
    def write(self):
        if self.pipeline['write'] is not None:
            print '-' * 30, 'write stage for %s' % self.pipeline['write'], '-' * 30
            self.pipeline['write'].write(self)
            self.instruction_count += 1
    
    #@decode_register
    def write_register(self, register, data):
        if register == 0:
            return
        
        print 'Writing %s to register %d' % (data, register)
        self.registers[register] = data
    
    #@decode_register
    def read_register(self, register):
        print 'Reading register %d' % register
        return self.registers[register]
