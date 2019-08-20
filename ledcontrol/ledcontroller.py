# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

import ledcontrol.rpi_ws281x as rpi_ws281x
import ledcontrol.utils as utils

class LEDController:
    def __init__(self, led_count, led_pin,
                 led_data_rate, led_dma_channel, led_strip_type, led_pixel_order,
                 led_color_correction):
        # This is bad but it's the only way
        px_order = rpi_ws281x.WS2811_STRIP_GRB
        if led_strip_type == 'WS2812':
            if led_pixel_order == 'RGB':
                px_order = rpi_ws281x.WS2811_STRIP_RGB
            elif led_pixel_order == 'RBG':
                px_order = rpi_ws281x.WS2811_STRIP_RBG
            elif led_pixel_order == 'GRB':
                px_order = rpi_ws281x.WS2811_STRIP_GRB
            elif led_pixel_order == 'GBR':
                px_order = rpi_ws281x.WS2811_STRIP_GBR
            elif led_pixel_order == 'BRG':
                px_order = rpi_ws281x.WS2811_STRIP_BRG
            elif led_pixel_order == 'BGR':
                px_order = rpi_ws281x.WS2811_STRIP_BGR
        elif led_strip_type == 'SK6812':
            if led_pixel_order == 'RGBW':
                px_order = rpi_ws281x.SK6812_STRIP_RGBW
            elif led_pixel_order == 'RBGW':
                px_order = rpi_ws281x.SK6812_STRIP_RBGW
            elif led_pixel_order == 'GRBW':
                px_order = rpi_ws281x.SK6812_STRIP_GRBW
            elif led_pixel_order == 'GBRW':
                px_order = rpi_ws281x.SK6812_STRIP_GBRW
            elif led_pixel_order == 'BRGW':
                px_order = rpi_ws281x.SK6812_STRIP_BRGW
            elif led_pixel_order == 'BGRW':
                px_order = rpi_ws281x.SK6812_STRIP_BGRW

        self.count = led_count
        self.leds = rpi_ws281x.PixelStrip(led_count, led_pin,
                                          led_data_rate, led_dma_channel,
                                          False, # invert?
                                          255, # master brightness
                                          0, # channel
                                          px_order)

        self.correction_original = led_color_correction
        self.set_color_temp(6500)

        self.leds.begin()
        self.clear()

    def set_color_temp(self, kelvin):
        temp_rgb = utils.blackbody2rgb_2(kelvin)
        self.correction = [self.correction_original[0] * temp_rgb[0] // 255,
                           self.correction_original[1] * temp_rgb[1] // 255,
                           self.correction_original[2] * temp_rgb[2] // 255]

    def clear(self):
        for i in range(self.count):
            self.leds.setPixelColor(i, rpi_ws281x.Color(0, 0, 0))
        self.leds.show()

    def set_led_states(self, states):
        for i in range(len(states)):
            self.leds.setPixelColor(i, rpi_ws281x.Color(states[i][0] * self.correction[0] // 255,
                                                        states[i][1] * self.correction[1] // 255,
                                                        states[i][2] * self.correction[2] // 255))
        self.leds.show()
