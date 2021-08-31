# led-control WS2812B LED Controller Server
# Copyright 2021 jackw01. Released under the MIT License (see LICENSE for details).

import atexit

import ledcontrol.driver as driver
import ledcontrol.utils as utils

class LEDController:
    def __init__(self,
                 led_count,
                 led_pin,
                 led_data_rate,
                 led_dma_channel,
                 led_pixel_order):
        # This is bad but it's the only way
        px_order = driver.WS2811_STRIP_GRB
        if led_pixel_order == 'RGB':
            px_order = driver.WS2811_STRIP_RGB
        elif led_pixel_order == 'RBG':
            px_order = driver.WS2811_STRIP_RBG
        elif led_pixel_order == 'GRB':
            px_order = driver.WS2811_STRIP_GRB
        elif led_pixel_order == 'GBR':
            px_order = driver.WS2811_STRIP_GBR
        elif led_pixel_order == 'BRG':
            px_order = driver.WS2811_STRIP_BRG
        elif led_pixel_order == 'BGR':
            px_order = driver.WS2811_STRIP_BGR
        elif led_pixel_order == 'RGBW':
            px_order = driver.SK6812_STRIP_RGBW
        elif led_pixel_order == 'RBGW':
            px_order = driver.SK6812_STRIP_RBGW
        elif led_pixel_order == 'GRBW':
            px_order = driver.SK6812_STRIP_GRBW
        elif led_pixel_order == 'GBRW':
            px_order = driver.SK6812_STRIP_GBRW
        elif led_pixel_order == 'BRGW':
            px_order = driver.SK6812_STRIP_BRGW
        elif led_pixel_order == 'BGRW':
            px_order = driver.SK6812_STRIP_BGRW

        self._has_white = 1 if 'W' in led_pixel_order else 0
        self._count = led_count

        # Create ws2811_t structure and fill in parameters
        self._leds = driver.new_ws2811_t()

        # Initialize the channels to zero
        for i in range(2):
            chan = driver.ws2811_channel_get(self._leds, i)
            driver.ws2811_channel_t_count_set(chan, 0)
            driver.ws2811_channel_t_gpionum_set(chan, 0)
            driver.ws2811_channel_t_invert_set(chan, 0)
            driver.ws2811_channel_t_brightness_set(chan, 0)

        # Initialize the channel in use
        self._channel = driver.ws2811_channel_get(self._leds, 0) # default
        driver.ws2811_channel_t_gamma_set(self._channel, list(range(256)))
        driver.ws2811_channel_t_count_set(self._channel, led_count)
        driver.ws2811_channel_t_gpionum_set(self._channel, led_pin)
        driver.ws2811_channel_t_invert_set(self._channel, 0) # 1 if true
        driver.ws2811_channel_t_brightness_set(self._channel, 255)
        driver.ws2811_channel_t_strip_type_set(self._channel, px_order)

        # Initialize the controller
        driver.ws2811_t_freq_set(self._leds, led_data_rate)
        driver.ws2811_t_dmanum_set(self._leds, led_dma_channel)

        # Substitute for __del__, traps an exit condition and cleans up properly
        atexit.register(self._cleanup)

        # Begin
        resp = driver.ws2811_init(self._leds)
        if resp != 0:
            str_resp = driver.ws2811_get_return_t_str(resp)
            raise RuntimeError('ws2811_init failed with code {0} ({1})'.format(resp, str_resp))

    def _cleanup(self):
        # Clean up memory used by the library when not needed anymore
        if self._leds is not None:
            driver.delete_ws2811_t(self._leds)
            self._leds = None
            self._channel = None

    def set_all_pixels_hsv_float(self, pixels, correction, saturation, brightness, gamma):
        driver.ws2811_hsv_render_array_float(self._leds, self._channel, pixels, len(pixels),
                                             correction, saturation, brightness, gamma,
                                             self._has_white)

    def set_all_pixels_rgb_float(self, pixels, correction, saturation, brightness, gamma):
        driver.ws2811_rgb_render_array_float(self._leds, self._channel, pixels, len(pixels),
                                             correction, saturation, brightness, gamma,
                                             self._has_white)
