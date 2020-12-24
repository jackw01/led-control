# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

from random import random
from enum import Enum

import ledcontrol.driver as driver
import ledcontrol.utils as utils

ColorMode = Enum('ColorMode', ['hsv', 'rgb'])

# Primary animations that generate patterns in HSV or RGB color spaces
# return color, mode

def blank(t, dt, x, y, prev_state):
    return (0, 0, 0), ColorMode.hsv

static_patterns = [0, 1] # pattern IDs that display a solid color

default = {
    0: {
        'name': 'Solid Color',
        'primary_speed': 0.0,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    return palette(0), hsv
'''
    },
    1: {
        'name': 'Palette Gradient',
        'primary_speed': 0.0,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    return palette(x), hsv
'''
    },
    10: {
        'name': 'Cycle Hue 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    return (t + x, 1, 1), hsv
'''
    },
    20: {
        'name': 'Cycle Hue Quantized 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    hue = (t + x) % 1
    return (hue - (hue % 0.1666), 1, 1), hsv
'''
    },
    30: {
        'name': 'Cycle Palette 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    return palette(t + x), hsv
'''
    },
    31: {
        'name': 'Cycle Palette Mirrored 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    return palette(wave_triangle(t + x)), hsv
'''
    },
    32: {
        'name': 'Cycle Palette Quantized 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    t = (t + x) % 1
    return palette(t - (t % (1 / palette_length()))), hsv
'''
    },
    33: {
        'name': 'Cycle Palette Random 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    t = t + x
    i = (t - (t % 0.2)) / 0.2
    return palette(i * 0.618034), hsv
'''
    },
    40: {
        'name': 'RGB Sines 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    return (wave_sine(t + x),
            wave_sine((t + x) * 1.2),
            wave_sine((t + x) * 1.4)), rgb
'''
    },
    50: {
        'name': 'RGB Cubics 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    return (wave_cubic(t + x),
            wave_cubic((t + x) * 1.2),
            wave_cubic((t + x) * 1.4)), rgb
'''
    },
    60: {
        'name': 'Cycle Blackbody 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    v = (t + x) % 1
    c = blackbody_to_rgb(v * v * 5500 + 1000)
    return (c[0] * v, c[1] * v, c[2] * v), rgb
'''
    },
    70: {
        'name': 'Bounce Hue 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    return (wave_triangle(t) + x, 1, 1), hsv
'''
    },
    71: {
        'name': 'Bounce Palette 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    return palette(wave_triangle(t) + x), hsv
'''
    },
    80: {
        'name': 'RGB Ripples 1 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    color = [0, 0, 0]
    for i in range(3):
        delay = 0.05 * i
        v = x + (wave_sine(t + delay)) + wave_sine(x + 0.666 * t + delay)
        color[i] = 0.005 / wave_triangle(v)
    return color, rgb
'''
    },
    90: {
        'name': 'RGB Plasma (Spectrum) 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    v = plasma_sines(x, y, t, 1.0, 0.5, 0.5, 1.0)
    return (wave_sine(v),
            wave_sine(v + 0.333),
            wave_sine(v + 0.666)), rgb
'''
    },
    100: {
        'name': 'RGB Plasma (Fire) 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    v = plasma_sines(x, y, t, 1.0, 0.5, 0.5, 1.0)
    return (0.9 - wave_sine(v),
            wave_sine(v + 0.333) - 0.1,
            0.9 - wave_sine(v + 0.666)), rgb
'''
    },
    110: {
        'name': 'RGB Octave Plasma (Fire) 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    v = plasma_sines_octave(x, y, t, 7, 1.5, 0.5)
    return (1.0 - wave_sine(v),
            wave_sine(v + 0.333),
            1.0 - wave_sine(v + 0.666)), rgb
'''
    },
    120: {
        'name': 'HSV Waves 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    h = (x + t) * 0.5 % .5 + x + wave_sine(t)
    return (h, 1, wave_sine(h + t)), hsv
'''
    },
    121: { # Performance isn't as good as it could be
        'name': 'Palette Waves 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    h = (x + t) * 0.5 % .5 + x + wave_sine(t)
    c = palette(h)
    return (c[0], c[1], wave_sine(h + t)), hsv
'''
    },
    130: {
        'name': 'HSV Ripples 1 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    wave1 = wave_sine(t / 4 + x)
    wave2 = wave_sine(t / 8 - x)
    wave3 = wave_sine(x + wave1 + wave2)
    return (wave3 % 0.4 + t, 1, wave1 + wave3), hsv
'''
    },
    131: {
        'name': 'Palette Ripples 1 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    wave1 = wave_sine(t / 4 + x)
    wave2 = wave_sine(t / 8 - x)
    wave3 = wave_sine(x + wave1 + wave2)
    c = palette(wave3 % 0.2 + t)
    return (c[0], c[1], wave1 + wave3), hsv
'''
    },
    140: {
        'name': 'Palette Twinkle 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, prev_state):
    v = prev_state[2] - dt
    if v <= 0:
        c = palette(t + x)
        return (c[0], c[1], random.random()), hsv
    elif v > 0:
        return (prev_state[0], prev_state[1], v), hsv
    else:
        return (0, 0, 0), hsv
'''
    }
}

