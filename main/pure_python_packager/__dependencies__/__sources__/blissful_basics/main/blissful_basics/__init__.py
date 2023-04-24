from .__dependencies__ import json_fix
from .__dependencies__ import file_system_py as FS
from .__dependencies__.super_map import LazyDict, Map
from .__dependencies__.super_hash import super_hash, hash_file

from time import time as now
from random import shuffle

# 
# checkers
# 
if True:
    def is_iterable(thing):
        # https://stackoverflow.com/questions/1952464/in-python-how-do-i-determine-if-an-object-is-iterable
        try:
            iter(thing)
        except TypeError:
            return False
        else:
            return True

    def is_generator_like(thing):
        return is_iterable(thing) and not isinstance(thing, (str, bytes))
    
    import collections.abc
    def is_dict(thing):
        return isinstance(thing, collections.abc.Mapping)


# 
# data structures
# 
if True:
    def singleton(a_class):
        """
        @singleton
        SomeClass:
            thing = 10
            @property
            def double_thing(self):
                return self.thing * 2
        
        print(SomeClass.double_thing) # >>> 20
        """
        return a_class()
    
    class Object: # just an empty object for assigning attributes of
        def __init__(self, **kwargs):
            for each_key, each_value in kwargs.items():
                setattr(self, each_key, each_value)
        
        def __repr__(self):
            if len(self.__dict__) == 0:
                return 'Object()'
            else:
                entries = "Object(\n"
                for each_key, each_value in self.__dict__.items():
                    entries += "    "+str(each_key)+" = "+repr(each_value)+",\n"
                return entries+")"
    
    def create_named_list_class(names):
        """
        Example:
            Position = create_named_list_class(['x','y','z'])
            a = Position([1,2,3])
            print(a.x)   # 1
            a.x = 4
            print(a[0])  # 4
            a[0] = 9
            print(a.x)   # 9
        """
        
        names_to_index = {}
        if isinstance(names, dict):
            names_to_index = names
        if isinstance(names, (tuple, list)):
            for index, each in enumerate(names):
                names_to_index[each] = index
        
        class NamedList(list):
            def __getitem__(self, key):
                if isinstance(key, (int, slice)):
                    return super(NamedList, self).__getitem__(key)
                # assume its a name
                else:
                    try:
                        index = names_to_index[key]
                    except:
                        raise KeyError(f'''key={key} not in named list: {self}''')
                    if index >= len(self):
                        return None
                    return self[index]
            
            def __getattr__(self, key):
                if key in names_to_index:
                    return self[key]
                else:
                    super(NamedList, self).__getattribute__(key)
            
            def __setattr__(self, key, value):
                if key in names_to_index:
                    index = names_to_index[key]
                    while index >= len(self):
                        super(NamedList, self).append(None)
                    super(NamedList, self).__setitem__(index, value)
                else:
                    super(NamedList, self).__setattr__(key, value)
            
            def __setitem__(self, key, value):
                if isinstance(key, int):
                    super(NamedList, self).__setitem__(key, value)
                # assume its a name
                else:
                    index = names_to_index[key]
                    while index >= len(self):
                        super(NamedList, self).append(None)
                    super(NamedList, self).__setitem__(index, value)
                    
            def keys(self):
                return list(names_to_index.keys())
            
            def values(self):
                return self
            
            def get(self, key, default):
                try:
                    return self[key]
                except Exception as error:
                    return default
            
            def items(self):
                return zip(self.keys(), self.values())
            
            def update(self, other):
                for each_key in names_to_index:
                    if each_key in other:
                        self[each_key] = other[each_key]
                return self
            
            def __repr__(self):
                import itertools
                out_string = '['
                named_values = 0
                
                reverse_lookup = {}
                for each_name, each_index in names_to_index.items():
                    reverse_lookup[each_index] = reverse_lookup.get(each_index, []) + [ each_name ]
                    
                for each_index, value in enumerate(self):
                    name = "=".join(reverse_lookup.get(each_index, []))
                    if name:
                        name += '='
                    out_string += f' {name}{value},'
                
                out_string += ' ]'
                return out_string
                
        return NamedList

# 
# warnings
# 
if True:
    import warnings
    @singleton
    class Warnings:
        _original_filters = list(warnings.filters)
        _original_showwarning = warnings.showwarning
        def show_full_stack_trace(self):
            # show full traceback of each warning
            import traceback
            import warnings
            import sys
            def warn_with_traceback(message, category, filename, lineno, file=None, line=None):
                log = file if hasattr(file,'write') else sys.stderr
                traceback.print_stack(file=log)
                log.write(warnings.formatwarning(message, category, filename, lineno, line))
            warnings.showwarning = warn_with_traceback
            warnings.simplefilter("always")
        
        def show_normal(self):
            warnings.filters = self._original_filters
            warnings.showwarning = self._original_showwarning
        
        def disable(self):
            warnings.simplefilter("ignore")
            warnings.filterwarnings('ignore')
        
        class disabled:
            # TODO: in future allow specify which warnings to disable
            def __init__(with_obj, *args, **kwargs):
                pass
            
            def __enter__(with_obj):
                with_obj._original_filters = list(warnings.filters)
                with_obj._original_showwarning = warnings.showwarning
            
            def __exit__(with_obj, _, error, traceback):
                # normal cleanup HERE
                warnings.filters = with_obj._original_filters
                warnings.showwarning = with_obj._original_showwarning
                
                with_obj._original_filters = list(warnings.filters)
                with_obj._original_showwarning = warnings.showwarning
                
                if error is not None:
                    raise error
    # show full stack trace by default instead of just saying "something wrong happened somewhere I guess"
    Warnings.show_full_stack_trace()
        
