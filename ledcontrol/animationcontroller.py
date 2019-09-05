# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

import math
import random
import time
import RestrictedPython
from threading import Event, Thread

import ledcontrol.animationpatterns as patterns
import ledcontrol.utils as utils

class RepeatedTimer:
    """
    Repeat function call at a regular interval.
    """

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

    def target(self):
        """
        Waits until ready and executes target function.
        """
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
        """
        Stops the timer thread.
        """
        self.event.set()
        self.thread.join()

class AnimationController:
    def __init__(self, led_controller, refresh_rate, led_count, mapping, led_color_correction):
        self.led_controller = led_controller
        self.refresh_rate = refresh_rate
        self.led_count = led_count
        self.mapping = mapping

        # Map led indices to normalized position vectors
        self.mapped = [self.mapping(i) for i in range(self.led_count)]
        # Initialize prev state arrays
        self.reset_prev_states()

        # Check mapping dimensions to simplify loop if possible
        self.mapping_uses_x_only = True
        for point in self.mapped:
            if point.y != 0:
                self.mapping_uses_x_only = False

        # Used to render main slider/select list
        self.params = {
            'master_brightness': 0.15,
            'master_color_temp': 6500,
            'master_saturation': 1.0,
            'primary_pattern': 'cycle_hue_1d',
            'primary_speed': 0.2,
            'primary_scale': 1.0,
            'secondary_pattern': 'none',
            'secondary_speed': 0.2,
            'secondary_scale': 1.0,
        }

        # Source code for patterns
        self.pattern_sources = {}
        # Lookup dictionary for pattern functions - keys are used to generate select menu
        self.pattern_functions = {}

        # Initialize primary patterns
        for k, v in patterns.default.items():
            self.set_pattern_function(k, v)

        # Lookup dictionary for secondary pattern functions
        self.secondary_pattern_functions = {
            'none': None,
        }

        # Color palette used for animations
        self.colors = [(0, 0, 1)]

        # Set default color temp
        self.correction_original = led_color_correction
        self.set_color_correction(self.params['master_color_temp'])
        # Prepare to start
        self.start = time.perf_counter()
        self.time = 0

    def compile_pattern(self, source):
        """
        Compiles source string to a pattern function using restricted globals.
        """
        def getitem(obj, index):
            if obj is not None and type(obj) in (list, tuple, dict):
                return obj[index]
            raise Exception()

        restricted_globals = {
            '__builtins__': RestrictedPython.Guards.safe_builtins,
            '_print_': RestrictedPython.PrintCollector,
            '_getattr_': RestrictedPython.Guards.safer_getattr,
            '_getitem_': getitem,
            '_write_': RestrictedPython.Guards.full_write_guard,
            'math': math,
            'random': random,
            'hsv': patterns.ColorMode.hsv,
            'rgb': patterns.ColorMode.rgb,
            'clamp': utils.clamp,
            'wave_pulse': utils.wave_pulse,
            'wave_triangle': utils.wave_triangle,
            'wave_sine': utils.wave_sine,
            'impulse_exp': utils.impulse_exp,
            'fract': utils.fract,
        }
        restricted_locals = {}
        arg_names = ['t', 'dt', 'x', 'y', 'prev_state']

        name_error = False
        results = RestrictedPython.compile_restricted_exec(source, filename='<inline code>')
        print(results)
        warnings = list(results.warnings)
        for name in results.used_names:
            if name not in restricted_globals and name not in arg_names:
                name_error = True
                warnings.append('NameError: name \'{}\' is not defined'.format(name))

        if results.code:
            exec(results.code, restricted_globals, restricted_locals)
            return results.errors, warnings, restricted_locals['pattern']
        else:
            return results.errors, warnings, None

    def reset_prev_states(self):
        """
        Reset previous animation state lists.
        """
        self.primary_prev_state = [(0, 0, 0) for i in range(self.led_count)]
        self.secondary_prev_state = [(0, (0, 0, 0)) for i in range(self.led_count)]

    def set_color_correction(self, kelvin):
        """
        Set blackbody color temperature correction.
        """
        temp_rgb = utils.blackbody2rgb_2(kelvin)
        c = [self.correction_original[0] * temp_rgb[0] // 255,
             self.correction_original[1] * temp_rgb[1] // 255,
             self.correction_original[2] * temp_rgb[2] // 255]
        self.correction = (c[0] << 16) | (c[1] << 8) | c[2]

    def set_param(self, key, value):
        """
        Set an animation parameter.
        """
        self.params[key] = value
        if key == 'master_color_temp':
            self.set_color_correction(value)

    def set_pattern_function(self, key, source):
        """
        Update the source code and recompile a pattern function.
        """
        errors, warnings, pattern = self.compile_pattern(source)
        if len(errors) == 0:
            self.pattern_sources[key] = source
            self.pattern_functions[key] = pattern
        return errors, warnings

    def set_color_component(self, index, component, value):
        self.colors[index][component] = value

    def begin_animation_thread(self):
        """
        Start animating.
        """
        self.timer = RepeatedTimer(1.0 / self.refresh_rate, self.update_leds)

    def get_next_frame(self):
        """
        Render the next frame based on current time.
        """
        new_primary_prev_state = []
        new_secondary_prev_state = []
        led_states = []
        mode = patterns.ColorMode.hsv

        pattern_1 = self.pattern_functions[self.params['primary_pattern']]
        pattern_2 = self.secondary_pattern_functions[self.params['secondary_pattern']]

        # Calculate times
        # time component = time (s) * speed (cycle/s)
        primary_time = self.time * self.params['primary_speed']
        primary_delta_t = self.timer.delta_t * self.params['primary_speed']
        secondary_time = self.time * self.params['secondary_speed']
        secondary_delta_t = self.timer.delta_t * self.params['secondary_speed']

        # Initialize these in case they don't get assigned later
        primary_x = 0
        primary_y = 0
        secondary_x = 0
        secondary_y = 0
        secondary_value = 1

        try:
            for i in range(len(self.mapped)):
                # Calculate scale components to determine animation position
                # scale component = position (max size) / scale (pattern length in units)
                # One cycle is a normalized input value's transition from 0 to 1

                if self.params['primary_scale'] != 0:
                    primary_x = (self.mapped[i][0] / self.params['primary_scale']) % 1
                    if not self.mapping_uses_x_only:
                        primary_y =(self.mapped[i][1] / self.params['primary_scale']) % 1

                # Run primary pattern to determine initial color
                color, mode = pattern_1(primary_time,
                                        primary_delta_t,
                                        primary_x,
                                        primary_y,
                                        self.primary_prev_state[i],
                                        self.colors)
                new_primary_prev_state.append(color)

                # Run secondary pattern to determine new brightness and possibly modify color
                if pattern_2 is not None:
                    if self.params['primary_scale'] != 0:
                        secondary_x = (self.mapped[i][0] / self.params['secondary_scale']) % 1
                        if not self.mapping_uses_x_only:
                            secondary_y = (self.mapped[i][1] / self.params['secondary_scale']) % 1

                    secondary_value, color = pattern_2(secondary_time,
                                                       secondary_delta_t,
                                                       secondary_x,
                                                       secondary_y,
                                                       self.secondary_prev_state[i],
                                                       color)
                    new_secondary_prev_state.append((secondary_value, color))

                if mode == patterns.ColorMode.hsv:
                    led_states.append((color[0], color[1], color[2] * secondary_value))
                elif mode == patterns.ColorMode.rgb:
                    led_states.append((color[0] * secondary_value,
                                       color[1] * secondary_value,
                                       color[2] * secondary_value))

            self.primary_prev_state = new_primary_prev_state
            self.secondary_prev_state = new_secondary_prev_state
            return led_states, mode

        except Exception as e:
            print('Pattern execution: {}: {}'.format(type(e).__name__, e))
            return [(0, 0, 0) for i in range(self.led_count)]

    def update_leds(self):
        """
        Determine time, render frame, and display.
        """
        self.time = self.timer.last_frame - self.start
        led_states, mode = self.get_next_frame()
        if mode == patterns.ColorMode.hsv:
            self.led_controller.leds.set_all_pixels_hsv_float(led_states, self.correction,
                                                              self.params['master_saturation'],
                                                              self.params['master_brightness'])
        elif mode == patterns.ColorMode.rgb:
            self.led_controller.leds.set_all_pixels_rgb_float(led_states, self.correction,
                                                              self.params['master_saturation'],
                                                              self.params['master_brightness'])

    def end_animation_thread(self):
        """
        Stop rendering in the animation thread.
        """
        self.timer.stop()
