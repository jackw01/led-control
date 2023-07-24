# led-control WS2812B LED Controller Server
# Copyright 2023 jackw01. Released under the MIT License (see LICENSE for details).

import io

def is_raspberrypi():
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower():
                return True
    except Exception:
        pass
    return False

if is_raspberrypi():
    # Import the extension module
    from _ledcontrol_rpi_ws281x_driver import *
else:
    from . driver_non_raspberry_pi import *


