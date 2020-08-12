# led-control WS2812B LED Controller Server
# Copyright 2020 jackw01. Released under the MIT License (see LICENSE for details).

from ledcontrol.animationpatterns import ColorMode

default = {
    0: {
        'name': 'Sunset',
        'mode': 0,
        'colors': [(0.114, 1, 1), (0.005, 1, 1), (0.925, 1, 0.66), (0.883, 1, 0.28)]
    },
    1: {
        'name': 'Spectrum',
        'mode': 0,
        'colors': [(0, 1, 1), (1, 1, 1)]
    }
}
