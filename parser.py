import types

OPTIONAL_DEFAULT = False
DEBUG_DEFAULT = False
NAME_ONLY_DEFAULT = True
IGNORE_NAME_DEFAULT = True
ATOM_DEBUG = True

class CouldNotFindType(object):
    def __init__(self, message=""):
        self.message = message

CouldNotFind = CouldNotFindType()

def rec_join(s):
    try:
        return ''.join([rec_join(i) for i in s])
    except:
        return s

def general_sum(lst):
    if not lst: raise RuntimeError("Cannot do a sum on an empty list")
    s = lst[0]
    for i in lst[1:]:
        s += i
    return s

def copydict(d):
    o = {}
    for k in d:
        o[k] = d[k]
    return o

def __isfunction__(f):
    return type(f) in (types.FunctionType, types.MethodType)

def __pdebug__(s, depth, verbose, atom=False):
    if verbose and (not atom or atom and ATOM_DEBUG):
        print '  ' * depth + s

def __return_item__(item, rest, arguments):
    global CouldNotFind
    
    #print '------------ Returning ', arguments.get('name', None)
    action = lambda lst: lst + [item]
    if type(item) is CouldNotFindType:
        if arguments.get('optional', False):
            action = lambda lst: (lst)
        else:
            return CouldNotFind, rest
    else:
        if 'postprocess' in arguments:
            item = arguments['postprocess'](item)
        
        if 'name' in arguments and not arguments.get('ignorename', IGNORE_NAME_DEFAULT):
            item = {arguments['name']: item}
        #elif 'name' in arguments:
        
        if arguments.get('hide', False):
            action = lambda lst: list(lst)
        else:
            if arguments.get('combine', False):
                def combine_func(lst):
                    lst = lst + list(item) if hasattr(item, '__iter__') else [item]
                    return lst
                action = combine_func#lambda lst: lst + list(item)
    
    return action, rest

def __combine_options__(options1, options2):
    ret = {}
    for key in options1.keys() + options2.keys():
        if key in ret: continue
        if key in options1:
            ret[key] = options1[key]
        elif key in options2:
            ret[key] = options2[key]
    return ret

def copied_self(func):
    def wrapper(self, *args, **kwargs):
        cp = self.copy()
        func(cp, *args, **kwargs)
        return cp
    return wrapper

class MatchObject(object):

    def set_option(self, property_name, value):
        self.options[property_name] = value
        return self
    
    def set_options(self, **arguments):
        for argument in arguments:
            self.options[argument] = arguments[argument]
        return self
    
    def copy(self):
        raise RuntimeError("The base match object does not support copying")
    
    @copied_self
    def optional(self, optional=True):
        #cp = self.copy()
        self.options['optional'] = optional
        #return cp
    
    @copied_self
    def postprocess(self, postprocess):
        #cp = self.copy()
        self.options['postprocess'] = postprocess
        #return cp
    
    @copied_self
    def name(self, name):
        #cp = self.copy()
        self.options['name'] = name
        #return cp
    
    @copied_self
    def nameonly(self, nameonly=True):
        #cp = self.copy()
        self.options['nameonly'] = nameonly
        #return cp
    
    @copied_self
    def hide(self, hide=True):
        #cp = self.copy()
        self.options['hide'] = hide
        #return cp
    
    @copied_self
    def combine(self, combine=True):
        #cp = self.copy()
        self.options['combine'] = combine
        #return cp
    
    @copied_self
    def verbose(self, verbose=True):
        self.options['verbose'] = verbose
    
    @copied_self
    def quiet(self, quiet=True):
        self.options['verbose'] = not quiet
        
    def __repr__(self):
        return str(self)
    
    def __or__(self, other):
        if type(other) == OrMatch:
            return NotImplemented
        return OrMatch(self, other)
    
    def __add__(self, other):
        #if type(other) == LinearMatch:
        #    return NotImplemented
        return LinearMatch(self, other)

