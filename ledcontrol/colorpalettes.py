# led-control WS2812B LED Controller Server
# Copyright 2020 jackw01. Released under the MIT License (see LICENSE for details).

from ledcontrol.animationpatterns import ColorMode

default = {
    0: {
        'name': 'Spectrum',
        'mode': ColorMode.hsv,
        'colors': [(0, 1, 1), (1, 1, 1)]
    }
}
