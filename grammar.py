import myparser
from myparser import *

def enable_debug():
	myparser.DEBUG_DEFAULT = True

def joiner(l):
	return ''.join(l)

chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
digits = '0123456789'
hex_digits = digits + 'abcdefABCDEF'
spaces = ' \t'
newlines = '\n\r'

hex_number = LinearMatch(StringMatch('0x').postprocess(joiner), Word(hex_digits)).combine()
number = LinearMatch(atom('-').optional(), Word(digits)).combine().name('number').nameonly()
whitespace = Word(spaces).hide()
register = LinearMatch(atom('$'), Word(chars + digits)).combine().name('register').nameonly()
address = hex_number.name('address').nameonly()
offset = (number + whitespace.optional() + atom('(').hide() + (register | address) + atom(')').hide()).combine()

instruction_delimiter = whitespace.optional() + atom(',').hide() + whitespace.optional()
instruction_start = (whitespace.optional() + Word(chars + digits).name('instruction-name').nameonly() + whitespace).combine()
instruction = instruction_start + DelimitedMatch((register | offset | hex_number | address | number).combine(), whitespace.optional() + atom(',') + whitespace.optional())#.combine()

r_instruction = register + instruction_delimiter + register + instruction_delimiter + register
i_instruction = register + instruction_delimiter + register + instruction_delimiter + (number | hex_number)
j_instruction = address

comment = OrMatch(atom(';'), atom('#')) + StarMatch(NotMatch(orstring(newlines)))
end_of_instruction = LinearMatch(whitespace.optional(), comment.optional(), StarMatch(orstring(newlines), min=1)).combine()
#end_of_instruction = LinearMatch(comment.optional(), StarMatch(orstring(newlines), min=1)).combine()

instructions = (DelimitedMatch(instruction, end_of_instruction).combine() + StarMatch(orstring('\n\t\r ')).hide()).combine()

def parse(insts):
	return totalMatch(insts, instructions)

def raw_parse(insts):
	return instructions.match(insts)