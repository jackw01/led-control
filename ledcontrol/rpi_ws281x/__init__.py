# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

from .rpi_ws281x import PixelStrip, Color
from .lib.rpi_ws281x import (
    blackbody_to_rgb,
    blackbody_correction_rgb,
    wave_pulse,
    wave_triangle,
    wave_sine,
    wave_cubic,
    plasma_sines,
    plasma_sines_octave,
    perlin_noise_3d,
)
from .lib import *

__version__ = '4.2.2'
