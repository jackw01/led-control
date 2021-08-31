# led-control WS2812B LED Controller Server
# Copyright 2021 jackw01. Released under the MIT License (see LICENSE for details).

import collections

Point = collections.namedtuple('Point', ['x', 'y', 'z'])

def line(count):
    return lambda i: Point(i / count, 0, 0)

def from_array(mapping):
    min_v = min([min(pt) for pt in mapping])
    v_range = max([max(pt) for pt in mapping]) - min_v
    mapping_normalized = [[(v - min_v) / v_range * 0.999 for v in pt] for pt in mapping]
    return lambda i: Point(mapping_normalized[i][0],
                           mapping_normalized[i][1],
                           mapping_normalized[i][2])
