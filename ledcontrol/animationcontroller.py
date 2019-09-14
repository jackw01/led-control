# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

import math
import random
import time
import traceback
import RestrictedPython
import copy
from threading import Event, Thread

import ledcontrol.animationpatterns as patterns
import ledcontrol.rpi_ws281x as rpi_ws281x
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
            if self.count % 100 == 0:
                print('Wait ratio: {}'.format(self.wait_time / self.interval))
            if (self.wait_time < 0):
                self.wait_time = 0

    def stop(self):
        """
        Stops the timer thread.
        """
        self.event.set()
        self.thread.join()

class AnimationController:
    def __init__(self, led_controller, refresh_rate, led_count, mapping_func, led_color_correction):
        self.led_controller = led_controller
        self.refresh_rate = refresh_rate
        self.led_count = led_count
        self.mapping_func = mapping_func

        # Initialize prev state arrays
        self.reset_prev_states()

        # Map led indices to normalized position vectors
        self.mapped = [self.mapping_func(i) for i in range(self.led_count)]

        # Check mapping dimensions to simplify loop if possible
        self.mapping_uses_x_only = True
        for point in self.mapped:
            if point.y != 0:
                self.mapping_uses_x_only = False

        # Create lists used to cache current mapping
        # so it doesn't have to be recalculated every frame
        self.primary_mapping = []
        self.secondary_mapping = []

        # Used to render main slider/select list
        self.params = {
            'master_brightness': 0.15,
            'master_color_temp': 6500,
            'master_saturation': 1.0,
            'primary_pattern': 0,
            'primary_speed': 0.2,
            'primary_scale': 1.0,
            'secondary_pattern': 0,
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
        self.secondary_pattern_functions = patterns.default_secondary

        # Color palette used for animations
        self.colors = [(0, 0, 1)]

        # Set default color temp
        self.correction_original = led_color_correction
        self.calculate_color_correction()

        # Set default mapping
        self.calculate_mappings()

        # Prepare to start
        self.start = time.perf_counter()
        self.time = 0
        self.render_perf_avg = 0

    def compile_pattern(self, source):
        """
        Compiles source string to a pattern function using restricted globals.
        """
        def getitem(obj, index):
            if obj is not None and type(obj) in (list, tuple, dict):
                return obj[index]
            raise Exception()

        def getiter(obj):
            return obj

        restricted_globals = {
            '__builtins__': RestrictedPython.Guards.safe_builtins,
            '_print_': RestrictedPython.PrintCollector,
            '_getattr_': RestrictedPython.Guards.safer_getattr,
            '_getitem_': getitem,
            '_getiter_': getiter,
            '_write_': RestrictedPython.Guards.full_write_guard,
            'math': math,
            'random': random,
            'hsv': patterns.ColorMode.hsv,
            'rgb': patterns.ColorMode.rgb,
            'clamp': utils.clamp,
            'wave_pulse': rpi_ws281x.wave_pulse,
            'wave_triangle': rpi_ws281x.wave_triangle,
            'wave_sine': rpi_ws281x.wave_sine,
            'wave_cubic': rpi_ws281x.wave_cubic,
            'impulse_exp': utils.impulse_exp,
            'fract': utils.fract,
            'blackbody_to_rgb': rpi_ws281x.blackbody_to_rgb,
            'blackbody_correction_rgb': rpi_ws281x.blackbody_correction_rgb,
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

    def calculate_color_correction(self):
        """
        Calculate and store color temperature correction.
        """
        rgb = [int(x * 255) for x in rpi_ws281x.blackbody_to_rgb(self.params['master_color_temp'])]
        c = [self.correction_original[0] * rgb[0] // 255,
             self.correction_original[1] * rgb[1] // 255,
             self.correction_original[2] * rgb[2] // 255]
        self.correction = (c[0] << 16) | (c[1] << 8) | c[2]

    def calculate_mappings(self):
        """
        Calculate and store spatial mapping values with current scale
        """
        self.primary_mapping = []
        self.secondary_mapping = []
        for i in range(self.led_count):
            # Calculate scale components to determine animation position
            # scale component = position (max size) / scale (pattern length in units)
            # One cycle is a normalized input value's transition from 0 to 1
            self.primary_mapping.append((
                (self.mapped[i][0] / self.params['primary_scale']) % 1,
                (self.mapped[i][1] / self.params['primary_scale']) % 1
            ))
            self.secondary_mapping.append((
                (self.mapped[i][0] / self.params['secondary_scale']) % 1,
                (self.mapped[i][1] / self.params['secondary_scale']) % 1
            ))

    def set_param(self, key, value):
        """
        Set an animation parameter.
        """
        self.params[key] = value
        if key == 'master_color_temp':
            self.calculate_color_correction()
        elif key == 'primary_scale' or key == 'secondary_scale':
            self.calculate_mappings()

    def set_pattern_function(self, key, source):
        """
        Update the source code and recompile a pattern function.
        """
        errors, warnings, pattern = self.compile_pattern(source)
        if len(errors) == 0:
            self.pattern_sources[key] = source
            self.pattern_functions[key] = pattern
        return errors, warnings

    def set_color(self, index, value):
        self.colors[index] = value

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

        pattern_1 = self.pattern_functions[self.params['primary_pattern']]
        pattern_2 = self.secondary_pattern_functions[self.params['secondary_pattern']]

        # Calculate times
        # time component = time (s) * speed (cycle/s)
        primary_time = self.time * self.params['primary_speed']
        primary_delta_t = self.timer.delta_t * self.params['primary_speed']
        secondary_time = self.time * self.params['secondary_speed']
        secondary_delta_t = self.timer.delta_t * self.params['secondary_speed']

        # Initialize these in case they don't get assigned later
        secondary_value = 1

        try:
            c, mode = self.pattern_functions[self.params['primary_pattern']](0,
                                                                             0.1,
                                                                             0,
                                                                             (0, 0, 0),
                                                                             [(0, 0, 0)])

            new_primary_prev_state = [pattern_1(primary_time,
                                 primary_delta_t,
                                 self.primary_mapping[i][0],
                                 self.primary_mapping[i][1],
                                 self.primary_prev_state[i],
                                 self.colors)[0] for i in range(self.led_count)]

            return [(c[0] * 1, c[1] * 1, c[2] * 1) for c in new_primary_prev_state]
            """
            for i in range(self.led_count):
                # Run primary pattern to determine initial color
                color, mode = pattern_1(primary_time,
                                        primary_delta_t,
                                        self.primary_mapping[i][0],
                                        self.primary_mapping[i][1],
                                        self.primary_prev_state[i],
                                        self.colors)
                new_primary_prev_state.append(color)

                # Run secondary pattern to determine new brightness and possibly modify color
                if pattern_2 is not None:
                    secondary_value, color = pattern_2(secondary_time,
                                                       secondary_delta_t,
                                                       self.secondary_mapping[i][0],
                                                       self.secondary_mapping[i][1],
                                                       self.secondary_prev_state[i],
                                                       color)
                    new_secondary_prev_state.append((secondary_value, color))

                if mode == patterns.ColorMode.hsv:
                    led_states.append((color[0], color[1], color[2] * secondary_value))
                elif mode == patterns.ColorMode.rgb:
                    led_states.append((color[0] * secondary_value,
                                       color[1] * secondary_value,
                                       color[2] * secondary_value))

            # Save current state as previous state
            self.primary_prev_state = new_primary_prev_state
            if pattern_2 is not None:
                self.secondary_prev_state = new_secondary_prev_state

            return led_states, mode
        """

        except Exception as e:
            print('Pattern execution: {}'.format(traceback.format_exception(type(e),
                                                                            e,
                                                                            e.__traceback__)))
            return [(0, 0, 0) for i in range(self.led_count)]

    def update_leds(self):
        """
        Determine time, render frame, and display.
        """
        self.time = self.timer.last_frame - self.start
        t0 = time.perf_counter()

        # Begin render
        # Create local references to patterns
        pattern_1 = self.pattern_functions[self.params['primary_pattern']]
        pattern_2 = self.secondary_pattern_functions[self.params['secondary_pattern']]

        # Calculate times
        # time component = time (s) * speed (cycle/s)
        primary_time = self.time * self.params['primary_speed']
        primary_delta_t = self.timer.delta_t * self.params['primary_speed']
        secondary_time = self.time * self.params['secondary_speed']
        secondary_delta_t = self.timer.delta_t * self.params['secondary_speed']

        # Determine current pattern mode
        c, mode = pattern_1(0, 0.1, 0, 0, (0, 0, 0), [(0, 0, 0)])

        # Run primary pattern to determine initial color
        state_1 = [(1, pattern_1(primary_time,
                            primary_delta_t,
                            self.primary_mapping[i][0],
                            self.primary_mapping[i][1],
                            self.primary_prev_state[i][1],
                            self.colors)[0]) for i in range(self.led_count)]
        self.primary_prev_state = state_1

        # Run secondary pattern to determine new brightness and possibly modify color
        if pattern_2 is not None:
            state_2 = [pattern_2(secondary_time,
                               secondary_delta_t,
                               self.secondary_mapping[i][0],
                               self.secondary_mapping[i][1],
                               self.secondary_prev_state[i],
                               s[1]) for i, s in enumerate(state_1)]
            self.secondary_prev_state = state_2
        else:
            state_2 = state_1

        # End render
        t1 = time.perf_counter()

        # Write colors to LEDs
        if mode == patterns.ColorMode.hsv:
            self.led_controller.leds.set_all_pixels_hsv_float(
                [(c[1][0], c[1][1], c[1][2] * c[0]) for c in state_2],
                self.correction,
                self.params['master_saturation'],
                self.params['master_brightness']
            )
        elif mode == patterns.ColorMode.rgb:
            self.led_controller.leds.set_all_pixels_rgb_float(
                [(c[1][0] * c[0], c[1][1] * c[0], c[1][2] * c[0]) for c in state_2],
                self.correction,
                self.params['master_saturation'],
                self.params['master_brightness']
            )

        self.render_perf_avg += (t1 - t0)
        if self.timer.count % 100 == 0:
            print(self.render_perf_avg / 100)
            self.render_perf_avg = 0

    def end_animation_thread(self):
        """
        Stop rendering in the animation thread.
        """
        self.timer.stop()