class LinearMatch(MatchObject):
    def __init__(self, *items, **arguments):
        self.items = items
        self.options = arguments
    
    def add_item(self, item):
        self.items += [item]
        return self
    
    def copy(self, copied_items={}):
        return LinearMatch(*[item.copy() for item in self.items], **self.options)
    
    def strval(self, seen=set()):
        if self in seen:
            return '...'
        if self.options.get('nameonly', NAME_ONLY_DEFAULT) and 'name' in self.options:
            return self.options['name']
        return 'LinearMatch(%s%s)' % ((self.options['name'] + ', ') if 'name' in self.options else '', ', '.join(['%s' % i.strval(seen=seen|set([self])) for i in self.items]))
    
    def __str__(self):
        return self.strval()
    
    def match(self, lst, depth=0, seen=set()):
        if (self, lst) in seen:
            return __return_item__(CouldNotFind, lst, self.options)
        __pdebug__('Matching %s to %r' % (str(self), lst), depth, self.options.get('verbose', DEBUG_DEFAULT))
        
        seen = seen | set([(self, lst)])
        original_lst = lst
        match_index = 0
        match_list = []
        done = False
        while True:
            match_item = self.items[match_index]
            #__pdebug__('Matching item %s to %s' % (match_item, lst), depth, self.options.get('verbose', DEBUG_DEFAULT))
            action, lst = match_item.match(lst, depth=depth+1, seen=seen)
            if type(action) is CouldNotFindType: return __return_item__(CouldNotFindType(action.message), original_lst, self.options)
            
            match_list = action(match_list)
            
            match_index += 1
            if match_index >= len(self.items):
                break
        
        return __return_item__(match_list, lst, self.options)
    
    def __add__(self, other):
        items = self.items + tuple([other])
        options = copydict(self.options)
        return LinearMatch(*items, **options)
    
    def __and__(self, other):
        if type(other) == LinearMatch:
            items = self.items + other.items
            options = __combine_options__(self.options, other.options)
        else:
            items = self.items + tuple([other])
            options = copydict(self.options)
        
        return LinearMatch(*items, **options)

class StarMatch(MatchObject):
    def __init__(self, match, **arguments):
        self.starMatch = match
        self.options = arguments
    
    def set_item(self, item):
        self.starMatch = item
        return self
    
    def get_item(self):
        return self.starMatch
    
    def copy(self):
        return StarMatch(self.starMatch.copy(), **self.options)
    
    def strval(self, seen=set()):
        if self in seen:
            return '...'
        if self.options.get('nameonly', NAME_ONLY_DEFAULT) and 'name' in self.options:
            return self.options['name']
        #return 'StarMatch(%s%s)' % ((self.options['name'] + ', ') if 'name' in self.options else '', self.starMatch.strval(seen=seen|set([self])))
        return '(%s)*' % str(self.starMatch)
    
    def __str__(self):
        return self.strval()
    
    def match(self, lst, depth=0, seen=set()):
        if (self, lst) in seen:
            return __return_item__(CouldNotFind, lst, self.options)
        __pdebug__('Matching %s to %r' % (str(self), lst), depth, self.options.get('verbose', DEBUG_DEFAULT))
        
        seen = seen | set([(self, lst)])
        original_lst = lst
        last_lst = lst
        matches = []
        while True:
            action, lst = self.starMatch.match(lst, depth=depth+1, seen=seen)
            
            if type(action) is CouldNotFindType or lst == last_lst: break
            last_lst = lst
            matches = action(matches)
        
        if self.options.get('min', 0) <= len(matches) <= self.options.get('max', float('inf')):
            __pdebug__('%s match succeeded' % self, depth, self.options.get('verbose', DEBUG_DEFAULT))
            return __return_item__(matches, lst, self.options)
        else:
            __pdebug__('%s match failed' % self, depth, self.options.get('verbose', DEBUG_DEFAULT))
            return __return_item__(CouldNotFind, original_lst, self.options)

