from pprint import pprint
from instructions import parse_instruction
import sys, time
import grammar

#grammar.enable_debug()

filename = sys.argv[1]
def read_asm_file(filename):
    with open(filename, 'rb') as f:
        data = f.read()
        print len(data.split('\n'))

        parsed_instructions = grammar.parse(data)

        if parsed_instructions is None:
            action, rest = grammar.raw_parse(data)
            error_char = len(data) - len(rest)
            data_up_to_error = data[:error_char]
            line_num = data_up_to_error.count('\n')
            prev_newline = data_up_to_error.rfind('\n')
            next_newline = rest.find('\n')
            if prev_newline < 0:
                prev_newline = 0
            if next_newline < 0:
                next_newline = len(rest)
            
            relative_error_char = error_char - prev_newline
            print "Syntax error at line %d, character %d" % (line_num + 1, relative_error_char)

            print data[prev_newline:error_char] + rest[:next_newline]
            print ' ' * relative_error_char + '^'
            return None
    
    return parsed_instructions

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

class Register(Argument):
    def __init__(self, name):
        self.name = name
    
    def __str__(self):
        return 'Register(%s)' % self.name
    
    def __repr__(self):
        return '$%s' % self.name
    
    def is_register(self):
        return True

class Immediate(Argument):
    def __init__(self, number, base=10):
        self.number = int(number, base)
    
    def __str__(self):
        return 'Integer(%s)' % self.number
    
    def __repr__(self):
        return '%d' % self.number
    
    def is_immediate(self):
        return True

class Offset(Argument):
    def __init__(self, offset, offset_from):
        self.offset = Integer(offset)
        self.offset_from = parse_arg(offset_from)
    
    def __str__(self):
        return 'Offset(%s, %s)' % (self.offset, self.offset_from)
    
    def __repr__(self):
        return '%r(%r)' % (self.offset, self.offset_from)
    
    def is_offset(self):
        return True

def parse_arg(arg):
    #print arg
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

for inst_name, args in read_asm_file(filename):
    args = [parse_arg(arg) for arg in args]
    print parse_instruction(inst_name, args)
