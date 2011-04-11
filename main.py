from pprint import pprint
from instructions import parse_instruction
from arguments import *
import traceback
import sys, time
import grammar
import simulator

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

for thing in read_asm_file(filename):
    print thing

insts = [parse_instruction(inst_name, [parse_arg(arg) for arg in args]) for inst_name, args in read_asm_file(filename)]
assert all(inst is not None for inst in insts)

sim = simulator.Simulator()
sim.load(insts)
sim.run()