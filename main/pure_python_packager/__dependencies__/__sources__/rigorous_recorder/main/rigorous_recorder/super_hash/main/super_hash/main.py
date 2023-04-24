from simple_namespace import namespace
import collections
from hashlib import md5 
import pickle

code = type(compile('1','','single'))

def consistent_hash(value):
    if isinstance(value, bytes):
        return md5(value).hexdigest()
    
    if isinstance(value, str):
        return md5(("@"+value).encode('utf-8')).hexdigest()
    
    if isinstance(value, (bool, int, float, type(None))):
        return md5(str(value).encode('utf-8')).hexdigest()
        
    else:
        return md5(pickle.dumps(value, protocol=4)).hexdigest()


@namespace
def helpers():
    
    # yup this is how to detect iterables in python
    def is_iterable(thing):
        # https://stackoverflow.com/questions/1952464/in-python-how-do-i-determine-if-an-object-is-iterable
        try:
            iter(thing)
        except TypeError:
            return False
        else:
            return True
            
    def shallow_instruction_hash(value):
        import dis
        instructions = dis.get_instructions(value)
        to_hash = [str((each.opcode, each.argval)) for each in instructions]
        hash_str = str(' '.join(to_hash).encode('utf-8')) + str(value.__name__ if hasattr(value, "__name__") else "")
        return consistent_hash(hash_str)
    
    def source_hash(value):
        import inspect
        source = inspect.getsource(value)
        return consistent_hash(f"{hash_salt}{source}")
    
    return locals()
    
@namespace
def function_hashers():
    def smart(value):
        # if defined in a proper module
        try:
            return deep(value)
        except Exception as error:
            pass
        
        # if user defined
        try:
            return shallow(value)
        except Exception as error:
            pass
        
        # if file defined, but actually a class
        try:
            return helpers.source_hash(value)
        except Exception as error:
            pass
        
        # if has documentation (e.g. builtin)
        if type(value.__doc__) == str and len(value.__doc__) > 0 and type(value.__name__) == str:
            return consistent_hash(f'{hash_salt}{value.__doc__}{value.__name__}')
        
        # if all this fails, use the object id
        return id(value)
    
    def shallow(value):
        return helpers.shallow_instruction_hash(value)
    
    # from https://github.com/andrewgazelka/smart-cache/blob/master/smart_cache/__init__.py
    def instructions_to_hash(instructions):
        to_hash = [str((each.opcode, super_hash(each.argval))) for each in instructions]
        hash_str = ' '.join(to_hash).encode('utf-8')
        return consistent_hash(hash_str)
    
    def get_referenced_function_names(instructions):
        return [ins.argval for ins in instructions if ins.opcode == 116]
    
    def deep(input_func):
        import inspect
        import dis
        module = inspect.getmodule(input_func)
        closed_set = set()
        instruction_hashes = [] if not hasattr(input_func, "__name__") else [ input_func.__name__ ]
        frontier = set()
        
        base_instructions = list(dis.get_instructions(input_func))
        child_names = get_referenced_function_names(base_instructions)
        instruction_hashes.append(str(instructions_to_hash(base_instructions)))
        for name in child_names:
            frontier.add(name)
        
        while len(frontier) > 0:
            function_name = frontier.pop()
            closed_set.add(function_name)
            function_reference = getattr(module, function_name, None)
            if function_reference is None:
                continue
            try:
                instructions = dis.get_instructions(function_reference)
            except TypeError as error:
                continue
            instruction_hashes.append(str(instructions_to_hash(instructions)))
            child_names = get_referenced_function_names(instructions)
            for child_name in child_names:
                if child_name not in closed_set:
                    frontier.add(child_name)
        hash_str = ' '.join(instruction_hashes).encode('utf-8')
        return consistent_hash(hash_str)
    
    return locals()

