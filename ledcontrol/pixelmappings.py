# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

def line(count):
    return lambda i: (i / count, 0)
