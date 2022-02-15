# led-control WS2812B LED Controller Server
# Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

from random import random
from enum import Enum

import ledcontrol.driver as driver
import ledcontrol.utils as utils

ColorMode = Enum('ColorMode', ['hsv', 'rgb'])

def blank(t, dt, x, y, z, prev_state):
    return (0, 0, 0), ColorMode.hsv

static_function_ids = [0, 1, 2, 3] # pattern IDs that display a solid color

default = {
    0: {
        'name': 'Static Color',
        'primary_speed': 0.0,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette(0), hsv
'''
    },
    1: {
        'name': 'Static White',
        'primary_speed': 0.0,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return (0, 0, 1), hsv
'''
    },
    2: {
        'name': 'Static Gradient 1D',
        'primary_speed': 0.0,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette(x), hsv
'''
    },
    3: {
        'name': 'Static Gradient Mirrored 1D',
        'primary_speed': 0.0,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette_mirrored(x), hsv
'''
    },

    6: {
        'name': 'Twinkle Gradient 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v = prev_state[2] - dt
    if v <= 0:
        c = palette(x)
        return (c[0], c[1], random.random()), hsv
    elif v > 0:
        return (prev_state[0], prev_state[1], v), hsv
    else:
        return (0, 0, 0), hsv
'''
    },
    7: {
        'name': 'Twinkle White 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v = prev_state[2] - dt
    if v <= 0:
        return (0, 0, random.random()), hsv
    elif v > 0:
        return (prev_state[0], prev_state[1], v), hsv
    else:
        return (0, 0, 0), hsv
'''
    },

    100: {
        'name': 'Palette Cycle 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette(t + x), hsv
'''
    },
    110: {
        'name': 'Palette Cycle Mirrored 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette_mirrored(t + x), hsv
'''
    },
    112: {
        'name': 'Palette Cycle Wipe 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    c = palette_mirrored(t + x)
    return (c[0], c[1], ((t + x) % 1 > 0.5) * 1.0), hsv
'''
    },
    114: {
        'name': 'Palette Cycle Wipe From Center 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    c = palette_mirrored(t + x)
    if x < 0.5:
        return (c[0], c[1], ((t + x) % 1 < 0.5) * 1.0), hsv
    else:
        return (c[0], c[1], ((t - x) % 1 < 0.5) * 1.0), hsv
'''
    },
    120: {
        'name': 'Palette Cycle Quantized 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    t = (t + x) % 1
    return palette(t - (t % (1 / 6))), hsv
'''
    },
    130: {
        'name': 'Palette Cycle Random 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
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
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette_mirrored(wave_triangle(t) + x), hsv
'''
    },
    141: {
        'name': 'Palette Bounce Mirrored 1D',
        'primary_speed': 0.1,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette_mirrored(wave_sine(t) + x), hsv
'''
    },
    150: { # Performance isn't as good as it could be
        'name': 'Palette Waves 1D',
        'primary_speed': 0.05,
        'primary_scale': 1.0,
        'default': True,
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
        'default': True,
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
        'default': True,
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
        'default': True,
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
        'default': True,
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
        'default': True,
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
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return palette(perlin_noise_3d(x, y, t)), hsv
'''
    },
    210: {
        'name': 'Palette fBm Noise 2D',
        'primary_speed': 0.3,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v = fbm_noise_3d(x, y, t * 0.5, 7, 2.0, 0.5)
    return palette(wave_triangle(v * 4)), hsv
'''
    },

    310: {
        'name': 'Hue Cycle 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return (t + x, 1, 1), hsv
'''
    },
    320: {
        'name': 'Hue Cycle Quantized 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    hue = (t + x) % 1
    return (hue - (hue % 0.1666), 1, 1), hsv
'''
    },
    330: {
        'name': 'Hue Scan 1D',
        'primary_speed': 0.1,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return (wave_triangle(t) + x, 1, 1), hsv
'''
    },
    331: {
        'name': 'Hue Bounce 1D',
        'primary_speed': 0.1,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return (wave_sine(t) + x, 1, 1), hsv
'''
    },
    340: {
        'name': 'Hue Waves 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    h = (x + t) * 0.5 + x + wave_sine(t)
    return (h, 1, wave_sine(h + t)), hsv
'''
    },
    350: {
        'name': 'Hue Ripples 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    wave1 = wave_sine(t / 4 + x)
    wave2 = wave_sine(t / 8 - x)
    wave3 = wave_sine(x + wave1 + wave2)
    return (wave3 % 0.15 + t, 1, wave1 + wave3), hsv
'''
    },

    400: {
        'name': 'RGB Sines 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return (wave_sine(t + x),
            wave_sine((t + x) * 1.2),
            wave_sine((t + x) * 1.4)), rgb
'''
    },
    410: {
        'name': 'RGB Cubics 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    return (wave_cubic(t + x),
            wave_cubic((t + x) * 1.2),
            wave_cubic((t + x) * 1.4)), rgb
'''
    },
    420: {
        'name': 'RGB Ripples 1D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v0 = x + (wave_sine(t)) + wave_sine(x + 0.666 * t)
    v1 = x + (wave_sine(t + 0.05)) + wave_sine(x + 0.666 * t + 0.05)
    v2 = x + (wave_sine(t + 0.1)) + wave_sine(x + 0.666 * t + 0.1)
    return (0.01 / (wave_triangle(v0) + 0.01), 0.01 / (wave_triangle(v1) + 0.01), 0.01 / (wave_triangle(v2) + 0.01)), rgb
'''
    },
    430: {
        'name': 'RGB Plasma (Spectrum Sines) 2D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v = plasma_sines(x, y, t, 1.0, 0.5, 0.5, 1.0)
    return (wave_sine(v),
            wave_sine(v + 0.333),
            wave_sine(v + 0.666)), rgb
'''
    },
    440: {
        'name': 'RGB Plasma (Fire Sines) 2D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v = plasma_sines(x, y, t, 1.0, 0.5, 0.5, 1.0)
    return (0.9 - wave_sine(v),
            wave_sine(v + 0.333) - 0.1,
            0.9 - wave_sine(v + 0.666)), rgb
'''
    },
    450: {
        'name': 'RGB Fractal Plasma (Fire Sines) 2D',
        'primary_speed': 0.2,
        'primary_scale': 1.0,
        'default': True,
        'source': '''
def pattern(t, dt, x, y, z, prev_state):
    v = plasma_sines_octave(x, y, t, 7, 2.0, 0.5)
    return (1.0 - wave_sine(v),
            wave_sine(v + 0.333),
            1.0 - wave_sine(v + 0.666)), rgb
'''
    },
}
