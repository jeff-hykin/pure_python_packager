from super_hash import *

class THingy():
    pass


exec("""
def thing():
    pass
""")

def static_nice_function():
    pass
    
function_hashers.smart(static_nice_function)
function_hashers.smart(thing)
function_hashers.smart(THingy)

# from super_hash import super_hash as hash
value = {
    frozenset({
        frozenset({
            "key-deep-deep": 10
        }.items()): "key-deep",
    }.items()): "first_value",
    "second_value": [
        {"a": 10},
    ]
}
print(super_hash(value))