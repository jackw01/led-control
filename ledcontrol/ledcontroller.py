# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

import colorsys, rpi_ws281x

# Using colorsys
def hsv2rgb_colorsys(triplet):
    return [int(x * 255) for x in colorsys.hsv_to_rgb(triplet[0], triplet[1], triplet[2])]

# Marginally faster than colorsys
def hsv2rgb_fast(triplet):
    (hue, sat, val) = [int(x * 255) for x in triplet]

    if sat == 0:
        return (val, val, val)

    brightness_floor = val * (255 - sat) // 256
    color_amplitude = val - brightness_floor 
    section = hue // 85
    offset = hue % 85
    rampup_adj_with_floor = offset * color_amplitude // 64 + brightness_floor
    rampdown_adj_with_floor = (85 - 1 - offset) * color_amplitude // 64 + brightness_floor

    if section:
        if section == 1:
            return [brightness_floor, rampdown_adj_with_floor, rampup_adj_with_floor]
        else:
            return [rampup_adj_with_floor, brightness_floor, rampdown_adj_with_floor]
    else:
        return [rampdown_adj_with_floor, rampup_adj_with_floor, brightness_floor]

# "Rainbow" color transform from FastLED, also marginally faster than colorsys
def hsv2rgb_fast_rainbow(triplet):
    (hue, sat, val) = [int(x * 255) for x in triplet]

    offset = hue & 0x1F # 0 to 31
    offset8 = offset << 3
    third = offset8 // 3 # max = 85

    r = 0
    g = 0
    b = 0

    if not (hue & 0x80):
        # 0XX
        if not (hue & 0x40):
            # 00X
            # section 0-1
            if not (hue & 0x20):
                # 000
                # case 0: # R -> O
                r = 255 - third
                g = third
                b = 0
            else:
                # 001
                # case 1: # O -> Y
                r = 171
                g = 85 + third
                b = 0
        else:
            # 01X
            # section 2-3
            if not (hue & 0x20):
                # 010
                # case 2: # Y -> G
                twothirds = offset8 * 2 // 3 # max=170
                r = 171 - twothirds
                g = 170 + third
                b = 0
            else:
                # 011
                # case 3: # G -> A
                r = 0
                g = 255 - third
                b = third
    else:
        # section 4-7
        # 1XX
        if not (hue & 0x40):
            # 10X
            if not (hue & 0x20):
                # 100
                # case 4: # A -> B
                r = 0
                twothirds = offset8 * 2 // 3 # max=170
                g = 171 - twothirds
                b = 85 + twothirds
            else:
                # 101
                # case 5: # B -> P
                r = third
                g = 0
                b = 255 - third
        else:
            if not (hue & 0x20):
                # 110
                # case 6: # P -- K
                r = 85 + third
                g = 0
                b = 171 - third
            else:
                # 111
                # case 7: # K -> R
                r = 170 + third
                g = 0
                b = 85 - third

    # This is one of the good places to scale the green down,
    # although the client can scale green down as well.
    #g = g >> 1

    # Scale down colors if we're desaturated at all
    # and add the brightness_floor to r, g, and b.
    if sat != 255:
        if sat == 0:
            r = 255
            b = 255
            g = 255
        else:
            desat = 255 - sat
            desat = desat * desat // 255
            r = r * sat // 255 + desat
            g = g * sat // 255 + desat
            b = b * sat // 255 + desat

    # Now scale everything down if we're at value < 255.
    if val != 255:
        val * val // 255
        if val == 0:
            r = 0
            g = 0
            b = 0
        else:
            r = r * val // 255
            g = g * val // 255
            b = b * val // 255

    return (r, g, b)

class LEDController:
    def __init__(self, led_count, led_pin,
                 led_data_rate, led_dma_channel, led_strip_type, led_pixel_order):
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

        self.leds = rpi_ws281x.PixelStrip(led_count, led_pin,
                                          led_data_rate, led_dma_channel,
                                          False, # invert?
                                          255, # master brightness
                                          0, # channel
                                          px_order)
        self.count = led_count
        self.leds.begin()
        self.clear()

    def clear(self):
        for i in range(self.count):
            self.leds.setPixelColor(i, rpi_ws281x.Color(0, 0, 0))
        self.leds.show()

    def set_led_states(self, led_states):
        for i in range(len(led_states)):
            self.leds.setPixelColor(i, rpi_ws281x.Color(*hsv2rgb_fast_rainbow(led_states[i])))
        self.leds.show()