class OrMatch(MatchObject):
    def __init__(self, *items, **arguments):
        self.items = items
        self.options = arguments
        #if 'combine' not in self.options:
        #    self.options['combine'] = True
    
    def add_item(self, item):
        self.items += [item]
        return self
    
    def copy(self, copied_items={}):
        return OrMatch(*[item.copy() for item in self.items], **self.options)
    
    def strval(self, seen=set()):
        if self in seen:
            return '...'
        if self.options.get('nameonly', NAME_ONLY_DEFAULT) and 'name' in self.options:
            return self.options['name']
        #return 'OrMatch(%s%s)' % ((self.options['name'] + ', ') if 'name' in self.options else '', ', '.join(['%s' % i.strval(seen=seen|set([self])) for i in self.items]))
        return '(%s)' % ' | '.join(['%s' % i.strval(seen=seen|set([self])) for i in self.items])
    
    def __str__(self):
        return self.strval()
    
    def match(self, lst, depth=0, seen=set()):
        if (self, lst) in seen:
            return __return_item__(CouldNotFind, lst, self.options)
        __pdebug__('Matching %s to %r' % (str(self), lst), depth, self.options.get('verbose', DEBUG_DEFAULT))
        
        seen = seen | set([(self, lst)])
        possible_matches = []
        operating_mode = self.options.get('mode', 'first')
        for match in self.items:
            __pdebug__('Matching item %s to %s' % (match, lst), depth, self.options.get('verbose', DEBUG_DEFAULT))
            action, new_lst = match.match(lst, depth=depth+1, seen=seen)
            if type(action) is CouldNotFindType:
                #print '-' * 20, self.options.get('name', '')
                continue
            
            l = action([])
            if len(l) > 0:
                possible_matches.append((l, new_lst))
            
                if operating_mode == 'first':
                    break
        
        if not possible_matches:
            __pdebug__('%s failed!' % (self), depth, self.options.get('verbose', DEBUG_DEFAULT))
            return __return_item__(CouldNotFind, lst, self.options)
        __pdebug__('%s succeeded!' % self, depth, self.options.get('verbose', DEBUG_DEFAULT))
        
        if operating_mode == 'shortest':
            # The longest list yields the shortest result
            result, rest = max(possible_matches, key=lambda m: len(m[1]))
        elif operating_mode == 'longest':
            # The longest list yields the shortest result
            result, rest = min(possible_matches, key=lambda m: len(m[1]))
        elif operating_mode == 'last':
            result, rest = possible_matches[-1]
        elif type(operating_mode) in (types.FunctionType, types.MethodType):
            result, rest = self.options['mode'](possible_matches)
        else:
            result, rest = possible_matches[0]
        
        return __return_item__(result, rest, self.options)
    
    def __or__(self, other):
        if type(other) == OrMatch:
            items = self.items + other.items
            options = __combine_options__(self.options, other.options)
        else:
            items = self.items + tuple([other])
            options = self.options
            
        return OrMatch(*items, **options)

class DelimitedMatch(MatchObject):
    def __init__(self, item, delimitor, **arguments):
        self.item = item
        self.delimitor = delimitor
        self.options = arguments
        #if 'combine' not in self.options:
        #    self.options['combine'] = True
    
    def copy(self, copied_items={}):
        return DelimitedMatch(self.item.copy(), self.delimitor.copy(), **self.options)
    
    def strval(self, seen=set()):
        if self in seen:
            return '...'
        if self.options.get('nameonly', NAME_ONLY_DEFAULT) and 'name' in self.options:
            return self.options['name']
        return 'DelimitedMatch(%s%s, %s)' % ((self.options['name'] + ', ') if 'name' in self.options else '', self.item, self.delimitor)
    
    def __str__(self):
        return self.strval()
    
    def match(self, lst, depth=0, seen=set()):
        if (self, lst) in seen:
            return __return_item__(CouldNotFind, lst, self.options)
        __pdebug__('Matching %s to %r' % (str(self), lst), depth, self.options.get('verbose', DEBUG_DEFAULT))
        
        seen = seen | set([(self, lst)])
        matches = []
        match = False
        new_lst = lst
        del_lst = None
        while not isinstance(match, CouldNotFindType):
            last_lst = new_lst
            if match: # is not None:
                __pdebug__('Searching for delimiter', depth, self.options.get('verbose', DEBUG_DEFAULT))
                delimitor_match, new_lst = self.delimitor.match(new_lst, depth=depth+1, seen=seen)
                if isinstance(delimitor_match, CouldNotFindType):
                    break
            
            __pdebug__('Searching for content...', depth, self.options.get('verbose', DEBUG_DEFAULT))
            action, new_lst = self.item.match(new_lst, depth=depth+1, seen=seen)
            if isinstance(action, CouldNotFindType):
                break
            match = True
            
            l = action([])
            matches.append(l)
        
        if not matches:
            __pdebug__('%s failed!' % (self), depth, self.options.get('verbose', DEBUG_DEFAULT))
            return __return_item__(CouldNotFind, lst, self.options)
        
        return __return_item__(matches, last_lst, self.options)
    
    def __or__(self, other):
        if type(other) == OrMatch:
            items = self.items + other.items
            options = __combine_options__(self.options, other.options)
        else:
            items = self.items + tuple([other])
            options = self.options
            
        return OrMatch(*items, **options)

