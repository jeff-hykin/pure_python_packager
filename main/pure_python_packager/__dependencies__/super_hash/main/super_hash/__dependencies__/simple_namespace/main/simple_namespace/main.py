def namespace(function):
    """
    Examples:
        @namespace
        def MyNamespace():
            my_value = 10
            def my_function(arg1):
                return 99
            
            return locals()
        
        print(MyNamespace.my_value) # prints 10
    """
    the_locals = function()
    if not isinstance(the_locals, dict):
        raise Exception('When creating a namespace, the function needs to return `locals()` or some other kind of dictionary')
    # turn the dictionary into an object/singleton
    class AttrDict:
        def __init__(self, a_dict):
            self.__dict__ = a_dict
    return AttrDict(the_locals)
