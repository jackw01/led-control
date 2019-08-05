# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

import math
import time
import colorsys
from threading import Event, Thread
from ledcontrol.ledmodes import LEDColorAnimationMode, LEDSecondaryAnimationMode

def hsv_to_rgb(triplet):
	return [int(x * 255) for x in colorsys.hsv_to_rgb(triplet[0], triplet[1], triplet[2])]

def hsv_to_rgb_norm(triplet):
	return colorsys.hsv_to_rgb(triplet[0], triplet[1], triplet[2])

class RepeatedTimer:
	"""Repeat `function` every `interval` seconds."""

	def __init__(self, interval, function, *args, **kwargs):
		self.interval = interval
		self.function = function
		self.args = args
		self.kwargs = kwargs
		self.start = time.time()
		self.event = Event()
		self.thread = Thread(target=self._target, daemon=True)
		self.thread.start()

	def _target(self):
		while not self.event.wait(self._time):
			self.function(*self.args, **self.kwargs)

	@property
	def _time(self):
		return self.interval - ((time.time() - self.start) % self.interval)

	def stop(self):
		self.event.set()
		self.thread.join()

class AnimationController:
	def __init__(self, led_controller, refresh_rate, led_count, mapping):
		self.led_controller = led_controller
		self.refresh_rate = refresh_rate
		self.led_count = led_count
		self.mapping = mapping

		self.params = {
			'master_brightness' : 1.0,
			'master_saturation': 1.0,
			'primary_speed': 0.2,
			'primary_scale': 10,
		}

		self.time = 0

	def begin_animation_thread(self):
		self.timer = RepeatedTimer(1 / self.refresh_rate, self.update_leds)

	def get_next_frame(self):
		led_states = []
		for i in enumerate(self.led_count):
			point = self.mapping(i)
			color = (0.0, 0.0, 0.0)
			primary_time_component = self.time * self.params['primary_speed']
			primary_scale_component = point[0] / float(self.params['primary_scale'])

			"""
			if self.params['color_animation_mode'] == LEDColorAnimationMode.SolidColor:
				color = self.colors[0]

			elif self.params['color_animation_mode'] == LEDColorAnimationMode.CycleHue:
				color = ((color_anim_time + color_anim_scale) % 1.0,
						 self.params['saturation'], 1.0)

			elif self.params['color_animation_mode'] == LEDColorAnimationMode.Sines:
				rgb = hsv_to_rgb_norm(self.colors[0])
				r_half, g_half, b_half = [x / 2 for x in rgb]
				r = r_half * math.sin(math.pi * color_anim_time * 10 * self.params['red_frequency'] +
										self.params['red_phase_offset'] + color_anim_scale) + r_half
				g = g_half * math.sin(math.pi * color_anim_time * 10 * self.params['green_frequency'] +
										self.params['green_phase_offset'] + color_anim_scale) + g_half
				b = b_half * math.sin(math.pi * color_anim_time * 10 * self.params['blue_frequency'] +
										self.params['blue_phase_offset'] + color_anim_scale) + b_half
				color = colorsys.rgb_to_hsv(r, g, b)

			color = [color[0], color[1], color[2]]

			if self.params['secondary_animation_mode'] == LEDSecondaryAnimationMode.Static:
				pass

			elif self.params['secondary_animation_mode'] == LEDSecondaryAnimationMode.Wave:
				color[2] *= (0.5 * math.sin(2 * math.pi * sec_anim_time +
											2 * math.pi * sec_anim_scale) + 0.5) ** 1.7

			elif self.params['secondary_animation_mode'] == LEDSecondaryAnimationMode.Trail:
				color[2] *= (1.0 - (sec_anim_time + sec_anim_scale) % 1) ** 4
			"""

			color[1] *= self.params['master_saturation']
			color[2] *= self.params['master_brightness']
			led_states.append(hsv_to_rgb(color))

		self.time += 1.0 / self.refresh_rate
		return led_states

	def update_leds(self):
		self.led_controller.set_led_states(self.get_next_frame())

	def end_animation_thread(self):
		self.timer.stop()
