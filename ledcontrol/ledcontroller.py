import neopixel

class LEDController:
    def __init__(self, num_leds, led_pin, led_data_rate, led_dma_channel, led_pixel_order):
        self.leds = neopixel.Adafruit_NeoPixel(num_leds, led_pin, led_data_rate, led_dma_channel, False, 255)
        self.px_order = led_pixel_order
        self.leds.begin()
        for i in range(num_leds):
            self.leds.setPixelColor(i, neopixel.Color(0, 0, 0))
        self.leds.show()

    def set_led_states(self, led_states):
        for i, state in enumerate(led_states):
            if (self.px_order == 'GRB'):
                self.leds.setPixelColor(i, neopixel.Color(state[1], state[0], state[2]))
            else:
                self.leds.setPixelColor(i, neopixel.Color(state[0], state[1], state[2]))
        self.leds.show()
