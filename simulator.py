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

class Simulator(object):
    def __init__(self):
        self.registers = [0 for x in xrange(32)]
        self.register_map = {}

        for x in xrange(32):
            self.register_map['r%d' % x] = x
        
        self.instructions = None
    
    def load(self, instructions):
        self.instructions = instructions
    
    def run(self):
        if self.instructions is None:
            raise RuntimeError("No instructions have been loaded.")

        

    
    @decode_register
    def write_register(self, register, data):
        if register == 0:
            return
        
        self.registers[register] = data
    
    @decode_register
    def read_register(self, register):
        return self.registers[register]