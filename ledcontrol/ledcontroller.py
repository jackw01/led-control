# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

from neopixel import Adafruit_NeoPixel

class LEDController:
	def __init__(self, led_count, led_pin, led_data_rate, led_dma_channel, led_pixel_order):
		self.leds = Adafruit_NeoPixel(led_count, led_pin, led_data_rate, led_dma_channel, False, 255)
		self.px_order = led_pixel_order
		self.leds.begin()
		for i in range(led_count):
			self.leds.setPixelColor(i, neopixel.Color(0, 0, 0))
		self.leds.show()

	def set_led_states(self, led_states):
		for i, state in enumerate(led_states):
			if (self.px_order == 'GRB'):
				self.leds.setPixelColor(i, neopixel.Color(state[1], state[0], state[2]))
			else:
				self.leds.setPixelColor(i, neopixel.Color(state[0], state[1], state[2]))
		self.leds.show()
