# ---------------------------------------------------------------------------- #
# Instruction Argument Types                                                   #
# ---------------------------------------------------------------------------- #

class Argument(object):
    def is_register(self):
        return False
    
    def is_immediate(self):
        return False
    
    def is_offset(self):
        return False
    
    def value(self, sim):
        raise RuntimeError("Base arguments don't have a value.")
    
    def write(self, sim, value):
        raise RuntimeError("Cannot write to type %s" % type(self))

register_map = {}
for x in xrange(32):
    register_map['r%d' % x] = x

def map_lookup(dct, item):
    while item in dct:
        item = dct[item]
    return item

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

class Register(Argument):
    def __init__(self, name):
        self.name = name
        self.register_number = map_lookup(register_map, name)
        if not (0 <= self.register_number < 32) or not isinstance(self.register_number, (int, long)):
            raise RuntimeError("$%s does not appear to be a valid register." % self.name)
    
    def __str__(self):
        return 'Register(%s->%d)' % (self.name, self.register_number)
    
    def __repr__(self):
        return '$%s' % self.name
    
    def __eq__(self, other):
        return isinstance(other, Register) and self.register_number == other.register_number
    
    def value(self, sim):
        return sim.read_register(self.register_number)
    
    def write(self, sim, value):
        sim.write_register(self.register_number, value)
    
    def is_register(self):
        return True

class Immediate(Argument):
    def __init__(self, number, base=10):
        self.number = int(number, base)
    
    def __str__(self):
        return 'Integer(%s)' % self.number
    
    def __repr__(self):
        return '%d' % self.number
    
    def value(self, sim):
        return self.number
    
    def is_immediate(self):
        return True

class Offset(Argument):
    def __init__(self, offset, offset_from):
        self.offset = Immediate(offset)
        self.offset_from = parse_arg(offset_from)
    
    def __str__(self):
        return 'Offset(%s, %s)' % (self.offset, self.offset_from)
    
    def __repr__(self):
        return '%r(%r)' % (self.offset, self.offset_from)
    
    def value(self, sim):
        return self.offset.value(sim) + self.offset_from.value(sim)
    
    def is_offset(self):
        return True

def parse_arg(arg):
    if len(arg) == 2 and arg[0] == '$':
        return Register(arg[1])
    elif len(arg) == 2 and arg[0] == '0x':
        return Immediate(arg[1], base=16)
    elif (len(arg) == 1 and arg[0].isdigit()) or \
         (len(arg) == 2 and (arg[0] == '-' and arg[1].isdigit())):
        return Immediate(''.join(arg))
    elif len(arg) == 2 and arg[0].isdigit():
        return Offset(*arg)
    else:
        return arg