class ValueMatch(MatchObject):
    def __init__(self, matchingValue, **arguments):
        self.matchingValue = matchingValue
        self.options = arguments
    
    def copy(self, copied_items={}):
        if self in copied_items:
            return copied_items[self]
        return ValueMatch(self.matchingValue, **self.options)
    
    def __str__(self):
        return self.strval()
    
    def strval(self, seen=set()):
        if self.options.get('nameonly', NAME_ONLY_DEFAULT) and 'name' in self.options:
            return self.options['name']
        return ('%s' % ('value(' + self.options['name'] + ', %s)') if 'name' in self.options else '%s') % '%r' % self.matchingValue
    
    def match(self, lst, depth=0, seen=set()):
        if (self, lst) in seen:
            return __return_item__(CouldNotFind, lst, self.options)
        __pdebug__('Matching %s to %r' % (str(self), lst), depth, self.options.get('verbose', DEBUG_DEFAULT), atom=True)
        
        return_value = CouldNotFind
        rest = lst
        if len(lst) > 0 and lst[0] == self.matchingValue:
            return_value = lst[0]
            rest = lst[1:]
        
        if return_value is CouldNotFind:
            __pdebug__('Match %s failed' % str(self), depth, self.options.get('verbose', DEBUG_DEFAULT), atom=True)
        else:
            __pdebug__('Match %s succeeded' % str(self), depth, self.options.get('verbose', DEBUG_DEFAULT), atom=True)
        return __return_item__(return_value, rest, self.options)

class TypeMatch(MatchObject):
    def __init__(self, *matching_types, **arguments):
        self.matching_types = matching_types
        self.options = arguments
    
    def copy(self, copied_items={}):
        return TypeMatch(*self.matching_types, **self.options)
    
    def __str__(self):
        return self.strval()
    
    def strval(self, seen=set()):
        if self.options.get('nameonly', NAME_ONLY_DEFAULT) and 'name' in self.options:
            return self.options['name']
        return 'type(%s%s)' % ((self.options['name'] + ', ') if 'name' in self.options else '', self.matching_types)
    
    def match(self, lst, depth=0, seen=set()):
        if (self, lst) in seen:
            return __return_item__(CouldNotFind, lst, self.options)
        __pdebug__('Matching %s to %r' % (str(self), lst), depth, self.options.get('verbose', DEBUG_DEFAULT), atom=True)
        
        return_value = CouldNotFind
        rest = lst
        if len(lst) > 0 and type(lst[0]) in self.matching_types:
            return_value = lst[0]
            rest = lst[1:]
        
        return __return_item__(return_value, rest, self.options)

class FunctionMatch(MatchObject):
    def __init__(self, function, **arguments):
        self.matching_function = function
        self.options = arguments
    
    def copy(self):
        return FunctionMatch(self.matching_function, **self.options)
    
    def strval(self, seen=set()):
        return self.matching_function
    
    def match(self, lst, depth=0, seen=set()):
        if (self, lst) in seen:
            return __return_item__(CouldNotFind, lst, self.options)
        __pdebug__('Matching %s to %r' % (str(self), lst), depth, self.options.get('verbose', DEBUG_DEFAULT))
        return self.matching_function(lst)

class RegexMatch(MatchObject):
    def __init__(self, regex, **arguments):
        self.matching_regex = regex
        self.options = arguments
    
    def copy(self):
        return RegexMatch(self.matching_regex, **self.options)
    
    def strval(self, seen=set()):
        return self.matching_regex
    
    def match(self, lst, depth=0, seen=set()):
        if (self, lst) in seen:
            return __return_item__(CouldNotFind, lst, self.options)
        __pdebug__('Matching %s to %r' % (str(self), lst), depth, self.options.get('verbose', DEBUG_DEFAULT))
        m = self.matching_regex.search(lst[0])
        if m:
            return __return_item__(m.groups(), lst[1:], self.options)

