import RestrictedPython
import math
import random

def getitem(obj, index):
    if obj is not None and type(obj) in (list, tuple, dict):
        return obj[index]
    raise Exception()

restricted_globals = {
    '__builtins__': RestrictedPython.Guards.safe_builtins,
    '_print_': RestrictedPython.PrintCollector,
    '_getattr_': RestrictedPython.Guards.safer_getattr,
    '_getitem_': getitem,
    '_write_': RestrictedPython.Guards.full_write_guard,
    'math': math,
    'random': random,
}

restricted_locals = {
}

source_code = """
def pattern(t, dt, x, y, prev_state):
    return (t + x, 0, prev_state[0])
"""

byte_code = RestrictedPython.compile_restricted_exec(
    source_code,
    filename='<inline code>'
)
print(byte_code)
print(exec(byte_code[0], restricted_globals, restricted_locals))

print(restricted_locals['pattern'](0.5, 0.01, 0.2, 0.2, (1, 2)))

