# led-control WS2812B LED Controller Server
# Copyright 2023 jackw01. Released under the MIT License (see LICENSE for details).

import math
import pyfastnoisesimd as fns

noise_coords = fns.empty_coords(3)
noise = fns.Noise()

def float_to_int_1000(t):
    return int(t * 999.9) % 1000

def float_to_int_1000_mirror(t):
    return abs(int(t * 1998.9) % 1999 - 999)

def wave_pulse(t, duty_cycle):
    return math.ceil(duty_cycle - math.fmod(t, 1.0))

def wave_triangle(t):
    ramp = math.fmod((2.0 * t), 2.0)
    return math.fabs((ramp + 2.0 if ramp < 0 else ramp) - 1.0)

def wave_sine(t):
    return math.cos(6.283 * t) / 2.0 + 0.5

def wave_cubic(t):
    ramp = math.fmod((2.0 * t), 2.0)
    tri = math.fabs((ramp + 2.0 if ramp < 0 else ramp) - 1.0)
    if tri > 0.5:
        t2 = 1.0 - tri
        return 1.0 - 4.0 * t2 * t2 * t2
    else:
        return 4.0 * tri * tri * tri

def plasma_sines(x, y, t, coeff_x, coeff_y, coeff_x_y, coeff_dist_x_y):
    v = 0
    v += math.sin((x + t) * coeff_x)
    v += math.sin((y + t) * coeff_y)
    v += math.sin((x + y + t) * coeff_x_y)
    v += math.sin((math.sqrt(x * x + y * y) + t) * coeff_dist_x_y)
    return v

def plasma_sines_octave(x, y, t, octaves, lacunarity, persistence):
    vx = x
    vy = y
    freq = 1.0
    amplitude = 1.0
    for i in range(octaves):
        vx1 = vx
        vx += math.cos(vy * freq + t * freq) * amplitude
        vy += math.sin(vx1 * freq + t * freq) * amplitude
        freq *= lacunarity
        amplitude *= persistence
    return vx / 2.0

def perlin_noise_3d(x, y, z):
    noise_coords[0,:] = x
    noise_coords[1,:] = y
    noise_coords[2,:] = z
    return noise.genFromCoords(noise_coords)[0]

def fbm_noise_3d(x, y, z, octaves, lacunarity, persistence):
    v = 0
    freq = 1.0
    amplitude = 1.0
    for i in range(octaves):
        v += amplitude * perlin_noise_3d(freq * x, freq * y, freq * z)
        freq *= lacunarity
        amplitude *= persistence
    return v / 2.0

def clamp(x, min, max):
    if x < min:
        return min
    elif x > max:
        return max
    else:
        return x

def blackbody_to_rgb(kelvin):
    tmp_internal = kelvin / 100.0
    r_out = 0
    g_out = 0
    b_out = 0

    if tmp_internal <= 66:
        xg = tmp_internal - 2.0
        r_out = 1.0
        g_out = clamp((-155.255 - 0.446 * xg + 104.492 * math.log(xg)) / 255.0, 0, 1)
    else:
        xr = tmp_internal - 55.0
        xg = tmp_internal - 50.0
        r_out = clamp((351.977 + 0.114 * xr - 40.254 * math.log(xr)) / 255.0, 0, 1)
        g_out = clamp((325.449 + 0.079 * xg - 28.085 * math.log(xg)) / 255.0, 0, 1)

    if tmp_internal >= 66:
        b_out = 1.0
    elif tmp_internal <= 19:
        b_out = 0.0
    else:
        xb = tmp_internal - 10.0
        b_out = clamp((-254.769 + 0.827 * xb + 115.680 * math.log(xb)) / 255.0, 0, 1)

    return [r_out, g_out, b_out]

def blackbody_correction_rgb(rgb, kelvin):
    bb = blackbody_to_rgb(kelvin)
    return [rgb[0] * bb[0], rgb[1] * bb[1], rgb[2] * bb[2]]
