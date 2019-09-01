# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

from random import random
from enum import Enum

ColorMode = Enum('ColorMode', ['hsv', 'rgb'])

# Primary animations that generate patterns in HSV or RGB color spaces
# return color, mode

def blank(t, dt, x, y, prev_state):
    return (0, 0, 0), ColorMode.hsv

cycle_hue_1d = '''
def pattern(t, dt, x, y, prev_state):
    return (t + x, 1, 1), hsv
'''

defaults = {
  'cycle_hue_1d': cycle_hue_1d,
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
