# led-control WS2812B LED Controller Server
# Copyright 2021 jackw01. Released under the MIT License (see LICENSE for details).

import re
import math
import colorsys

# Constrain value
def clamp(x, min, max):
    if x < min:
        return min
    elif x > max:
        return max
    else:
        return x

# Title generation

def camel_to_title(text):
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', text)

def snake_to_title(text):
    return text.replace('_', ' ').title()

# Misc shaping functions

# Exponential asymmetric impulse function - peaks at t=1
# See http://www.iquilezles.org/www/articles/functions/functions.htm
def impulse_exp(t):
    return t * math.exp(1 - t)

# Equivalent to GLSL fract - returns the floating point component of a number
def fract(x):
    return x - math.floor(x)
