# led-control WS2812B LED Controller Server
# Copyright 2021 jackw01. Released under the MIT License (see LICENSE for details).

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
        'name': 'Static Color',
        'primary_speed': 0.0,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette(0), hsv
'''
    },
    1: {
        'name': 'Static Gradient 1D',
        'primary_speed': 0.0,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette(x), hsv
'''
    },
    2: {
        'name': 'Static Gradient Mirrored 1D',
        'primary_speed': 0.0,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette_mirrored(x), hsv
'''
    },
    10: {
        'name': 'Hue Cycle 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return (t + x, 1, 1), hsv
'''
    },
    20: {
        'name': 'Hue Cycle Quantized 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    hue = (t + x) % 1
    return (hue - (hue % 0.1666), 1, 1), hsv
'''
    },
    30: {
        'name': 'Hue Scan 1D',
        'primary_speed': 0.1,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return (wave_triangle(t) + x, 1, 1), hsv
'''
    },
    31: {
        'name': 'Hue Bounce 1D',
        'primary_speed': 0.1,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return (wave_sine(t) + x, 1, 1), hsv
'''
    },
    40: {
        'name': 'Hue Waves 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    h = (x + t) * 0.5 + x + wave_sine(t)
    return (h, 1, wave_sine(h + t)), hsv
'''
    },
    50: {
        'name': 'Hue Ripples 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    wave1 = wave_sine(t / 4 + x)
    wave2 = wave_sine(t / 8 - x)
    wave3 = wave_sine(x + wave1 + wave2)
    return (wave3 % 0.15 + t, 1, wave1 + wave3), hsv
'''
    },



    100: {
        'name': 'Palette Cycle 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette(t + x), hsv
'''
    },
    110: {
        'name': 'Palette Cycle Mirrored 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette_mirrored(t + x), hsv
'''
    },
    120: {
        'name': 'Palette Cycle Quantized 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    t = (t + x) % 1
    return palette(t - (t % (1 / palette_length()))), hsv
'''
    },
    130: {
        'name': 'Palette Cycle Random 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    t = t + x
    i = (t - (t % 0.2)) / 0.2
    return palette(i * 0.618034), hsv
'''
    },
    140: {
        'name': 'Palette Scan Mirrored 1D',
        'primary_speed': 0.1,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette_mirrored(wave_triangle(t) + x), hsv
'''
    },
    141: {
        'name': 'Palette Bounce Mirrored 1D',
        'primary_speed': 0.1,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette_mirrored(wave_sine(t) + x), hsv
'''
    },
    150: { # Performance isn't as good as it could be
        'name': 'Palette Waves 1D',
        'primary_speed': 0.05,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    h = (x + t) * 0.1 + x + wave_sine(t)
    c = palette(wave_triangle(h))
    return (c[0], c[1], wave_sine(h + t)), hsv
'''
    },
    160: {
        'name': 'Palette Ripples 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    wave1 = wave_sine(t / 4 + x)
    wave2 = wave_sine(t / 8 - x)
    wave3 = wave_sine(x + wave1 + wave2)
    c = palette(wave3 % 0.15 + t)
    return (c[0], c[1], wave1 + wave3), hsv
'''
    },
    161: {
        'name': 'Palette Ripples (Fast Cycle) 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    wave1 = wave_sine(t / 4 + x)
    wave2 = wave_sine(t / 8 - x)
    wave3 = wave_sine(x + wave1 + wave2)
    c = palette(wave3 % 0.8 + t)
    return (c[0], c[1], wave1 + wave3), hsv
'''
    },
    170: {
        'name': 'Palette Plasma 2D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v = plasma_sines(x, y, t, 1.0, 0.5, 0.5, 1.0)
    return palette(wave_triangle(v)), hsv
'''
    },
    180: {
        'name': 'Palette Fractal Plasma 2D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v = plasma_sines_octave(x, y, t, 7, 2.0, 0.5)
    return palette(wave_triangle(v)), hsv
'''
    },
    190: {
        'name': 'Palette Twinkle 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v = prev_state[2] - dt
    if v <= 0:
        c = palette(t + x)
        return (c[0], c[1], random.random()), hsv
    elif v > 0:
        return (prev_state[0], prev_state[1], v), hsv
    else:
        return (0, 0, 0), hsv
'''
    },
    200: {
        'name': 'Palette Perlin Noise 2D',
        'primary_speed': 0.3,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette(perlin_noise_3d(x, y, t)), hsv
'''
    },


    300: {
        'name': 'RGB Sines 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return (wave_sine(t + x),
            wave_sine((t + x) * 1.2),
            wave_sine((t + x) * 1.4)), rgb
