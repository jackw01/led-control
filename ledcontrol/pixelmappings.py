# led-control WS2812B LED Controller Server
# Copyright 2021 jackw01. Released under the MIT License (see LICENSE for details).

import collections

Point = collections.namedtuple('Point', ['x', 'y'])

def line(count):
    return lambda i: Point(i / count, 0)

# needs arrays and serpentine order modes
# json mapping