class NotMatch(MatchObject):
    def __init__(self, *matches, **arguments):
        self.matches = matches
        self.options = arguments
    
    def copy(self, copied_items={}):
        return NotMatch(*[m.copy() for m in self.matches], **self.options)
    
    def __str__(self):
        return self.strval()
    
    def strval(self, seen=set()):
        if self in seen:
            return '...'
        if self.options.get('nameonly', NAME_ONLY_DEFAULT) and 'name' in self.options:
            return self.options['name']
        return 'not %s' % ', '.join([m.strval(seen=seen|set([self])) for m in self.matches])
    
    def match(self, lst, depth=0, seen=set()):
        if (self, lst) in seen:
            return __return_item__(CouldNotFind, lst, self.options)
        __pdebug__('Matching %s to %r' % (str(self), lst), depth, self.options.get('verbose', DEBUG_DEFAULT))
        
        ret = [m.match(lst, depth=depth+1, seen=seen|set([(self, lst)])) for m in self.matches]
        #action, new_lst = self.matching_match.match(lst, depth=depth+1, seen=seen+[(self,lst)])
        if all([type(action) is CouldNotFindType for action, new_lst in ret]):
            advance_amount = self.options.get('advance', 1)
            #print advance_amount, len(lst)
            if len(lst) >= advance_amount:
                return __return_item__(lst[0:advance_amount], lst[advance_amount:], self.options)
        
        #print ret
        __pdebug__('%s to %r failed' % (str(self), lst), depth, self.options.get('verbose', DEBUG_DEFAULT))
        return __return_item__(CouldNotFind, lst, self.options)

def atom(item, **arguments):
    return ValueMatch(item, **arguments)

def StringMatch(s, **arguments):
    l = [atom(c) for c in s]
    return LinearMatch(*l, **arguments)

def orstring(s, **arguments):
    arguments['combine'] = arguments.get('combine', True)
    l = [atom(c) for c in s]
    return OrMatch(*l, **arguments)

class Combine(MatchObject):
    def __init__(self, match, **arguments):
        self.thismatch = match
        self.options = arguments
    
    def copy(self, copied_items={}):
        return Combine(self.thismatch.copy(), **self.options)
    
    def __str__(self):
        return self.strval()
    
    def strval(self, seen=set()):
        if self in seen:
            return '...'
        if self.options.get('nameonly', NAME_ONLY_DEFAULT) and 'name' in self.options:
            return self.options['name']
        return 'Combine(%s)' % self.thismatch.strval(seen=seen | set([self]))
    
    def match(self, lst, depth=0, seen=set()):
        if (self, lst) in seen:
            return __return_item__(CouldNotFind, lst, self.options)
        __pdebug__('Matching %s to %r' % (str(self), lst), depth, self.options.get('verbose', DEBUG_DEFAULT))

        ret = self.thismatch.match(lst, depth=depth+1, seen=seen|set([(self, lst)]))
        if isinstance(ret, CouldNotFindType):
            __pdebug__('%s to %r failed' % (str(self), lst), depth, self.options.get('verbose', DEBUG_DEFAULT))
            return __return_item__(CouldNotFind, lst, self.options)
        
        ret_object, remainder = ret
        options = {
            'postprocess': lambda r: general_sum(r([]))
        }
        options.update(self.options)
        return __return_item__(ret_object, remainder, options)

def Word(s, **arguments):
    arguments['combine'] = arguments.get('combine', True)
    arguments['min'] = 1
    l = [atom(c) for c in s]
    return Combine(StarMatch(OrMatch(*l, combine=True), **arguments))

def totalMatch(lst, match, **arguments):
    match = match.copy()
    match.options.update(arguments)
    ret = match.match(lst)
    
    if ret is None:
        return False
    
    retObject, remainder = ret

    if not remainder and not isinstance(retObject, CouldNotFindType):
        return retObject([])
    else:
        return None

