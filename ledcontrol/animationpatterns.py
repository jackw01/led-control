# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

import math
from random import random
from enum import Enum

import ledcontrol.rpi_ws281x as rpi_ws281x
import ledcontrol.utils as utils

ColorMode = Enum('ColorMode', ['hsv', 'rgb'])

# Primary animations that generate patterns in HSV or RGB color spaces
# return color, mode

def blank(t, dt, x, y, prev_state, colors):
    return (0, 0, 0), ColorMode.hsv

default = {
    0: '''
def pattern(t, dt, x, y, prev_state, colors):
    return colors[0], hsv
''',
    1: '''
def pattern(t, dt, x, y, prev_state, colors):
    return (t + x, 1, 1), hsv
''',
    2: '''
def pattern(t, dt, x, y, prev_state, colors):
    hue = (t + x) % 1
    return (hue - (hue % 0.1666), 1, 1), hsv
''',
    3: '''
def pattern(t, dt, x, y, prev_state, colors):
    return (wave_sine(t + x),
            wave_sine((t + x) * 1.2),
            wave_sine((t + x) * 1.4)), rgb
''',
    4: '''
def pattern(t, dt, x, y, prev_state, colors):
    return (wave_cubic(t + x),
            wave_cubic((t + x) * 1.2),
            wave_cubic((t + x) * 1.4)), rgb
''',
    5: '''
def pattern(t, dt, x, y, prev_state, colors):
    v = (t + x) % 1
    c = blackbody_to_rgb(v * v * 5500 + 1000)
    return (c[0] * v, c[1] * v, c[2] * v), rgb
''',
    6: '''
def pattern(t, dt, x, y, prev_state, colors):
    return (math.fabs((2 * t) % 2 - 1) + x, 1, 1), hsv
''',
    7: '''
def pattern(t, dt, x, y, prev_state, colors):
    color = [0, 0, 0]
    for i in range(3):
        delay = 0.05 * i
        v = x + (wave_sine(t + delay)) + wave_sine(x + 0.666 * t + delay)
        color[i] = 0.005 / wave_triangle(v)
    return color, rgb
''',
    8: '''
def pattern(t, dt, x, y, prev_state, colors):
    v = plasma_sines(x, y, t, 1.0, 0.5, 0.5, 1.0)
    return (wave_sine(v),
            wave_sine(v + 0.333),
            wave_sine(v + 0.666)), rgb
''',
    9: '''
def pattern(t, dt, x, y, prev_state, colors):
    v = plasma_sines(x, y, t, 1.0, 0.5, 0.5, 1.0)
    return (0.9 - wave_sine(v),
            wave_sine(v + 0.333) - 0.1,
            0.9 - wave_sine(v + 0.666)), rgb
''',
    10: '''
def pattern(t, dt, x, y, prev_state, colors):
    v = plasma_sines_octave(x, y, t, 7, 1.5, 0.5)
    return (0.9 - wave_sine(v),
            wave_sine(v + 0.333) - 0.1,
            0.9 - wave_sine(v + 0.666)), rgb
''',
}

default_names = {
    0: 'Solid Color',
    1: 'Cycle Hue 1D',
    2: 'Cycle Hue Bands 1D',
    3: 'RGB Sines 1D',
    4: 'RGB Cubics 1D',
    5: 'Cycle Blackbody 1D',
    6: 'Bounce Hue 1D',
    7: 'RGB Ripples 1D',
    8: 'RGB Plasma (Spectrum) 1D',
    9: 'RGB Plasma (Fire) 1D',
    10: 'RGB Octave Plasma (Fire) 1D',
}

# Secondary animations that transform finalized colors to add brightness-based effects
# return brightness, colorRGB

def sine_1d(t, dt, x, y, prev_state, in_color):
    return in_color, rpi_ws281x.wave_sine(t + x)

def cubic_1d(t, dt, x, y, prev_state, in_color):
    return in_color, rpi_ws281x.wave_cubic(t + x)

def ramp_1d(t, dt, x, y, prev_state, in_color):
    return in_color, (t + x) % 1 # test ramp^2

def bounce_linear_1d(t, dt, x, y, prev_state, in_color):
    return in_color, rpi_ws281x.wave_sine(x + rpi_ws281x.wave_triangle(t))

def bounce_sine_1d(t, dt, x, y, prev_state, in_color):
    return in_color, rpi_ws281x.wave_sine(x + rpi_ws281x.wave_sine(t))

def bounce_cubic_1d(t, dt, x, y, prev_state, in_color):
    return in_color, rpi_ws281x.wave_sine(x + rpi_ws281x.wave_cubic(t))

def perlin_noise_2d(t, dt, x, y, prev_state, in_color):
    return in_color, rpi_ws281x.perlin_noise_3d(x, y, t)

def twinkle_pulse_1d(t, dt, x, y, prev_state, in_color):
    v = prev_state[1] - dt
    if v <= -1:
        return in_color, random()
    elif v > 0:
        return prev_state[0], v
    else:
        return (0, 0, 0), v

def twinkle_pulse_2_1d(t, dt, x, y, prev_state, in_color):
    part = utils.fract(rpi_ws281x.wave_sine(t))
    v = 1 - utils.clamp(abs(x - part) * 10, 0, 1)
    return in_color, v

default_secondary = {
    0: None,
    1: sine_1d,
    2: cubic_1d,
    3: ramp_1d,
    4: bounce_linear_1d,
    5: bounce_sine_1d,
    6: bounce_cubic_1d,
    6: perlin_noise_2d,
    7: twinkle_pulse_1d,
    8: twinkle_pulse_2_1d,
}

default_secondary_names = {
    k: utils.snake_to_title(v.__name__) if v else 'None' for k, v in default_secondary.items()
}
