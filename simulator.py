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

class EventDispatcher(object):
    def __init__(self):
        self.events = {}
    
    def add_event(self, event):
        if event in self.events:
            raise RuntimeError("Event %s already exists" % event)
        
        self.events[event] = []
    
    def remove_event(self, event):
        if event not in self.events:
            raise RuntimeError("No such event: %s" % event)

        del self.events[event]
    
    def add_handler(self, event, handler):
        if event not in self.events:
            raise RuntimeError("No such event: %s" % event)

        self.events[event].append(handler)
    
    def remove_handler(self, handler):
        for event in self.events:
            while handler in self.events[event]:
                self.events[event].remove(handler)

    def fire_event(self, event, *args, **kwargs):
        if event not in self.events:
            raise RuntimeError("No such event: %s" % event)
        
        [handler(*args, **kwargs) for handler in self.events[event]]


class Simulator(EventDispatcher):
    def __init__(self, verbose=False):
        super(Simulator, self).__init__()
        
        self.add_event('on-cycle')

        self.verbose = verbose
        self.pc = None
        self.registers = [0 for x in xrange(32)]
        
        #self.instructions = None
        self.instruction_count = 0
        self.cycle_count = 0
        self.stages = 'fetch', 'decode', 'execute', 'memory', 'write'
        self.pipeline = {}
        self.results = {}
        self.__stall = None
        for stage in self.stages:
            self.pipeline[stage] = None
            self.results[stage] = None
        
        self.reset_memory()
    
    def stall(self, stage):
        self.__stall = stage
    
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
            if self.verbose: print 'Flushing %s' % self.pipeline[stage]
            self.pipeline[stage] = self.results[stage] = None
            self.pc -= 4
    
    def flush_before(self, from_stage):
        for stage in self.stages[:self.stages.index(from_stage)]:
            if self.verbose: print 'Flushing %s' % self.pipeline[stage]
            self.pipeline[stage] = self.results[stage] = None
            self.pc -= 4
    
    def jump_to(self, addr):
        if self.verbose: print 'Jumping to 0x%x' % addr
        self.pc = addr + 4
    
    def jump_relative_to(self, addr):
        if self.verbose: print 'Jumping 0x%x relative to 0x%x' % (addr, self.pc)
        self.pc += addr
        if self.verbose: print 'PC is now %x' % self.pc
    
    def load(self, instructions):
        for idx, instruction in enumerate(instructions):
            addr = idx * 4 + BASE_MEMORY
            self.write_word(addr, instruction)
    
    def run(self, start_pc=BASE_MEMORY):
        if self.verbose: print 'Run'
        self.instruction_count = 0
        self.cycle_count = 0
        self.pc = start_pc
        while self.pc == BASE_MEMORY or any(self.pipeline[stage] is not None for stage in self.pipeline):
            #BASE_MEMORY <= self.pc <= self.memory_size():
            self.cycle()
            #if self.pipeline['fetch'] is not None:
            self.pc += 4
            if self.verbose: print hex(self.pc), self.registers
        
        print 'Execution finished'
        print '%d instructions were run in %d cycles' % (self.instruction_count, self.cycle_count)
        print self.registers
        print '[', ' '.join(['0x%x' % r for r in self.registers]), ']'
    
    def cycle(self):
        if self.verbose: print '=' * 40, 'NEW CYCLE', '=' * 40
        for stage in self.stages:
            self.current_stage = stage
            self.do_stage(stage)
        
        if any(self.pipeline[stage] is not None for stage in self.stages):
            self.cycle_count += 1
        
        self.fire_event('on-cycle', self)
        
        if self.verbose: print 'Cycle count is now %d' % self.cycle_count
    
    def simple_run(self, start_pc=BASE_MEMORY):
        self.pc = start_pc
        while BASE_MEMORY <= self.pc < self.memory_size():
            self.simple_cycle()
            if self.verbose: print hex(self.pc), self.registers
            self.pc += 4

    def simple_cycle(self):
        if self.verbose: print '=' * 40, 'NEW CYCLE', '=' * 40
        instruction = self.read_word(self.pc)
        if self.verbose: print 'Executing %s' % instruction
        for stage in self.stages:
            getattr(instruction, stage)(self)

    def do_stage(self, stage):
        if stage not in self.stages:
            raise RuntimeError("Invalid stage: %s" % stage)
        
        getattr(self, stage)()

    def fetch(self):
        for idx, stage in reversed(list(enumerate(self.stages))):
            if stage == self.__stall:
                self.__stall = None
                #self.pipeline[stage] = None
                print 'Stalling pipeline at %s' % stage
                print 'New pipeline: %s' % self.pipeline
                return
            
            if idx > 0:
                instruction = self.pipeline[self.stages[idx - 1]]
                if instruction is not None:
                    if self.verbose: print 'Moved %s from %s to %s' % (instruction, self.stages[idx - 1], stage)
                self.pipeline[stage] = instruction
                self.results[stage] = self.results[self.stages[idx - 1]]


        if BASE_MEMORY <= self.pc < self.memory_size():
            self.pipeline['fetch'] = self.read_word(self.pc)
            if self.verbose: print 'Fetched new instruction from address 0x%x: %s' % (self.pc, self.pipeline['fetch'])
        else:
            self.pipeline['fetch'] = None
        self.results['fetch'] = None
    
    def decode(self):
        if self.pipeline['decode'] is not None:
            if self.verbose: print '-' * 30, 'decode stage for %s' % self.pipeline['decode'], '-' * 30
            self.pipeline['decode'].decode(self)
    
    def execute(self):
        if self.pipeline['execute'] is not None:
            if self.verbose: print '-' * 30, 'execute stage for %s' % self.pipeline['execute'], '-' * 30
            self.pipeline['execute'].execute(self)
    
    def memory(self):
        if self.pipeline['memory'] is not None:
            if self.verbose: print '-' * 30, 'memory stage for %s' % self.pipeline['memory'], '-' * 30
            self.pipeline['memory'].memory(self)
    
    def write(self):
        if self.pipeline['write'] is not None:
            if self.verbose: print '-' * 30, 'write stage for %s' % self.pipeline['write'], '-' * 30
            self.pipeline['write'].write(self)
            self.instruction_count += 1
    
    #@decode_register
    def write_register(self, register, data):
        if register == 0:
            return
        
        if self.verbose: print 'Writing %s to register %d' % (data, register)
        self.registers[register] = data
    
    #@decode_register
    def read_register(self, register):
        if self.verbose: print 'Reading register %d' % register
        return self.registers[register]