# 
# string related
# 
if True:
    def indent(string, by="    ", ignore_first=False):
        indent_string = (" "*by) if isinstance(by, int) else by
        string = string if isinstance(string, str) else stringify(string)
        start = indent_string if not ignore_first else ""
        return start + string.replace("\n", "\n"+indent_string)

    def remove_largest_common_prefix(list_of_strings):
        def all_equal(a_list):
            if len(a_list) == 0:
                return True
            
            prev = a_list[0]
            for each in a_list:
                if prev != each:
                    return False
                prev = each
            
            return True
        
        shortest_path_length = min([ len(each_path) for each_path in list_of_strings ])
        longest_common_path_length = shortest_path_length
        while longest_common_path_length > 0:
            # binary search would be more efficient but its fine
            longest_common_path_length -= 1
            if all_equal([ each[0:longest_common_path_length] for each_path in list_of_strings ]):
                break
        
        return [ each[longest_common_path_length:] for each_path in list_of_strings ]
            
    def pascal_case_with_spaces(string, valid_word_contents="1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"):
        digits = "1234567890"
        new_string = " "
        # get pairwise elements
        for each_character in string:
            prev_character = new_string[-1]
            prev_is_lowercase = prev_character.lower() == prev_character
            each_is_uppercase = each_character.lower() != each_character
            
            # remove misc characters (handles snake case, kebab case, etc)
            if each_character not in valid_word_contents:
                new_string += " "
            # start of word
            elif prev_character not in valid_word_contents:
                new_string += each_character.upper()
            # start of number
            elif prev_character not in digits and each_character in digits:
                new_string += each_character
            # end of number
            elif prev_character in digits and each_character not in digits:
                new_string += each_character.upper()
            # camel case
            elif prev_is_lowercase and each_is_uppercase:
                new_string += " "+each_character.upper()
            else:
                new_string += each_character
        
        # flatten out all the whitespace
        new_string = new_string.strip()
        while "  " in new_string:
            new_string = new_string.replace("  "," ")
        
        return new_string

    def levenshtein_distance(s1, s2):
        # https://stackoverflow.com/questions/2460177/edit-distance-in-python
        if len(s1) > len(s2):
            s1, s2 = s2, s1
        
        distances = range(len(s1) + 1)
        for i2, c2 in enumerate(s2):
            distances_ = [i2+1]
            for i1, c1 in enumerate(s1):
                if c1 == c2:
                    distances_.append(distances[i1])
                else:
                    distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
            distances = distances_
        return distances[-1]
    
    def levenshtein_distance_sort(*, word, other_words):
        word = word.lower() # otherwise this totally screws up distance
        prioritized = sorted(other_words, key=lambda each_other: levenshtein_distance(word, each_other))
        return prioritized

