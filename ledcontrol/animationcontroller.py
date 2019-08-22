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
        self.count = 0
        self.wait_time = 0
        self.last_frame = time.perf_counter()
        self.last_render_start = time.perf_counter()
        self.last_render_end = time.perf_counter()
        self.delta_t = interval
        self.event = Event()
        self.thread = Thread(target=self.target, daemon=True)
        self.thread.start()

    # Main event timer loop
    def target(self):
        while not self.event.wait(self.wait_time):
            self.last_render_start = time.perf_counter() # get start time
            if self.count % 100 == 0:
                print('FPS: {}'.format(1.0 / self.delta_t)) # print fps
            self.delta_t = self.last_render_start - self.last_frame # recalculate frame delta_t
            self.last_frame = self.last_render_start
            self.function(*self.args, **self.kwargs) # call target function
            self.count += 1
            self.last_render_end = time.perf_counter() # get end time

            # Calculate wait for next iteration
            self.wait_time = self.interval - (self.last_render_end - self.last_render_start)
            if (self.wait_time < 0):
                self.wait_time = 0

    def stop(self):
        self.event.set()
        self.thread.join()

class AnimationController:
    def __init__(self, led_controller, refresh_rate, led_count, mapping,
                 primary_pattern, secondary_pattern, led_color_correction):
        self.led_controller = led_controller
        self.refresh_rate = refresh_rate
        self.led_count = led_count
        self.mapping = mapping
        self.primary_pattern = primary_pattern
        self.secondary_pattern = secondary_pattern

        # Map led indices to normalized position vectors
        self.mapped = [self.mapping(i) for i in range(self.led_count)]
        # Initialize prev state arrays
        self.primary_prev_state = [(0, 0, 0) for i in range(self.led_count)]
        self.secondary_prev_state = [(0, (0, 0, 0)) for i in range(self.led_count)]

        self.correction_original = led_color_correction
        self.set_color_correction(6500)

        self.params = {
            'master_brightness': 0.15,
            'master_color_temp': 6500,
            'master_saturation': 1.0,
            'primary_speed': 0.2,
            'primary_scale': 1.0,
            'secondary_speed': 0.2,
            'secondary_scale': 1.0,
        }

        self.start = time.perf_counter()
        self.time = 0

    def set_color_correction(self, kelvin):
        temp_rgb = utils.blackbody2rgb_2(kelvin)
        c = [self.correction_original[0] * temp_rgb[0] // 255,
             self.correction_original[1] * temp_rgb[1] // 255,
             self.correction_original[2] * temp_rgb[2] // 255]
        self.correction = (c[0] << 16) | (c[1] << 8) | c[2]

    def set_param(self, key, value):
        self.params[key] = value
        if key == 'master_color_temp':
            self.set_color_correction(value)

    #def set_color(self, index, component, value):
    #    self.colors[index][component] = value

    def begin_animation_thread(self):
        self.timer = RepeatedTimer(1.0 / self.refresh_rate, self.update_leds)

    def get_next_frame(self):
        begin = time.perf_counter()
        new_primary_prev_state = []
        new_secondary_prev_state = []
        led_states = []

        # Calculate times
        # time component = time (s) * speed (cycle/s)
        primary_time = self.time * self.params['primary_speed']
        primary_delta_t = self.timer.delta_t * self.params['primary_speed']
        secondary_time = self.time * self.params['secondary_speed']
        secondary_delta_t = self.timer.delta_t * self.params['secondary_speed']

        for i in range(len(self.mapped)):
            # Calculate scale components to determine animation position
            # scale component = position (max size) / scale (pattern length in units)
            # One cycle is a normalized input value's transition from 0 to 1

            primary_scale_component_x = self.mapped[i][0] / self.params['primary_scale']
            primary_scale_component_y = self.mapped[i][1] / self.params['primary_scale']
            secondary_scale_component_x = self.mapped[i][0] / self.params['secondary_scale']
            secondary_scale_component_y = self.mapped[i][1] / self.params['secondary_scale']

            color_primary, mode = self.primary_pattern(primary_time,
                                                       primary_delta_t,
                                                       primary_scale_component_x,
                                                       primary_scale_component_y,
                                                       self.primary_prev_state[i])
            new_primary_prev_state.append(color_primary)

            secondary_value, color = self.secondary_pattern(secondary_time,
                                                              secondary_delta_t,
                                                              secondary_scale_component_x,
                                                              secondary_scale_component_y,
                                                              self.secondary_prev_state[i],
                                                              color_primary)
            new_secondary_prev_state.append((secondary_value, color))

            h = int((color[0] % 1) * 255)
            s = int(color[1] * self.params['master_saturation'] * 255)
            v = int(color[2] * secondary_value * self.params['master_brightness'] * 255)
            led_states.append((h, s, v))
            """
            h = int(0.5 * 255)
            s = int(1.0 * self.params['master_saturation'] * 255)
            v = int(1.0 * self.params['master_brightness'] * 255)
            led_states.append((h, s, v))
            """

        self.primary_prev_state = new_primary_prev_state
        self.secondary_prev_state = new_secondary_prev_state
        return led_states

    def update_leds(self):
        self.time = self.timer.last_frame - self.start
        self.led_controller.leds.set_all_pixels_hsv2(self.get_next_frame(), self.correction)

    def end_animation_thread(self):
        self.timer.stop()
