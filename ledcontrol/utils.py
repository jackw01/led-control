# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

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

# Waveforms for pattern generation. All have a period of 2 time units and range from 0-1.
# Sawtooth wave is just (t % 1)

# Square/pulse wave - this should run pretty fast?
def wave_pulse(t, duty_cycle=0.5):
    return math.ceil(duty_cycle - (t % 1))

# Triangle wave
def wave_triangle(t):
    return math.fabs(((2 * t) % 2) - 1)

# Sine wave - should test speed of approximation methods
def wave_sine(t):
    return math.sin(2 * math.pi * (t + 0.25)) / 2 + 0.5 # 2 * math.pi * t + 0.5 * math.pi

# Misc shaping functions

# Exponential asymmetric impulse function - peaks at t=1
# See http://www.iquilezles.org/www/articles/functions/functions.htm
def impulse_exp(t):
    return t * math.exp(1 - t)

# Equivalent to GLSL fract - returns the floating point component of a number
def fract(x):
    return x - math.floor(x)

# HSV to RGB transforms (normalized HSV to 8 bit RGB)

# Using colorsys
def hsv2rgb_colorsys(triplet):
    return [int(x * 255) for x in colorsys.hsv_to_rgb(triplet[0] % 1, triplet[1], triplet[2])]

# Marginally faster than colorsys
def hsv2rgb_fast(triplet):
    (hue, sat, val) = [int(x * 255) for x in triplet]
    hue = hue % 255

    if sat == 0:
        return (val, val, val)

    brightness_floor = val * (255 - sat) // 256
    color_amplitude = val - brightness_floor
    section = hue // 85
    offset = hue % 85
    rampup_adj_with_floor = offset * color_amplitude // 64 + brightness_floor
    rampdown_adj_with_floor = (85 - 1 - offset) * color_amplitude // 64 + brightness_floor

    if section:
        if section == 1:
            return [brightness_floor, rampdown_adj_with_floor, rampup_adj_with_floor]
        else:
            return [rampup_adj_with_floor, brightness_floor, rampdown_adj_with_floor]
    else:
        return [rampdown_adj_with_floor, rampup_adj_with_floor, brightness_floor]

# "Rainbow" color transform from FastLED, also marginally faster than colorsys
def hsv2rgb_fast_rainbow(triplet):
    (hue, sat, val) = [int(x * 255) for x in triplet]
    hue = hue % 255

    offset = hue & 0x1F # 0 to 31
    offset8 = offset << 3
    third = offset8 // 3 # max = 85

    r = 0
    g = 0
    b = 0

    if not (hue & 0x80):
        # 0XX
        if not (hue & 0x40):
            # 00X
            # section 0-1
            if not (hue & 0x20):
                # 000
                # case 0: # R -> O
                r = 255 - third
                g = third
                b = 0
            else:
                # 001
                # case 1: # O -> Y
                r = 171
                g = 85 + third
                b = 0
        else:
            # 01X
            # section 2-3
            if not (hue & 0x20):
                # 010
                # case 2: # Y -> G
                twothirds = offset8 * 2 // 3 # max=170
                r = 171 - twothirds
                g = 170 + third
                b = 0
            else:
                # 011
                # case 3: # G -> A
                r = 0
                g = 255 - third
                b = third
    else:
        # section 4-7
        # 1XX
        if not (hue & 0x40):
            # 10X
            if not (hue & 0x20):
                # 100
                # case 4: # A -> B
                r = 0
                twothirds = offset8 * 2 // 3 # max=170
                g = 171 - twothirds
                b = 85 + twothirds
            else:
                # 101
                # case 5: # B -> P
                r = third
                g = 0
                b = 255 - third
        else:
            if not (hue & 0x20):
                # 110
                # case 6: # P -- K
                r = 85 + third
                g = 0
                b = 171 - third
            else:
                # 111
                # case 7: # K -> R
                r = 170 + third
                g = 0
                b = 85 - third

    # This is one of the good places to scale the green down,
    # although the client can scale green down as well.
    # g = g >> 1

    # Scale down colors if we're desaturated at all
    # and add the brightness_floor to r, g, and b.
    if sat != 255:
        if sat == 0:
            r = 255
            b = 255
            g = 255
        else:
            desat = 255 - sat
            desat = desat * desat // 255
            r = r * sat // 255 + desat
            g = g * sat // 255 + desat
            b = b * sat // 255 + desat

    # Now scale everything down if we're at value < 255.
    if val != 255:
        val * val // 255
        if val == 0:
            r = 0
            g = 0
            b = 0
        else:
            r = r * val // 255
            g = g * val // 255
            b = b * val // 255

    return [r, g, b]

# Color temperature to RGB conversion
def blackbody2rgb(kelvin):
    # See http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/

    kelvin = clamp(kelvin, 1000, 40000)
    tmp_internal = kelvin / 100.0

    r = 0
    g = 0
    b = 0

    if tmp_internal <= 66:
        r = 255
        g = int(clamp(99.47080 * math.log(tmp_internal) - 161.11957, 0, 255))
    else:
        r = int(clamp(329.69873 * math.pow(tmp_internal - 60, -0.13320), 0, 255))
        g = int(clamp(288.12217 * math.pow(tmp_internal - 60, -0.07551), 0, 255))

    if tmp_internal >= 66:
        b = 255
    elif tmp_internal <= 19:
        b = 0
    else:
        b = int(clamp(138.51773 * math.log(tmp_internal - 10) - 305.04479, 0, 255))

    return [r, g, b]

# Color temperature to RGB conversion (more accurate)
def blackbody2rgb_2(kelvin):
    # See http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
    # See http://www.zombieprototypes.com/?p=210

    kelvin = clamp(kelvin, 1000, 40000)
    tmp_internal = kelvin / 100.0

    r = 0
    g = 0
    b = 0

    if tmp_internal <= 66:
        xg = tmp_internal - 2
        r = 255
        g = int(clamp(-155.25485 - 0.44596 * xg + 104.49216 * math.log(xg), 0, 255))
    else:
        xr = tmp_internal - 55
        xg = tmp_internal - 50
        r = int(clamp(351.97691 + 0.11421 * xr - 40.25366 * math.log(xr), 0, 255))
        g = int(clamp(325.44941 + 0.07943 * xg - 28.08529 * math.log(xg), 0, 255))

    if tmp_internal >= 66:
        b = 255
    elif tmp_internal <= 19:
        b = 0
    else:
        xb = tmp_internal - 10
        b = int(clamp(-254.76935 + 0.82740 * xb + 115.67994 * math.log(xb), 0, 255))

    return [r, g, b]
