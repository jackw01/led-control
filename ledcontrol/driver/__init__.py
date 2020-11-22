# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

import _ledcontrol_rpi_ws281x_driver as rpi_ws281x

from .rpi_ws281x_helper import PixelStrip, Color
#from .lib.rpi_ws281x import (
#    blackbody_to_rgb,
#    blackbody_correction_rgb,
#    wave_pulse,
#    wave_triangle,
#    wave_sine,
#    wave_cubic,
#    plasma_sines,
#    plasma_sines_octave,
#    perlin_noise_3d,
#)

print(dir(rpi_ws281x))

# For some reason this stopped working the normal way
blackbody_to_rgb = rpi_ws281x.blackbody_to_rgb
blackbody_correction_rgb = rpi_ws281x.blackbody_correction_rgb
wave_pulse = rpi_ws281x.wave_pulse
wave_triangle = rpi_ws281x.wave_triangle
wave_sine = rpi_ws281x.wave_sine
wave_cubic = rpi_ws281x.wave_cubic
plasma_sines = rpi_ws281x.plasma_sines
plasma_sines_octave = rpi_ws281x.plasma_sines_octave
perlin_noise_3d = rpi_ws281x.perlin_noise_3d

__version__ = '4.2.2'