# 
# generic (any value)
# 
if True:
    def attributes(a_value):
        if a_value == None:
            return []
        all_attachments = dir(a_value)
        return [
            each for each in all_attachments if not (each.startswith("__") and each.endswith("__")) and not callable(getattr(a_value, each))
        ]
    
    def to_pure(an_object, recursion_help=None):
        # 
        # infinte recursion prevention
        # 
        top_level = False
        if recursion_help is None:
            top_level = True
            recursion_help = {}
        class PlaceHolder:
            def __init__(self, id):
                self.id = id
            def eval(self):
                return recursion_help[key]
        object_id = id(an_object)
        # if we've see this object before
        if object_id in recursion_help:
            # if this value is a placeholder, then it means we found a child that is equal to a parent (or equal to other ancestor/grandparent)
            if isinstance(recursion_help[object_id], PlaceHolder):
                return recursion_help[object_id]
            else:
                # if its not a placeholder, then we already have cached the output
                return recursion_help[object_id]
        # if we havent seen the object before, give it a placeholder while it is being computed
        else:
            recursion_help[object_id] = PlaceHolder(object_id)
        
        parents_of_placeholders = set()
        
        # 
        # optional torch tensor converter
        # 
        if hasattr(an_object, "__class__") and hasattr(an_object.__class__, "__name__"):
            if an_object.__class__.__name__ == "Tensor":
                try:
                    import torch
                    if isinstance(an_object, torch.Tensor):
                        an_object = an_object.detach().cpu()
                except Exception as error:
                    pass
        # 
        # main compute
        # 
        return_value = None
        # base case 1 (iterable but treated like a primitive)
        if isinstance(an_object, str):
            return_value = an_object
        # base case 2 (exists because of scalar numpy/pytorch/tensorflow objects)
        elif hasattr(an_object, "tolist"):
            return_value = an_object.tolist()
        else:
            # base case 3
            if not is_iterable(an_object):
                return_value = an_object
            else:
                if isinstance(an_object, dict):
                    return_value = {
                        to_pure(each_key, recursion_help) : to_pure(each_value, recursion_help)
                            for each_key, each_value in an_object.items()
                    }
                else:
                    return_value = [ to_pure(each, recursion_help) for each in an_object ]
        
        # convert iterables to tuples so they are hashable
        if is_iterable(return_value) and not isinstance(return_value, dict) and not isinstance(return_value, str):
            return_value = tuple(return_value)
        
        # update the cache/log with the real value
        recursion_help[object_id] = return_value
        #
        # handle placeholders
        #
        if is_iterable(return_value):
            # check if this value has any placeholder children
            children = return_value if not isinstance(return_value, dict) else [ *return_value.keys(), *return_value.values() ]
            for each in children:
                if isinstance(each, PlaceHolder):
                    parents_of_placeholders.add(return_value)
                    break
            # convert all the placeholders into their final values
            if top_level == True:
                for each_parent in parents_of_placeholders:
                    iterator = enumerate(each_parent) if not isinstance(each_parent, dict) else each_parent.items()
                    for each_key, each_value in iterator:
                        if isinstance(each_parent[each_key], PlaceHolder):
                            each_parent[each_key] = each_parent[each_key].eval()
                        # if the key is a placeholder
                        if isinstance(each_key, PlaceHolder):
                            value = each_parent[each_key]
                            del each_parent[each_key]
                            each_parent[each_key.eval()] = value
        
        # finally return the value
        return return_value

    def stringify(value, onelineify_threshold=None):
        if onelineify_threshold is None: onelineify_threshold = stringify.onelineify_threshold
        
        length = 0
        if isinstance(value, str):
            return repr(value)
        elif isinstance(value, dict):
            if len(value) == 0:
                return "{}"
            else:
                # if all string keys and all identifiers
                if all(isinstance(each, str) and each.isidentifier() for each in value.keys()):
                    items = value.items()
                    output = "dict(\n"
                    for each_key, each_value in items:
                        element_string = repr(each_key) + "=" + stringify(each_value)
                        length += len(element_string)+2
                        output += indent(element_string, by=4) + ", \n"
                    output += ")"
                    if length < onelineify_threshold:
                        output = output.replace("\n    ","").replace("\n","")
                    return output
                # more complicated mapping
                else:
                    items = value.items()
                    output = "{\n"
                    for each_key, each_value in items:
                        element_string = stringify(each_key) + ": " + stringify(each_value)
                        length += len(element_string)+2
                        output += indent(element_string, by=4) + ", \n"
                    output += "}"
                    if length < onelineify_threshold:
                        output = output.replace("\n    ","").replace("\n","")
                    return output
        elif isinstance(value, list):
            if len(value) == 0:
                return "[]"
            output = "[\n"
            for each_value in value:
                element_string = stringify(each_value)
                length += len(element_string)+2
                output += indent(element_string, by=4) + ", \n"
            output += "]"
            if length < onelineify_threshold:
                output = output.replace("\n    ","").replace("\n","")
            return output
        elif isinstance(value, set):
            if len(value) == 0:
                return "set([])"
            output = "set([\n"
            for each_value in value:
                element_string = stringify(each_value)
                length += len(element_string)+2
                output += indent(element_string, by=4) + ", \n"
            output += "])"
            if length < onelineify_threshold:
                output = output.replace("\n    ","").replace("\n","")
            return output
        elif isinstance(value, tuple):
            if len(value) == 0:
                return "tuple()"
            output = "(\n"
            for each_value in value:
                element_string = stringify(each_value)
                length += len(element_string)+2
                output += indent(element_string, by=4) + ", \n"
            output += ")"
            if length < onelineify_threshold:
                output = output.replace("\n    ","").replace("\n","")
            return output
        else:
            try:
                debug_string = value.__repr__()
            except Exception as error:
                from io import StringIO
                import builtins
                string_stream = StringIO()
                builtins.print(value, file=string_stream)
                debug_string = string_stream.getvalue()
            
            # TODO: handle "<slot wrapper '__repr__' of 'object' objects>"
            if debug_string.startswith("<class") and hasattr(value, "__name__"):
                return value.__name__
            if debug_string.startswith("<function <lambda>"):
                return "(lambda)"
            if debug_string.startswith("<function") and hasattr(value, "__name__"):
                return value.__name__
            if debug_string.startswith("<module") and hasattr(value, "__name__"):
                _, *file_path, _, _ = debug_string.split(" ")[-1]
                file_path = "".join(file_path)
                return f"module(name='{value.__name__}', path='{file_path}')"
            
            space_split = debug_string.split(" ")
            if len(space_split) >= 4 and debug_string[0] == "<" and debug_string[-1] == ">":
                
                if space_split[-1].startswith("0x") and space_split[-1] == "at":
                    _, *name_pieces = space_split[0]
                    *parts, name = "".join(name_pieces).split(".")
                    parts_str = ".".join(parts)
                    return f'{name}(from="{parts_str}")'
            
            return debug_string
    stringify.onelineify_threshold = 50
    
    def is_required_by(*args, **kwargs):
        """
            Summary:
                A way to know why a method function exists, and know if it can be renamed
                (A way of mapping out dependencies)
            
            Example:
                import custom_json_thing
                
                class Thing:
                    @is_required_by(custom_json_thing)
                    def to_json(self):
                        return "something"
                        
        """
        def decorator(function_being_wrapped):
            return function_being_wrapped
        return decorator
    
    def is_used_by(*args, **kwargs):
        """
            Summary:
                A way to know why a method function exists, and know if it can be renamed
                (A way of mapping out dependencies)
            
            Example:
                import custom_json_thing
                
                class Thing:
                    @is_used_by(custom_json_thing)
                    def to_json(self):
                        return "something"
                        
        """
        def decorator(function_being_wrapped):
            return function_being_wrapped
        return decorator

