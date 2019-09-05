# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

from random import random
from enum import Enum

ColorMode = Enum('ColorMode', ['hsv', 'rgb'])

# Primary animations that generate patterns in HSV or RGB color spaces
# return color, mode

def blank(t, dt, x, y, prev_state, colors):
    return (0, 0, 0), ColorMode.hsv

solid_color = '''
def pattern(t, dt, x, y, prev_state, colors):
    return colors[0], hsv
'''

cycle_hue_1d = '''
def pattern(t, dt, x, y, prev_state, colors):
    return (t + x, 1, 1), hsv
'''

cycle_hue_bands_1d = '''
def pattern(t, dt, x, y, prev_state, colors):
    hue = (t + x) % 1
    return (hue - (hue % 0.1666), 1, 1), hsv
'''

default = {
  0: solid_color,
  1: cycle_hue_1d,
  2: cycle_hue_bands_1d,
}

default_names = {
  0: 'Solid Color',
  1: 'Cycle Hue 1D',
  2: 'Cycle Hue Bands 1D',
}

# Secondary animations that transform finalized colors to add brightness-based effects
# return brightness, colorRGB

def secondary_solid(t, dt, x, y, prev_state, in_color):
  return 1.0, in_color

def twinkle_pulse_1d(t, dt, x, y, prev_state, in_color):
    v = prev_state[0] - dt
    if v <= 0:
      return random(), in_color
    else:
      return v, prev_state[1]
