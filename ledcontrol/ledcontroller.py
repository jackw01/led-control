# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

import ledcontrol.driver as rpi_ws281x
import ledcontrol.utils as utils

class LEDController:
    def __init__(self, led_count, led_pin,
                 led_data_rate, led_dma_channel,
                 led_pixel_order):
        # This is bad but it's the only way
        px_order = rpi_ws281x.rpi_ws281x.WS2811_STRIP_GRB
        if led_pixel_order == 'RGB':
            px_order = rpi_ws281x.rpi_ws281x.WS2811_STRIP_RGB
        elif led_pixel_order == 'RBG':
            px_order = rpi_ws281x.rpi_ws281x.WS2811_STRIP_RBG
        elif led_pixel_order == 'GRB':
            px_order = rpi_ws281x.rpi_ws281x.WS2811_STRIP_GRB
        elif led_pixel_order == 'GBR':
            px_order = rpi_ws281x.rpi_ws281x.WS2811_STRIP_GBR
        elif led_pixel_order == 'BRG':
            px_order = rpi_ws281x.rpi_ws281x.WS2811_STRIP_BRG
        elif led_pixel_order == 'BGR':
            px_order = rpi_ws281x.rpi_ws281x.WS2811_STRIP_BGR
        elif led_pixel_order == 'RGBW':
            px_order = rpi_ws281x.rpi_ws281x.SK6812_STRIP_RGBW
        elif led_pixel_order == 'RBGW':
            px_order = rpi_ws281x.rpi_ws281x.SK6812_STRIP_RBGW
        elif led_pixel_order == 'GRBW':
            px_order = rpi_ws281x.rpi_ws281x.SK6812_STRIP_GRBW
        elif led_pixel_order == 'GBRW':
            px_order = rpi_ws281x.rpi_ws281x.SK6812_STRIP_GBRW
        elif led_pixel_order == 'BRGW':
            px_order = rpi_ws281x.rpi_ws281x.SK6812_STRIP_BRGW
        elif led_pixel_order == 'BGRW':
            px_order = rpi_ws281x.rpi_ws281x.SK6812_STRIP_BGRW

        self.has_white = 1 if 'W' in led_pixel_order else 0

        self.count = led_count
        self.leds = rpi_ws281x.PixelStrip(led_count, led_pin,
                                          led_data_rate, led_dma_channel,
                                          False, # invert?
                                          255, # master brightness
                                          0, # channel
                                          px_order)

        self.leds.begin()
        self.clear()

    def clear(self):
        for i in range(self.count):
            self.leds.setPixelColor(i, rpi_ws281x.Color(0, 0, 0))
        self.leds.show()
