# led-control WS2812B LED Controller Server
# Copyright 2020 jackw01. Released under the MIT License (see LICENSE for details).

import ujson

class ControlClient:
    'Receives LED states from a remote source'
    def __init__(self):
        pass

    def get_frame(self, length):
        'Gets data for one frame'
        #raw = ujson.loads(data.decode())
        raw = []
        return [(raw[i], 1) if i < len(raw) else ([0, 0, 0], 1) for i in range(length)]