'''
    },
    310: {
        'name': 'RGB Cubics 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return (wave_cubic(t + x),
            wave_cubic((t + x) * 1.2),
            wave_cubic((t + x) * 1.4)), rgb
'''
    },
    320: {
        'name': 'RGB Ripples 1 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v0 = x + (wave_sine(t)) + wave_sine(x + 0.666 * t)
    v1 = x + (wave_sine(t + 0.05)) + wave_sine(x + 0.666 * t + 0.05)
    v2 = x + (wave_sine(t + 0.1)) + wave_sine(x + 0.666 * t + 0.1)
    return (0.01 / (wave_triangle(v0) + 0.01), 0.01 / (wave_triangle(v1) + 0.01), 0.01 / (wave_triangle(v2) + 0.01)), rgb
'''
    },
    330: {
        'name': 'RGB Plasma (Spectrum Sines) 2D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v = plasma_sines(x, y, t, 1.0, 0.5, 0.5, 1.0)
    return (wave_sine(v),
            wave_sine(v + 0.333),
            wave_sine(v + 0.666)), rgb
'''
    },
    340: {
        'name': 'RGB Plasma (Fire Sines) 2D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v = plasma_sines(x, y, t, 1.0, 0.5, 0.5, 1.0)
    return (0.9 - wave_sine(v),
            wave_sine(v + 0.333) - 0.1,
            0.9 - wave_sine(v + 0.666)), rgb
'''
    },
    350: {
        'name': 'RGB Fractal Plasma (Fire Sines) 2D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v = plasma_sines_octave(x, y, t, 7, 2.0, 0.5)
    return (1.0 - wave_sine(v),
            wave_sine(v + 0.333),
            1.0 - wave_sine(v + 0.666)), rgb
'''
    },
    360: {
        'name': 'Blackbody Cycle 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v = wave_triangle(t + x)
    c = blackbody_to_rgb(v * v * 5500 + 1000)
    return (c[0] * v, c[1] * v, c[2] * v), rgb
'''
    },
}

# Secondary animations that transform finalized colors to add brightness effects
# return brightness, colorRGB

def sine_1d(t, dt, x, y, z, prev_state, in_color):
    return in_color, driver.wave_sine(t + x)

def cubic_1d(t, dt, x, y, z, prev_state, in_color):
    return in_color, driver.wave_cubic(t + x)

def ramp_1d(t, dt, x, y, z, prev_state, in_color):
    return in_color, (t + x) % 1 # test ramp^2

def bounce_linear_1d(t, dt, x, y, z, prev_state, in_color):
    return in_color, driver.wave_sine(x + driver.wave_triangle(t))

def bounce_sine_1d(t, dt, x, y, z, prev_state, in_color):
    return in_color, driver.wave_sine(x + driver.wave_sine(t))

def bounce_cubic_1d(t, dt, x, y, z, prev_state, in_color):
    return in_color, driver.wave_sine(x + driver.wave_cubic(t))

def perlin_noise_2d(t, dt, x, y, z, prev_state, in_color):
    return in_color, driver.perlin_noise_3d(x, y, t)

def twinkle_pulse_1d(t, dt, x, y, z, prev_state, in_color):
    v = prev_state[1] - dt
    if v <= -0.2:
        return in_color, random()
    elif v > 0:
        return prev_state[0], v
    else:
        return (0, 0, 0), v

def wipe_across_1d(t, dt, x, y, z, prev_state, in_color):
    return in_color, ((t + x) % 1 > 0.5) * 1.0

def wipe_from_center_1d(t, dt, x, y, z, prev_state, in_color):
    if x < 0.5:
        return in_color, ((t + x) % 1 < 0.5) * 1.0
    else:
        return in_color, ((x - t) % 1 < 0.5) * 1.0

def wipe_from_ends_1d(t, dt, x, y, z, prev_state, in_color):
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