class WhitespaceClass(object):
    def __init__(self, whitespace):
        pass
    
    def __repr__(self):
        return 'Whitespace()'

class StringClass(object):
    def __init__(self, s):
        print '-' * 100
        print 'String class of ', s
        self.stringcontent = ''.join(s)
    
    def __repr__(self):
        return 'String(%s)' % self.stringcontent

class NameClass(object):
    def __init__(self, s):
        self.name = ''.join(s)
    
    def __repr__(self):
        return 'Name(%s)' % self.name

class TextClass(object):
    def __init__(self, s):
        self.text = s
    
    def __repr__(self):
        return 'Text(%s)' % self.text

class NumberClass(object):
    def __init__(self, s):
        print s
        self.number = ''.join(s[0])
    
    def __repr__(self):
        return 'Number(%s)' % self.number

if __name__ == '__main__':
    whitespace = StarMatch(atom(' ', name='space') | atom('\n', name='newline') | atom('\r', name='carriage-return') | atom('\t', name='tab') | (StringMatch('/*', name='comment-start') + NotMatch(StringMatch('*/'), name='not-comment-end') + StringMatch('*/', name='comment-end')), name='whitespace', optional=True, hide=True, postprocess=WhitespaceClass)
    name = StarMatch(orstring('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`~!@#$%^&*\\|;:,./<>?', combine=True, name='name-chars', verbose=False), min=1, name='name', postprocess=NameClass)

    integer_number = StarMatch(orstring('0123456789', combine=True), min=1, name='integer-number', nameonly=True)
    float_number = (integer_number + atom('.') + StarMatch(orstring('0123456789'))).set_options(name='float-number', combine=True)
    number = (integer_number | float_number).set_options(name='number', combine=True, postprocess=NumberClass)
    string = ((atom('"', name='double-quote', hide=True) + StarMatch(OrMatch(StringMatch('\\"', postprocess=lambda i:'"'), NotMatch(atom('"')), combine=True), name='double-quote-string-content', combine=True) + atom('"', name='double-quote', hide=True)).set_options(combine=True) | \
              (atom("'", name='single-quote', hide=True) + StarMatch(OrMatch(StringMatch("\\'", postprocess=lambda i:"'"), NotMatch(atom("'")), combine=True), name='single-quote-string-content', combine=True) + atom("'", name='single-quote', hide=True)).set_options(combine=True)).set_options(postprocess=StringClass)
    expr = OrMatch(string, number, name='expr')

    #print expr.match('123')

    parameter = expr.copy().set_options(name='parameter', combine=True)
    named_parameter = (name + whitespace + atom('=') + whitespace + expr).set_options(name='named-parameter', combine=True)

    reg_parameters_rest = StarMatch((whitespace + atom(',', hide=True) + whitespace + parameter).set_options(combine=True), name='reg-parameters-rest', combine=True)
    reg_parameters = (parameter + reg_parameters_rest).set_options(name='reg-parameters', combine=True)
    named_parameters_rest = StarMatch((whitespace + atom(',', hide=True) + whitespace + named_parameter).set_options(combine=True), name='named-parameters-rest', combine=True)
    named_parameters = (named_parameter + named_parameters_rest).set_options(name='named-parameters', combine=True)

    parameters = OrMatch(reg_parameters, named_parameters, reg_parameters + named_parameters_rest, whitespace, name='parameters', optional=True)

    content_placeholder = StarMatch(None, name='content')
    header = whitespace + name + whitespace + atom('(', hide=True) + whitespace + parameters + whitespace + atom(')', hide=True) + whitespace + atom('{', hide=True) + whitespace + content_placeholder + whitespace + atom('}', hide=True) + whitespace
    header.set_options(name='header', optional=True, combine=True)
    content_placeholder.set_item(OrMatch(header, NotMatch(atom('}', postprocess=TextClass)), combine=True))
    content_placeholder.set_options(combine=True)

    #sys.exit(1)
    #print totalMatch('abdbdc () {}', header)
    print totalMatch('abdbdc     ( 123 , 124, 125, 126, 127, "this is a test string.  in theory all of this\\\"should fall", \'a\\\'bcd\' ) { hello name() {} } ', header)