class FrozenDict(collections.Mapping):
    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        self._hash = None

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __getitem__(self, key):
        return self._d[key]

    def __hash__(self):
        # from: https://stackoverflow.com/questions/2703599/what-would-a-frozen-dict-be
        # It would have been simpler and maybe more obvious to 
        # use hash(tuple(sorted(self._d.iteritems()))) from this discussion
        # so far, but this solution is O(n). I don't know what kind of 
        # n we are going to run into, but sometimes it's hard to resist the 
        # urge to optimize when it will gain improved algorithmic performance.
        if self._hash is None:
            hash_ = 0
            for pair in self.items():
                hash_ ^= consistent_hash(pair)
            self._hash = hash_
        return self._hash

# lots of things are not hashable when they could be (dicts), we need to make them hashable
def super_hash(value, *, __already_seen__=None):
    already_seen = {} if __already_seen__ is None else __already_seen__
    # 
    # first check the table
    # 
    for each_checker in reversed(super_hash.conversion_table.keys()):
        type_matches = isinstance(each_checker, type) and isinstance(value, each_checker)
        callable_check_matches = not isinstance(each_checker, type) and callable(each_checker) and each_checker(value)
        if type_matches or callable_check_matches:
            custom_hash_function = super_hash.conversion_table[each_checker]
            return custom_hash_function(value)
    
    if type(value) == code:
        try:
            import dis
            instructions = dis.get_instructions(value)
            return consistent_hash(str([str((each.opcode, super_hash(each.argval))) for each in instructions]))
        except Exception as error:
            return consistent_hash(code.co_code)
    # 
    # fallback 1: attempt consistent hash
    # 
    try:
        return consistent_hash(value)
    except Exception as error:
        # ignore the "TypeError: unhashable type:" errors and go to the next fallback method
        pass
    # 
    # generic fallback methods
    # 
    hash_salt = -24979514859357
    value_id = id(value)
    if helpers.is_iterable(value):
        if value_id in already_seen:
            # seen but not yet computed
            if already_seen[value_id] is None:
                return hash_salt
            else:
                return already_seen[value_id]
        else:
            already_seen[value_id] = None
        
        # dict is a special case, switch to using all its keys
        if isinstance(value, dict):
            value = (
                (
                    super_hash(each_key, __already_seen__=already_seen),
                    super_hash(each_value, __already_seen__=already_seen),
                    super_hash(value.__class__),
                ) 
                    for each_key, each_value in value.items() 
            )
        # all the items
        output = super_hash(
            tuple(
                super_hash(each, __already_seen__=already_seen) for each in value
            ) + (
                super_hash(value.__class__),
            )
        )
        # give it a real value
        already_seen[value_id] = output
        return already_seen[value_id]
    # some weird primitive, like a class or method or builtin function
    else:
        # if cached
        if value_id in super_hash._non_iterable_cache:
            return super_hash._non_iterable_cache[value_id]
        
        # if its a type
        if isinstance(value, type):
            the_class = ""
            if hasattr(the_class, "__name__"):
                the_class += the_class.__name__
            if hasattr(the_class, "__module__"):
                the_class += str(the_class.__module__)
            return consistent_hash(the_class)
        
        # if statically defined in a file
        try:
            super_hash._non_iterable_cache[value_id] = helpers.source_hash(value)
            return super_hash._non_iterable_cache[value_id]
        except Exception as error:
            pass
        
        # if dynamically defined
        try:
            super_hash._non_iterable_cache[value_id] = shallow_instruction_hash(value)
            return super_hash._non_iterable_cache[value_id]
        except Exception as error:
            pass
        
        # if has documentation (e.g. builtin)
        if type(value.__doc__) == str and len(value.__doc__) > 0 and type(value).__name__ == str:
            super_hash._non_iterable_cache[value_id] = consistent_hash(f'{hash_salt}{value.__doc__}{value.__name__}')
            return super_hash._non_iterable_cache[value_id]
        
        # if all this fails, use the object id
        super_hash._non_iterable_cache[value_id] = value_id
        return super_hash._non_iterable_cache[value_id]

super_hash._non_iterable_cache = {}
super_hash.conversion_table = {
    # have functions default to deep hashing
    (lambda each: callable(each) and not isinstance(each, type)): function_hashers.smart
}