#
# iterative helpers
#
if True:
    def flatten(value):
        flattener = lambda *m: (i for n in m for i in (flattener(*n) if is_generator_like(n) else (n,)))
        return list(flattener(value))

    def iteratively_flatten_once(items):
        for each in items:
            if is_generator_like(each):
                yield from each
            else:
                yield each

    def flatten_once(items):
        return list(iteratively_flatten_once(items))
    
    def countdown(size=None, offset=0, delay=0, seconds=None):
        """
            Returns a function
                That function will return False until it has been called `size` times
                Then on the size-th time it returns True, and resets/repeats
        """
        import time
        if seconds:
            def _countdown():
                    
                now = time.time()
                # init
                if _countdown.marker is None:
                    _countdown.marker = now
                # enough time has passed
                if _countdown.marker + seconds <= now:
                    _countdown.marker = now
                    return True
                else:
                    return False
            _countdown.marker = None
            return _countdown
        else:
            remaining = size
            def _countdown():
                _countdown.remaining -= 1
                if _countdown.remaining + offset <= 0:
                    # restart
                    _countdown.remaining = size - offset
                    return True
                else:
                    return False
            _countdown.remaining = size + delay
            _countdown.size = size
            return _countdown

    def bundle(iterable, bundle_size):
        next_bundle = []
        for each in iterable:
            next_bundle.append(each)
            if len(next_bundle) >= bundle_size:
                yield tuple(next_bundle)
                next_bundle = []
        # return any half-made bundles
        if len(next_bundle) > 0:
            yield tuple(next_bundle)

    def wrap_around_get(index, a_list):
        """
            given an in-bound index will return that element
            given an out-of-bound index, it will treat the list as if it were circular and infinite and get the corrisponding value
        """
        list_length = len(a_list)
        return a_list[((index % list_length) + list_length) % list_length]

    def shuffled(a_list):
        from random import shuffle
        new_list = list(a_list)
        shuffle(new_list)
        return new_list
    
    import itertools
    def permutate(possibilities, digits=None):
        # TODO:
            # possibilities-per-digit
            # combinations
            # powerset
            # fixed length
            # variable length
        
        # without repeats
        if type(digits) == type(None):
            yield from itertools.permutations(possibilities)
        # with repeats
        else:
            if digits == 1:
                for each in possibilities:
                    yield [ each ]
            elif digits > 1:
                for each_subcell in permutate(possibilities, digits-1):
                    for each in possibilities:
                        yield [ each ] + each_subcell
            # else: dont yield anything

    def randomly_pick_from(a_list):
        from random import randint
        index = randint(0, len(a_list)-1)
        return a_list[index]

    import collections.abc
    def merge(old_value, new_value):
        # if not dict, see if it is iterable
        if not isinstance(new_value, collections.abc.Mapping):
            if is_generator_like(new_value):
                new_value = { index: value for index, value in enumerate(new_value) }
        
        # if still not a dict, then just return the current value
        if not isinstance(new_value, collections.abc.Mapping):
            return new_value
        # otherwise get recursive
        else:
            # if not dict, see if it is iterable
            if not isinstance(old_value, collections.abc.Mapping):
                if is_iterable(old_value):
                    old_value = { index: value for index, value in enumerate(old_value) }
            # if still not a dict
            if not isinstance(old_value, collections.abc.Mapping):
                # force it to be one
                old_value = {}
            
            # override each key recursively
            for key, updated_value in new_value.items():
                old_value[key] = merge(old_value.get(key, {}), updated_value)
            
            return old_value

    def recursively_map(an_object, function, is_key=False):
        """
            inputs:
                the function should be like: lambda value, is_key: value if is_key else (f"{value}") # convert all values to strings
            explaination:
                this will be recursively called on all elements of iterables (and all key/values of dictionaries)
                - the deepest elements (primitives) are done first
                - there is no object-contains-itself checking yet (TODO)
            outputs:
                a copy of the original value
        """
        # base case 1 (iterable but treated like a primitive)
        if isinstance(an_object, (str, bytes)):
            return_value = an_object
        # base case 2 (exists because of scalar numpy/pytorch/tensorflow objects)
        if hasattr(an_object, "tolist"):
            return_value = an_object.tolist()
        else:
            # base case 3
            if not is_iterable(an_object):
                return_value = an_object
            else:
                if isinstance(an_object, dict):
                    return_value = { recursively_map(each_key, function, is_key=True) : recursively_map(each_value, function) for each_key, each_value in an_object.items() }
                else:
                    return_value = [ recursively_map(each, function) for each in an_object ]
        
        # convert lists to tuples so they are hashable
        if is_iterable(return_value) and not isinstance(return_value, dict) and not isinstance(return_value, str):
            return_value = tuple(return_value)
        
        return function(return_value, is_key=is_key)

    def all_equal(a_list):
        if len(a_list) == 0:
            return True
        
        prev = a_list[0]
        for each in a_list[1:]:
            if prev != each:
                return False
            prev = each
        
        return True

    def all_different(a_list):
        if len(a_list) == 0:
            return True
        
        prev = a_list[0]
        for each in a_list[1:]:
            if prev == each:
                return False
            prev = each
        
        return True

