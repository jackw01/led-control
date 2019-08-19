# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

import collections

Point = collections.namedtuple('Point', ['x', 'y'])

def line(count):
    return lambda i: Point(i / count, 0)