# Secondary animations that transform finalized colors to add brightness effects
# return brightness, colorRGB

def sine_1d(t, dt, x, y, prev_state, in_color):
    return in_color, driver.wave_sine(t + x)

def cubic_1d(t, dt, x, y, prev_state, in_color):
    return in_color, driver.wave_cubic(t + x)

def ramp_1d(t, dt, x, y, prev_state, in_color):
    return in_color, (t + x) % 1 # test ramp^2

def bounce_linear_1d(t, dt, x, y, prev_state, in_color):
    return in_color, driver.wave_sine(x + driver.wave_triangle(t))

def bounce_sine_1d(t, dt, x, y, prev_state, in_color):
    return in_color, driver.wave_sine(x + driver.wave_sine(t))

def bounce_cubic_1d(t, dt, x, y, prev_state, in_color):
    return in_color, driver.wave_sine(x + driver.wave_cubic(t))

def perlin_noise_2d(t, dt, x, y, prev_state, in_color):
    return in_color, driver.perlin_noise_3d(x, y, t)

def twinkle_pulse_1d(t, dt, x, y, prev_state, in_color):
    v = prev_state[1] - dt
    if v <= -0.2:
        return in_color, random()
    elif v > 0:
        return prev_state[0], v
    else:
        return (0, 0, 0), v

def wipe_across_1d(t, dt, x, y, prev_state, in_color):
    return in_color, ((t + x) % 1 > 0.5) * 1.0

def wipe_from_center_1d(t, dt, x, y, prev_state, in_color):
    if x < 0.5:
        return in_color, ((t + x) % 1 < 0.5) * 1.0
    else:
        return in_color, ((x - t) % 1 < 0.5) * 1.0

def wipe_from_ends_1d(t, dt, x, y, prev_state, in_color):
    if x < 0.5:
        return in_color, ((x - t) % 1 < 0.5) * 1.0
    else:
        return in_color, ((t + x) % 1 < 0.5) * 1.0


default_secondary = {
    0: None,
    1: sine_1d,
    2: cubic_1d,
    3: ramp_1d,
    4: bounce_linear_1d,
    5: bounce_sine_1d,
    6: bounce_cubic_1d,
    7: perlin_noise_2d,
    8: twinkle_pulse_1d,
    9: wipe_across_1d,
    10: wipe_from_center_1d,
    11: wipe_from_ends_1d,
}

default_secondary_names = {
    k: utils.snake_to_title(v.__name__) if v else 'None' for k, v in default_secondary.items()
}
