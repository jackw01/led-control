# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

__version__ = '1.0.0'

from ledcontrol.app import create_app
from werkzeug.serving import run_simple

color_correction_hex = '#FFB0F0'.lstrip('#')

app = create_app(160, 30,
                 18, 800000, 10,
                 'WS2812', 'GRB',
                 [int(color_correction_hex[i:i + 2], 16) for i in (0, 2, 4)])
run_simple('0.0.0.0', 8080, app,
           use_reloader=False,
           use_debugger=True,
           use_evalex=True)
