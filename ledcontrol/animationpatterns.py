# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

from ledcontrol.animationcontroller import ColorMode

def cycle_hue_1d(x, y):
    return [x, 1, 1], ColorMode.hsv