# 
# math related
# 
if True:
    def log_scale(number):
        import math
        if number > 0:
            return math.log(number+1)
        else:
            return -math.log((-number)+1)

    def integers(*, start, end_before, step=1):
        return list(range(start, end_before, step))

    def product(iterable):
        from functools import reduce
        import operator
        return reduce(operator.mul, iterable, 1)

    def max_index(iterable):
        iterable = tuple(iterable)
        if len(iterable) == 0:
            return None
        max_value = max(iterable)
        from random import sample
        options = tuple( each_index for each_index, each in enumerate(iterable) if each == max_value )
        return sample(options, 1)[0]
    
    def max_indices(iterable):
        iterable = tuple(iterable)
        if len(iterable) == 0:
            return None
        max_value = max(iterable)
        return tuple( each_index for each_index, each in enumerate(iterable) if each == max_value )
    
    def arg_max(*, args, values):
        values = tuple(values)
        if len(values) == 0:
            return None
        max_value = max(values)
        from random import sample
        options = tuple( arg for arg, value in zip(args, values) if value == max_value )
        return sample(options, 1)[0]
    
    def arg_maxs(*, args, values):
        values = tuple(values)
        if len(values) == 0:
            return None
        max_value = max(values)
        return tuple( arg for arg, value in zip(args, values) if value == max_value )

    def average(iterable):
        from statistics import mean
        from trivial_torch_tools.generics import to_pure
        return mean(tuple(to_pure(each) for each in iterable))

    def median(iterable):
        from statistics import median
        from trivial_torch_tools.generics import to_pure
        return median(tuple(to_pure(each) for each in iterable))

    def stats(number_iterator):
        import math
        from statistics import stdev, median, quantiles
        
        minimum = math.inf
        maximum = -math.inf
        total = 0
        values = [] # for iterables that get consumed
        for each in number_iterator:
            values.append(to_pure(each))
            total += each
            if each > maximum:
                maximum = each
            if each < minimum:
                minimum = each
        
        count = len(values)
        range = maximum-minimum
        average     = total / count     if count != 0 else None
        median      = median(values)    if count != 0 else None
        stdev       = stdev(values)     if count  > 1 else None
        normalized  = tuple((each-minimum)/range for each in values) if range != 0 else None
        (q1,_,q3),_ = quantiles(values) if count  > 1 else (None,None,None),None
        
        return Object(
            max=maximum,
            min=minimum,
            range=range,
            count=count,
            sum=total,
            average=average,
            stdev=stdev,
            median=median,
            q1=q1,
            q3=q3,
            normalized=normalized,
        )    

    def normalize(values, max, min):
        """
            all elements of the output should be between 0 and 1
            if there's no difference between the max an min, it outputs all 0's
        """
        reward_range = max - min
        if reward_range == 0:
            return tuple(0 for each in values)
        else:
            return tuple((each - min)/reward_range for each in values)

    def rolling_average(a_list, window):
        results = []
        if len(a_list) < window * 2:
            return a_list
        near_the_end = len(a_list) - 1 - window 
        for index, each in enumerate(a_list):
            # at the start
            if index < window:
                average_items = a_list[0:index]+a_list[index:index+window]
            # at the end
            elif index > near_the_end:
                average_items = a_list[index-window:index]+a_list[index:len(a_list)]
            else:
                # this could be done a lot more efficiently with a rolling sum, oh well! ¯\_(ツ)_/¯ 
                average_items = a_list[index-window:index+window+1]
            # fallback
            if len(average_items) == 0:
                average_items = [ a_list[index] ]
            results.append(sum(average_items)/len(average_items))
        return results

    def points_to_function(x_values, y_values):
        # method="linear"
        values = list(zip(x_values, y_values))
        values.sort(reverse=False, key=lambda each: each[0])
        def shift_towards(*, new_value, old_value, proportion):
            if proportion == 1:
                return new_value
            if proportion == 0:
                return old_value
            
            difference = new_value - old_value
            amount = difference * proportion
            return old_value+amount
        
        def new_function(x_input):
            prev_x, prev_y = values[0]
            if x_input <= prev_x: # x_input is outside of the bounds
                return prev_y 
            max_x, max_y = values[-1]
            if x_input >= max_x: # x_input is outside of the bounds
                return max_y
            
            for each_x, each_y in values:
                # they must not be equal, so skip
                if each_x == prev_x:
                    continue
                
                if each_x == x_input:
                    return each_y
                elif each_x > x_input > prev_x:
                    the_range = each_x - prev_x
                    relative_amount = x_input - prev_x
                    propotion = relative_amount/the_range
                    return shift_towards(new_value=each_x, old_value=prev_x, propotion=propotion)
                
                prev_x = each_x
                prev_y = each_y
            
            # if its a vertical line or only has one point, this line will run
            return prev_y
                    
        return new_function
# 
# time
#
if True: 
    import time
    
    def unix_time():
        return int(time.time()/1000)
    
    @singleton
    class Time:
        prev = time.time()
        
        @property
        def unix(self):
            return int(time.time()/1000)
        
        @property
        def time_since_prev_call(self):
            current = time.time()
            output = current-prev
            Time.prev = current
            return output
    
    class Timer:
        prev = None
        def __init__(self, name="", *, silence=False, **kwargs):
            self.name = name
            self.silence = silence
        
        def __enter__(self):
            self.start_time = int(time.time()/1000)
            return self
        
        def __exit__(self, _, error, traceback):
            self.end_time = int(time.time()/1000)
            self.duration = self.end_time - self.start_time
            if not self.silence:
                print(f"{self.name} took {self.duration}ms")
            Timer.prev = self
            if error is not None:
                # error cleanup HERE
                raise error

# 
# colors
# 
if True:
    class Colors:
        """
        Example:
            theme = Colors(dict(red="#000",blue="#000",))
            
            # index that wraps-around
            theme[0]      # returns red
            theme[1]      # returns blue
            theme[2]      # returns red
            theme[109320] # returns a valid color (keeps wrapping-around)
            
            # names
            theme.red     # returns the value for red
            
            # iteration
            for each_color in theme:
                 print(each_color) # outputs "#000"
        """
        def __init__(self, color_mapping):
            self._color_mapping = color_mapping
            for each_key, each_value in color_mapping.items():
                if isinstance(each_key, str) and len(each_key) > 0 and each_key[0] != '_':
                    setattr(self, each_key, each_value)
        
        def __getitem__(self, key):
            if isinstance(key, int):
                return wrap_around_get(key, list(self._color_mapping.values()))
            elif isinstance(key, str):
                return self._color_mapping.get(key, None)
        
        def __repr__(self):
            return stringify(self._color_mapping)
        
        def __iter__(self):
            for each in self._color_mapping.values():
                yield each
    
