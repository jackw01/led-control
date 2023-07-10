# led-control WS2812B LED Controller Server
# Copyright 2023 jackw01. Released under the MIT License (see LICENSE for details).

import math

def float_to_int_1000(t):
    return int(t * 999.9) % 1000

def float_to_int_1000_mirror(t):
    return abs(int(t * 1998.9) % 1999 - 999)

def wave_pulse(t, duty_cycle):
    return math.ceil(duty_cycle - (t % 1.0))

def wave_triangle(t):
    ramp = (2.0 * t) % 2.0
    return abs((ramp + 2.0 if ramp < 0 else ramp) - 1.0)

def wave_sine(t):
    return math.cos(6.283 * t) / 2.0 + 0.5

def wave_cubic(t):
    return 0

def plasma_sines(x, y, t, coeff_x, coeff_y, coeff_x_y, coeff_dist_x_y):
    return 0

def plasma_sines_octave(x, y, t, octaves, lacunarity, persistence):
    return 0

def perlin_noise_3d(x, y, z):
    return 0

def fbm_noise_3d(x, y, z, octaves, lacunarity, persistence):
    return 0

def blackbody_to_rgb(kelvin):
    return [1, 1, 1]

def blackbody_correction_rgb(rgb, kelvin):
    return 0
