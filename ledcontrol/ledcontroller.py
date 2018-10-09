import colorsys
import neopixel

class ColorHSV:
    def __init__(self, triplet):
        self.h = triplet[0]
        self.s = triplet[1]
        self.v = triplet[2]

    def rgb(self):
        # TODO: FastLED style conversion
        return [int(x * 255) for x in colorsys.hsv_to_rgb(self.h, self.s, self.v)]

class LEDController:
    def __init__(self, num_leds, led_pin, led_data_rate, led_dma_channel):
        self.leds = neopixel.Adafruit_NeoPixel(num_leds, led_pin, led_data_rate, led_dma_channel, False, 255)
        self.leds.begin()
        for i in range(num_leds):
            self.leds.setPixelColor(i, neopixel.Color(0, 0, 0))
        self.leds.show()

    def set_led_states(self, led_states):
        for i, state in enumerate(led_states):
            rgb = state.rgb()
            self.leds.setPixelColor(i, neopixel.Color(rgb[0], rgb[1], rgb[2]))
        self.leds.show()