# 
# print helpers
# 
if True:
    # 
    # print that can be indented or temporarily disabled
    # 
    real_print = print
    def print(*args, to_string=False, disable=False, **kwargs): # print(value, ..., sep=' ', end='\n', file=sys.stdout, flush=False)
        prev_end = print.prev_end
        print.prev_end = kwargs.get('end', '\n') or ''
        
        from io import StringIO
        if to_string:
            string_stream = StringIO()
            # dump to string
            real_print(*args, **{ "flush": True, **kwargs, "file":string_stream })
            output_str = string_stream.getvalue()
            string_stream.close()
            return output_str
            
        if disable or hasattr(print, "disable") and print.disable.always:
            return
            
        if hasattr(print, "indent"):
            if print.indent.size > 0:
                import json
                indent = print.indent.string*print.indent.size
                # dump to string
                output_str = print(*args, **{ **kwargs, "to_string":True})
                end_value = kwargs.get("end", '\n')
                if len(end_value) > 0:
                    output_str = output_str[0:-len(end_value)]
                # indent any contained newlines 
                if "\n" in output_str:
                    output_str = output_str.replace("\n", "\n"+indent)
                # starting indent depending on previous ending
                if len(prev_end) > 0 and prev_end[-1] in ('\n', '\r'):
                    output_str = indent + output_str
                
                # print it
                return real_print(output_str, **{ "flush": print.flush.always, **kwargs, }) 
        
        return real_print(*args, **{ "flush": print.flush.always, **kwargs})
    print.prev_end = '\n'

    class WithNothing(object):
        def __init__(*args, **kwargs):
            pass
        
        def __enter__(self):
            return None
        
        def __exit__(self, _, error, traceback):
            if error is not None:
                raise error
    with_nothing = WithNothing()

    class _Indent(object):
        """
        with print.indent:
            print("howdy1")
            with print.indent:
                print("howdy2")
            print("howdy3")
        """
        def __init__(self, *args, **kwargs):
            self.indent_before = []
        
        def __enter__(self):
            self.indent_before.append(print.indent.size)
            print.indent.size += 1
            return print
        
        def __exit__(self, _, error, traceback):
            # restore prev indent
            print.indent.size = self.indent_before.pop()
            if error is not None:
                # error cleanup HERE
                raise error
        
        def function(self, function_being_wrapped):
            """
            Example:
                @print.indent.function
                def some_function(arg1):
                    print("this is indented")
            """
            def wrapper(*args, **kwargs):
                original_value = print.indent.size
                print.indent.size += 1
                output = function_being_wrapped(*args, **kwargs)
                print.indent.size = original_value
                return output
            return wrapper
        
        def block(self, *args, disable=False):
            """
            Examples:
                with block("staring iterations"):
                    print("this is indented")
                
                with block("staring iterations", disable=True):
                    print("this is indented")
            """
            print(*args, disable=disable)
            if not disable:
                return print.indent
            else:
                return with_nothing
        
        def function_block(self,function_being_wrapped):
            """
            Example:
                @print.indent.function_block
                def some_function(arg1):
                    print("this is indented, and has the name of the function above it")
            """
            def wrapper(*args, **kwargs):
                original_value = print.indent.size
                if hasattr(function_being_wrapped, "__name__"):
                    print(function_being_wrapped.__name__)
                print.indent.size += 1
                output = function_being_wrapped(*args, **kwargs)
                print.indent.size = original_value
                return output
            return wrapper

    def _print_function(create_message=None, *, disable=False):
        """
        Examples:
            @print.function()
            def some_function(arg1):
                print("this is indented, and has the name of the function above it")
            
            @print.function(disable=True)
            def some_function(arg1):
                print("this will print, but wont be intended")
            
            @print.function(disable=lambda : True)
            def some_function(arg1):
                print("this will print, but wont be intended")
            
            @print.function(lambda func, arg1: f"{func.__name__}({arg1})")
            def some_function(arg1):
                print("this is indented, and above is func name and arg")
            
            @print.function(lambda func, *args: f"{func.__name__}{args}")
            def some_function(arg1, arg2, arg3):
                print("this is indented, and above is func name and all the args")
        """
        disable_check = disable if callable(disable) else lambda : disable
        def decorator_name(function_being_wrapped):
            def wrapper(*args, **kwargs):
                disabled = disable_check()
                if disabled:
                    return function_being_wrapped(*args, **kwargs)
                else:
                    original_value = print.indent.size
                    if not create_message:
                        if hasattr(function_being_wrapped, "__name__"):
                            print(f"{function_being_wrapped.__name__}(...)")
                    else:
                        print(create_message(function_being_wrapped, *args, **kwargs))
                    print.indent.size += 1
                    output = function_being_wrapped(*args, **kwargs)
                    print.indent.size = original_value
            return wrapper

    print.function = _print_function    
    print.indent  = _Indent()
    print.flush   = Object()
    print.disable = Object()
    print.indent.string = "    "
    print.indent.size = 0
    print.flush.always = True
    print.disable.always = False

    def apply_to_selected(func, which_args, args, kwargs):
        if which_args == ...:
            new_args = tuple(func(each) for each in args)
            new_kwargs = { each_key : func(each_value) for each_key, each_value in kwargs.items() }
            return new_args, new_kwargs
        else:
            # todo: probably make this more flexible
            which_args = tuple(which_args)
            
            new_args = []
            for index, each in enumerate(args):
                if index in which_args:
                    new_args[index].append(func(each))
                else:
                    new_args[index].append(each)
                
            new_kwargs = {}
            for key, value in kwargs.items():
                if key in which_args:
                    new_kwargs[key].append(func(value))
                else:
                    new_kwargs[key].append(value)
            
            return new_args, new_kwargs

