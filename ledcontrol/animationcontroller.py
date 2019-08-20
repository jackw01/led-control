# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

import math
import time
from enum import Enum
from threading import Event, Thread
import ledcontrol.utils as utils

ColorMode = Enum('ColorMode', ['hsv', 'rgb'])

class RepeatedTimer:
    """Repeat `function` every `interval` seconds."""

    def __init__(self, interval, function, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.last_frame = time.time()
        self.last_render_start = time.time()
        self.last_render_end = time.time()
        self.event = Event()
        self.thread = Thread(target=self.target, daemon=True)
        self.thread.start()

    def target(self):
        while not self.event.wait(self.wait_time):
            self.last_render_start = time.time()
            print('FPS: {}'.format(1.0 / (self.last_render_start - self.last_frame))) # fps
            self.last_frame = self.last_render_start
            self.function(*self.args, **self.kwargs) # call target function
            self.last_render_end = time.time()

    @property
    def wait_time(self): # calculate wait time based on last frame duration
        wait = max(0, self.interval - (self.last_render_end - self.last_render_start))
        return wait

    def stop(self):
        self.event.set()
        self.thread.join()

class AnimationController:
    def __init__(self, led_controller, refresh_rate, led_count, mapping, pattern):
        self.led_controller = led_controller
        self.refresh_rate = refresh_rate
        self.led_count = led_count
        self.mapping = mapping
        self.pattern = pattern

        # map led indices to normalized position vectors
        self.mappedPoints = [self.mapping(i) for i in range(self.led_count)]

        self.params = {
            'master_brightness': 0.05,
            'master_color_temp': 6500,
            'master_saturation': 1.0,
            'primary_speed': 0.2,
            'primary_scale': 1.0,
        }

        self.start = time.time()
        self.time = 0

    def set_param(self, key, value):
        self.params[key] = value
        if key == 'master_color_temp':
            self.led_controller.set_color_temp(value)

    #def set_color(self, index, component, value):
    #    self.colors[index][component] = value

    def begin_animation_thread(self):
        self.timer = RepeatedTimer(1.0 / self.refresh_rate, self.update_leds)

    def get_next_frame(self):
        led_states = []
        for point in self.mappedPoints:
            # Calculate time and scale components to determine animation position
            # time component = time (s) * speed (cycle/s)
            # scale component = position (max size) * scale (repeats / max size)
            # one cycle is a normalized input value's transition from 0 to 1
            primary_time_component = self.time * self.params['primary_speed']
            primary_scale_component_x = point.x * self.params['primary_scale']
            primary_scale_component_y = point.y * self.params['primary_scale']

            color, mode = self.pattern((primary_time_component + primary_scale_component_x) % 1.0,
                                       (primary_time_component + primary_scale_component_y) % 1.0)

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

            # Apply master brightness and saturation if using hsv
            if (mode == ColorMode.hsv):
                color = utils.hsv2rgb_fast_rainbow([color[0],
                                                    color[1] * self.params['master_saturation'],
                                                    color[2] * self.params['master_brightness']])
            else:
                color = [int(color[0] * self.params['master_brightness'] * 255),
                         int(color[1] * self.params['master_brightness'] * 255),
                         int(color[2] * self.params['master_brightness'] * 255)]

            led_states.append(color)

        return led_states

    def update_leds(self):
        self.time = self.timer.last_frame - self.start
        self.led_controller.set_led_states(self.get_next_frame())

    def end_animation_thread(self):
        self.timer.stop()
