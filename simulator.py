from instructions import *

# ---------------------------------------------------------------------------- #
# The Simulator and Helper Functions                                           #
# ---------------------------------------------------------------------------- #

BASE_MEMORY = 0x1000

def addr_check(func):
    """ Decorator for an instancemethod that takes in an address as its first argument.  This
    decorator will check if the address is at a word boundary and throw an exception if not.  If it
    is, it will pass the address / 4 to the actual function.
    """
    def wrapper(self, addr, *args, **kwargs):
        if addr & 0x3 != 0:
            raise RuntimeError("Can't access memory at a non-word boundary.")
        return func(self, addr >> 2, *args, **kwargs)
    return wrapper


class Simulator(object):
    """ Represents a simulator. """
    def __init__(self, verbose=False):
        """ verbose=bool

        Initializes a simulator.  If the verbose flag is enabled, the simulator will print out a lot
        of debug information.
        """
        self.verbose = verbose
        self.pc = None
        self.registers = [0 for x in xrange(32)] # Initialize 32 registers.
        
        # Set up the stage names and the pipeline and results data structures.
        self.stages = 'fetch', 'decode', 'execute', 'memory', 'write'
        self.pipeline = {}
        self.results = {}

        self.reset()
    
    def reset(self):
        """ Resets the simulator so that a new set of instructions can be loaded. """
        self.instruction_count = 0
        self.cycle_count = 0
        self.__stall = None
        for stage in self.stages:
            self.pipeline[stage] = None
            self.results[stage] = None
        
        self.reset_memory()
    
    def instructions_executed(self):
        """ Returns the number of instructions that were executed during the last run. """
        return self.instruction_count
    
    def cycles_executed(self):
        """ Returns the number of cycles that were executed during the last run. """
        return self.cycle_count
    
    def cpi(self):
        """ Returns the cpi of the last run. """
        return self.cycles_executed() / float(self.instructions_executed())
    
    def stall(self, stage):
        """ Stalls the pipeline at the given stage. """
        self.__stall = stage
    
    def reset_memory(self):
        """ Resets the memory to 4096 zero'd bytes. """
        self.memory_data = [0 for _ in xrange(BASE_MEMORY >> 2)]
    
    @addr_check
    def read_word(self, addr):
        """ Reads a word from memory at addr. """
        return self.memory_data[addr]
    
    @addr_check
    def write_word(self, addr, word):
        """ Writes word to memory at addr.

        Word can be an int, long, instruction, or str.  If it's anything else, this function will
        error.

        If word is a str, it must not be more than 4 bytes long.  The str will be converted to a
        number before being inserted into memory.
        """
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
        """ Returns the current memory size in bytes. """
        return len(self.memory_data) << 2
    
    def flush_after(self, from_stage):
        """ Flushes the pipeline after the given stage.

        i.e. if the given stage is 'execute', it will flush the 'memory' and 'write' stages.

        NOTE: This function decrements the PC by 4.
        """
        for stage in self.stages[self.stages.index(from_stage)+1:]:
            if self.verbose: print 'Flushing %s' % self.pipeline[stage]
            self.pipeline[stage] = self.results[stage] = None
            self.pc -= 4
    
    def flush_before(self, from_stage):
        """ Flushes the pipeline before the given stage.

        i.e. if the given stage is 'execute', it will flush the 'fetch' and 'decode' stages.

        NOTE: This function decrements the PC by 4.
        """
        for stage in self.stages[:self.stages.index(from_stage)]:
            if self.verbose: print 'Flushing %s' % self.pipeline[stage]
            self.pipeline[stage] = self.results[stage] = None
            self.pc -= 4
    
    def jump_to(self, addr):
        """ Sets the PC to addr + 4. """
        if self.verbose: print 'Jumping to 0x%x' % addr
        self.pc = addr + 4
    
    def jump_relative_to(self, addr):
        """ Given an offset, modifies the pc to be + that offset. """
        if self.verbose: print 'Jumping 0x%x relative to 0x%x' % (addr, self.pc)
        self.pc += addr
        if self.verbose: print 'PC is now %x' % self.pc
    
    def load(self, instructions):
        """ Loads a set of instructions into memory. """
        for idx, instruction in enumerate(instructions):
            addr = idx * 4 + BASE_MEMORY
            self.write_word(addr, instruction)
    
    def run(self, start_pc=BASE_MEMORY):
        """ Runs the set of instructions starting at PC start_pc. """
        self.pc = start_pc
        # While the pipeline still has something in it, execute.
        while self.pc == start_pc or any(self.pipeline[stage] is not None for stage in self.pipeline):
            self.cycle()
            self.pc += 4
            if self.verbose: print hex(self.pc), self.registers
        
        print 'Execution finished'
        print '%d instructions were run in %d cycles with a CPI of %.03f' % (self.instruction_count, self.cycle_count, self.cpi())
        print self.registers
        print '[', ' '.join(['0x%x' % r for r in self.registers]), ']'
    
    def cycle(self):
        """ Simulates a single cycle of the simulation. """
        if self.verbose: print '=' * 40, 'NEW CYCLE', '=' * 40
        # Do each of the stages
        for stage in self.stages:
            self.current_stage = stage
            self.do_stage(stage)
        
        # If the pipeline has anything in it, increase the cycle count.
        if any(self.pipeline[stage] is not None for stage in self.stages):
            self.cycle_count += 1
        
        if self.verbose: print 'Cycle count is now %d' % self.cycle_count

    def do_stage(self, stage):
        """ Execute the given stage. """
        if stage not in self.stages:
            raise RuntimeError("Invalid stage: %s" % stage)
        
        getattr(self, stage)()

    def fetch(self):
        """ Moves the pipeline along and fetches the next instruction. """
        # Move the pipeline along.
        for idx, stage in reversed(list(enumerate(self.stages))):
            if stage == self.__stall:
                # If we were told to stall at this stage, reset the stall and reset the next
                # instruction (since this one won't be moved to the next stage).
                self.__stall = None
                self.pipeline[self.stages[idx + 1]] = None
                if self.verbose: print 'Stalling pipeline at %s' % stage
                if self.verbose: print 'New pipeline: %s' % self.pipeline
                return
            
            if idx > 0:
                instruction = self.pipeline[self.stages[idx - 1]]
                if instruction is not None and self.verbose:
                    print 'Moved %s from %s to %s' % (instruction, self.stages[idx - 1], stage)
                self.pipeline[stage] = instruction
                self.results[stage] = self.results[self.stages[idx - 1]]

        # If our PC is still within the limits of our memory, fetch a new instruction.
        if BASE_MEMORY <= self.pc < self.memory_size():
            self.pipeline['fetch'] = self.read_word(self.pc)
            if self.verbose: print 'Fetched new instruction from address 0x%x: %s' % (self.pc, self.pipeline['fetch'])
        else:
            self.pipeline['fetch'] = None
        self.results['fetch'] = None
    
    def decode(self):
        """ Decode stage. """
        if self.pipeline['decode'] is not None:
            if self.verbose: print '-' * 30, 'decode stage for %s' % self.pipeline['decode'], '-' * 30
            self.pipeline['decode'].decode(self)
    
    def execute(self):
        """ Execute stage. """
        if self.pipeline['execute'] is not None:
            if self.verbose: print '-' * 30, 'execute stage for %s' % self.pipeline['execute'], '-' * 30
            self.pipeline['execute'].execute(self)
    
    def memory(self):
        """ Memory stage. """
        if self.pipeline['memory'] is not None:
            if self.verbose: print '-' * 30, 'memory stage for %s' % self.pipeline['memory'], '-' * 30
            self.pipeline['memory'].memory(self)
    
    def write(self):
        """ Write stage.  Also increments the number of instructions executed by 1. """
        if self.pipeline['write'] is not None:
            if self.verbose: print '-' * 30, 'write stage for %s' % self.pipeline['write'], '-' * 30
            self.pipeline['write'].write(self)
            self.instruction_count += 1
    
    def write_register(self, register, data):
        """ Writes data to the given register.  At this point, register must be a number.  If the
        register is 0, writes are ignored.
        """
        if register == 0:
            return
        
        if self.verbose: print 'Writing %s to register %d' % (data, register)
        self.registers[register] = data
    
    def read_register(self, register):
        """ Reads data from the given register.  Register must be a number. """
        if self.verbose: print 'Reading register %d' % register
        return self.registers[register]