# 
# 
# serialization
# 
# 
if True:
    # 
    # python pickle
    # 
    if True:
        def large_pickle_load(file_path):
            """
            This is for loading really big python objects from pickle files
            ~4Gb max value
            """
            import pickle
            import os
            max_bytes = 2**31 - 1
            bytes_in = bytearray(0)
            input_size = os.path.getsize(file_path)
            with open(file_path, 'rb') as f_in:
                for _ in range(0, input_size, max_bytes):
                    bytes_in += f_in.read(max_bytes)
            output = pickle.loads(bytes_in)
            return output

        def large_pickle_save(variable, file_path):
            """
            This is for saving really big python objects into a file
            so that they can be loaded in later
            ~4Gb max value
            """
            import file_system_py as FS
            import pickle
            bytes_out = pickle.dumps(variable, protocol=4)
            max_bytes = 2**31 - 1
            FS.clear_a_path_for(file_path, overwrite=True)
            with open(file_path, 'wb') as f_out:
                for idx in range(0, len(bytes_out), max_bytes):
                    f_out.write(bytes_out[idx:idx+max_bytes])
    
    # 
    # json
    # 
    if True: 
        import json

        # fallback method
        json.fallback_table[lambda obj: True ] = lambda obj: to_pure(obj)

        # 
        # pandas
        # 
        try:
            import pandas as pd
            json.fallback_table[lambda obj: isinstance(obj, pd.DataFrame)] = lambda obj: json.loads(obj.to_json())
        except ImportError as error:
            pass
        
        class Json:
            @staticmethod
            def read(path):
                with open(path, 'r') as in_file:
                    return json.load(in_file)
            
            @staticmethod
            def write(data, path):
                with open(path, 'w') as outfile:
                    json.dump(data, outfile)
    # 
    # csv
    # 
    class Csv:
        # reads .csv, .tsv, etc 
        @staticmethod
        def read(path=None, *, string=None, seperator=",", first_row_is_column_names=False, column_names=None, skip_empty_lines=True, comment_symbol=None):
            """
                Examples:
                    comments, column_names, rows = csv.read("something/file.csv", first_row_is_column_names=True, comment_symbol="#")
                    comments, _empty_list, rows = csv.read("something/file.csv", first_row_is_column_names=False)
                    comments, column_names_from_file, rows = csv.read(
                        "something/file.csv",
                        column_names=["column1_new_name"],
                        first_row_is_column_names=True,
                    )
                Summary:
                    Reads in CSV's
                    - Converts numbers, null, booleans, etc into those types in accordance with JSON
                    (e.g. null=>None, true=>True, 2.3e31=>float, "hi\n"=>str('hi\n'))
                    - Anything that is not json-parsable is kept as a string
                    - Comments can be enabled by with the comment_symbol arg
                    - Comments must start as the first character of a line, no trailing comments
                    - Blank spaces (e.g. ,,, ) are converted to None (e.g. ,null,null,)
                    - Read() will sill parse even if some lines are missing columns
                Returns:
                    value: tuple(comments, column_names, rows)
                    rows:
                        - Always returns a list
                        - Each element is a named list
                        - Named lists inherit from lists (full backwards compatibility)
                        - Named lists may also be accessed using column_names
                        for example: rows[0]["column1"] and rows[0].column1 are both valid
                    column_names:
                        - Will always return an empty list when first_row_is_column_names=False
                        - Will always be the column names according to the file (even if overridden)
                        - Every element in the list will be a string
                    comments:
                        - A list of strings
                        - One string per line
                        - The comment_symbol itself is removed from the string
                    
                Arguments:
                    path:
                        - Any string path or path-object
                        - Will throw error if file does not exist
                    first_row_is_column_names:
                        - Boolean, default is False
                        - If true all elements in the first row will be parsed as strings (even if they look like numbers/null)
                        - Not all columns need a name
                        - However using the same name twice or more will cause problems
                    column_names:
                        - Optional, a list of strings
                        - Will override the column_names within the file if provided
                        - Doesn't need to cover all columns (trailing columns can be unnamed)
                    skip_empty_lines:
                        - Boolean, default is True
                        - A line with spaces or tabs will still qualify as empty
                    
            """
            import json
            
            comments     = []
            rows         = []
            file_column_names = []
            is_first_data_row = True
            
            def handle_line(each_line):
                nonlocal comments, rows, file_column_names, is_first_data_row
                # remove all weird whitespace as a precaution
                each_line = each_line.replace("\r", "").replace("\n", "")
                
                # 
                # comments
                # 
                if comment_symbol:
                    if each_line.startswith(comment_symbol):
                        comments.append(each_line[len(comment_symbol):])
                        return
                
                # 
                # empty lines
                # 
                if skip_empty_lines and len(each_line.strip()) == 0:
                    return
                
                # 
                # cell data
                #
                cells = each_line.split(seperator)
                cells_with_types = []
                skip_to = 0
                for index, each_cell in enumerate(cells):
                    # apply any "skip_to" (which would be set by a previous loop)
                    if index < skip_to:
                        continue
                    
                    stripped = each_cell.strip()
                    if len(stripped) == 0:
                        cells_with_types.append(None)
                    else:
                        first_char = stripped[0]
                        if not (first_char == '"' or first_char == '[' or first_char == '{'):
                            # this converts scientific notation to floats, ints with whitespace to ints, null to None, etc
                            try: cells_with_types.append(json.loads(stripped))
                            # if its not valid JSON, just treat it as a string
                            except Exception as error:
                                cells_with_types.append(stripped)
                        else: # if first_char == '"' or first_char == '[' or first_char == '{'
                            # this gets complicated because strings/objects/lists could contain an escaped seperator
                            remaining_end_indicies = reversed(list(range(index, len(cells))))
                            skip_to = 0
                            for each_remaining_end_index in remaining_end_indicies:
                                try:
                                    cells_with_types.append(
                                        json.loads(seperator.join(cells[index:each_remaining_end_index]))
                                    )
                                    skip_to = each_remaining_end_index
                                    break
                                except Exception as error:
                                    pass
                            # continue the outer loop
                            if skip_to != 0:
                                continue
                            else:
                                # if all fail, go with the default of the shortest cell as a string
                                cells_with_types.append(each_cell)
                
                # 
                # file_column_names
                # 
                if is_first_data_row:
                    is_first_data_row = False
                    if first_row_is_column_names:
                        file_column_names = [ str(each) for each in cells_with_types ]
                        return
                
                rows.append(cells_with_types)
            
            if path:
                with open(path,'r') as file:
                    for each_line in file.readlines():
                        handle_line(each_line)
            elif string: 
                for each_line in string.splitlines():
                    handle_line(each_line)
            
            # if file_column_names
            if first_row_is_column_names or column_names:
                RowItem = create_named_list_class(column_names or file_column_names)
                # tranform each into a named list (backwards compatible with regular list)
                rows = [ RowItem(each_row) for each_row in rows ]
            
            return comments, file_column_names, rows

        @staticmethod
        def write(path=None, *, rows=tuple(), column_names=tuple(), seperator=",", eol="\n", comment_symbol=None, comments=tuple()):
            import json
            import sys
            assert comment_symbol or len(comments) == 0, "Comments were provided,"
            def contains_comment_symbol(string):
                if not comment_symbol:
                    return False
                else:
                    return comment_symbol in string
            
            def element_to_string(element):
                # strings are checked for seperators, if no seperators or whitespace, then unquoted
                if isinstance(element, str):
                    if not (
                        contains_comment_symbol(element) or
                        len(element.strip()) != len(element) or
                        seperator in element or
                        eol in element or
                        '\n' in element or
                        '\r' in element or 
                        element.startswith("{") or # because of JSON objects
                        element.startswith("[")    # because of JSON objects
                    ):
                        # no need for quoting
                        return element
                # all other values are stored in json format
                try:
                    return json.dumps(element)
                except Exception as error:
                    return f"{element}"
            
            def break_up_comments(comments):
                for each in comments:
                    yield from f"{each}".replace("\r", "").split("\n")
            
            the_file = sys.stdout if not path else open(path, 'w+')
            def close_file():
                if the_file != sys.stdout and the_file != sys.stderr:
                    try: the_file.close()
                    except: pass
            try:
                # 
                # comments
                # 
                the_file.write(
                    eol.join([ f"{comment_symbol}{each}" for each in break_up_comments(comments) ])
                )
                if len(comments) > 0:
                    the_file.write(eol)
                
                # 
                # column_names
                # 
                if len(column_names) > 0:
                    the_file.write(
                        seperator.join(tuple(
                            element_to_string(str(each)) for each in column_names 
                        ))+eol
                    )
                
                # 
                # rows
                # 
                for each_row in rows:
                    if isinstance(each_row, str):
                        the_file.write(each_row+eol)
                    else:
                        row_string_escaped = tuple(
                            element_to_string(each_cell)
                                for each_cell in each_row 
                        )
                        line = seperator.join(row_string_escaped)+eol
                        the_file.write(
                            seperator.join(row_string_escaped)+eol
                        )
            except Exception as error:
                # make sure to close the file
                close_file()
                raise error
            
            close_file()
    

# 
# 
# value conversion
# 
#
if True: 
    def to_numpy(value):
        import numpy
        
        # torch tensor
        if hasattr(value, "__class__") and hasattr(value.__class__, "__name__"):
            if value.__class__.__name__ == "Tensor":
                try:
                    import torch
                    if isinstance(value, torch.Tensor):
                        return value.detach().cpu().numpy()
                except Exception as error:
                    pass
        return numpy.array(to_pure(value))

# 
# 
# Console
# 
# 
@singleton
class Console:
    
    @singleton
    class foreground:
        black          = 30
        red            = 31
        green          = 32
        yellow         = 33
        blue           = 34
        magenta        = 35
        cyan           = 36
        white          = 37
        bright_black   = 90
        bright_red     = 91
        bright_green   = 92
        bright_yellow  = 93
        bright_blue    = 94
        bright_magenta = 95
        bright_cyan    = 96
        bright_white   = 97
    
    @singleton
    class background:
        black          = 40
        red            = 41
        green          = 42
        yellow         = 43
        blue           = 44
        magenta        = 45
        cyan           = 46
        white          = 47
        bright_black   = 100
        bright_red     = 101
        bright_green   = 102
        bright_yellow  = 103
        bright_blue    = 104
        bright_magenta = 105
        bright_cyan    = 106
        bright_white   = 107
    
    def color(self, string, foreground="white", background="black"):
        import sys
        # if outputing to a file, dont color anything
        if not sys.stdout.isatty():
            return string
        
        # TODO: detect windows/WSL and disable colors (because powershell and CMD are problematic)
        
        foreground_number = getattr(Console.foreground, foreground, None)
        background_number = getattr(Console.background, background, None)
        
        if foreground_number == None:
            raise Exception(f"couldn't find foreground color {foreground}\nAvailable colors are: {attributes(Console.foreground)}")
        if background_number == None:
            raise Exception(f"couldn't find background color {background}\nAvailable colors are: {attributes(Console.background)}")
        
        foreground_code = f"\u001b[{foreground_number}m"
        background_code = f"\u001b[{background_number}m"
        reset_code = f"\u001b[0m"
        return foreground_code+background_code+str(string)+reset_code
    
    def clear(self,):
        print(chr(27) + "[2J")      # erase everything
        print(chr(27) + "[1;1f")    # reset cursor position
    
    def run(self, *args, timeout_sec=None):
        """
            Example:
                stdout, stderr, exit_code = Console.run("echo", "hello", timeout_sec=30)
        """
        from subprocess import Popen, PIPE
        from threading import Timer
        
        proc = Popen(list(args), stdout=PIPE, stderr=PIPE)
        timer = None
        if timeout_sec:
            timer = Timer(timeout_sec, proc.kill)
        try:
            if timer:
                timer.start()
            stdout, stderr = proc.communicate()
            stdout = stdout.decode('utf-8')[0:-1]
            stderr = stderr.decode('utf-8')[0:-1]
            return stdout, stderr, proc.returncode
        finally:
            if timer:
                timer.cancel()
        return None, None, None

    
    class output_redirected_to:
        def __init__(self, file=None, filepath=None):
            import sys
            
            self.filepath = filepath
            
            if self.filepath:
                FS.ensure_is_folder(self.filepath)
                self.file = open(self.filepath, "w")
            else:
                self.file = file
                
            self.real_stdout = sys.stdout
            self.real_stderr = sys.stderr
            sys.stdout = self.file
            sys.stderr = self.file
        
        def __enter__(self):
            return self
        
        def __exit__(self, _, error, traceback):
            if error is not None:
                import traceback
                traceback.print_exc()
            
            sys.stdout = self.real_stdout
            sys.stderr = self.real_stderr
            if self.filepath:
                self.file.close()