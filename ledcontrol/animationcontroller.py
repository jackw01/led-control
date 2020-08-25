# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

import math
import random
import time
import traceback
import RestrictedPython
from threading import Event, Thread
from ledcontrol.controlclient import ControlClient

import ledcontrol.animationpatterns as animpatterns
import ledcontrol.colorpalettes as colorpalettes
import ledcontrol.rpi_ws281x as rpi_ws281x
import ledcontrol.utils as utils

class RepeatedTimer:
    'Repeat function call at a regular interval'

    def __init__(self, interval, function, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.count = 0
        self.wait_time = 0
        self.last_start = time.perf_counter()
        self.last_measurement_c = 0
        self.last_measurement_t = 0
        self.perf_avg = 0
        self.event = Event()
        self.thread = Thread(target=self.target, daemon=True)

    def start(self):
        'Starts the timer thread'
        self.thread.start()

    def target(self):
        'Waits until ready and executes target function'
        while not self.event.wait(self.wait_time):
            self.last_start = time.perf_counter()
            self.function(*self.args, **self.kwargs)
            self.perf_avg += (time.perf_counter() - self.last_start)

            self.count += 1
            if self.count % 100 == 0:
                print('Average execution time (s): {}'.format(self.perf_avg / 100))
                print('Average speed (cycles/s): {}'.format(
                    (self.count - self.last_measurement_c)
                    / (self.last_start - self.last_measurement_t)
                ))
                self.last_measurement_c = self.count
                self.last_measurement_t = self.last_start
                self.perf_avg = 0

            # Calculate wait for next iteration
            self.wait_time = self.interval - (time.perf_counter() - self.last_start)
            if (self.wait_time < 0):
                self.wait_time = 0

    def stop(self):
        'Stops the timer thread'
        self.event.set()
        self.thread.join()

class AnimationController:
    def __init__(self, led_controller, refresh_rate, led_count,
                 mapping_func,
                 led_color_correction):
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
            'master_gamma': 1.0,
            'master_saturation': 1.0,
            'primary_pattern': 0,
            'primary_speed': 0.2,
            'primary_scale': 1.0,
            'secondary_pattern': 0,
            'secondary_speed': 0.2,
            'secondary_scale': 1.0,
            'palette': 0,
            'direct_control_mode': 0,
        }

        # Lookup dictionary for pattern functions used to generate select menu
        self.pattern_functions = {}

        # Initialize primary patterns
        for k, v in animpatterns.default.items():
            self.set_pattern_function(k, v['source'])

        # Lookup dictionary for secondary pattern functions
        self.secondary_pattern_functions = animpatterns.default_secondary

        # Color palette used for animations
        self.palette_table_size = 1000
        self.palettes = dict(colorpalettes.default)
        self.calculate_palette_table()

        # Set default color temp
        self.correction_original = led_color_correction
        self.calculate_color_correction()

        # Set default mapping
        self.calculate_mappings()

        # Prepare to start
        self.start = time.perf_counter()
        self.time = 0

        self.control_client = ControlClient()

    def compile_pattern(self, source):
        'Compiles source string to a pattern function with restricted globals'
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
            'palette': self.get_palette_color,
            'palette_length': self.get_palette_length,
            'hsv': animpatterns.ColorMode.hsv,
            'rgb': animpatterns.ColorMode.rgb,
            'clamp': utils.clamp,
            'wave_pulse': rpi_ws281x.wave_pulse,
            'wave_triangle': rpi_ws281x.wave_triangle,
            'wave_sine': rpi_ws281x.wave_sine,
            'wave_cubic': rpi_ws281x.wave_cubic,
            'plasma_sines': rpi_ws281x.plasma_sines,
            'plasma_sines_octave': rpi_ws281x.plasma_sines_octave,
            'perlin_noise_3d': rpi_ws281x.perlin_noise_3d,
            'impulse_exp': utils.impulse_exp,
            'fract': utils.fract,
            'blackbody_to_rgb': rpi_ws281x.blackbody_to_rgb,
            'blackbody_correction_rgb': rpi_ws281x.blackbody_correction_rgb,
        }
        restricted_locals = {}
        arg_names = ['t', 'dt', 'x', 'y', 'prev_state']

        results = RestrictedPython.compile_restricted_exec(source)
        warnings = list(results.warnings)
        for name in results.used_names:
            if name not in restricted_globals and name not in arg_names:
                warnings.append(f'NameError: name \'{name}\' is not defined')

        if results.code:
            exec(results.code, restricted_globals, restricted_locals)
            return results.errors, warnings, restricted_locals['pattern']
        else:
            return results.errors, warnings, None

    def reset_prev_states(self):
        'Reset previous animation state lists'
        blank = [((0, 0, 0), 0) for i in range(self.led_count)]
        self.primary_prev_state = blank[:]
        self.secondary_prev_state = blank[:]

    def calculate_color_correction(self):
        'Calculate and store color temperature correction'
        rgb = rpi_ws281x.blackbody_to_rgb(self.params['master_color_temp'])
        c = [self.correction_original[0] * int(rgb[0] * 255) // 255,
             self.correction_original[1] * int(rgb[1] * 255) // 255,
             self.correction_original[2] * int(rgb[2] * 255) // 255]
        self.correction = (c[0] << 16) | (c[1] << 8) | c[2]

    def calculate_mappings(self):
        'Calculate and store spatial mapping values with current scale'
        p = []
        s = []
        if self.params['primary_scale'] != 0:
            for i in range(self.led_count):
                # Calculate scale components to determine animation position
                # scale component = position / scale (pattern length in units)
                # One cycle is a normalized input value's transition from 0 to 1
                p.append((
                    (self.mapped[i][0] / self.params['primary_scale']) % 1,
                    (self.mapped[i][1] / self.params['primary_scale']) % 1
                ))
        else:
            p = [(0, 0) for i in range(self.led_count)]

        if self.params['secondary_scale'] != 0:
            for i in range(self.led_count):
                s.append((
                    (self.mapped[i][0] / self.params['secondary_scale']) % 1,
                    (self.mapped[i][1] / self.params['secondary_scale']) % 1
                ))
        else:
            s = [(0, 0) for i in range(self.led_count)]

        self.primary_mapping = p
        self.secondary_mapping = s

    def set_param(self, key, value):
        'Set an animation parameter'
        self.params[key] = value
        if key == 'master_color_temp':
            self.calculate_color_correction()
        elif key == 'primary_scale' or key == 'secondary_scale':
            self.calculate_mappings()
        elif key == 'palette':
            self.calculate_palette_table()

    def set_pattern_function(self, key, source):
        'Update the source code and recompile a pattern function'
        errors, warnings, pattern = self.compile_pattern(source)
        if len(errors) == 0:
            self.pattern_functions[key] = pattern
        elif key not in self.pattern_functions:
            self.pattern_functions[key] = animpatterns.blank
        return errors, warnings

    def calculate_palette_table(self):
        'Set the color palette and recalculate the lookup table'
        palette = self.palettes[self.params['palette']]
        palette_table = []
        sector_size = 1.0 / (len(palette['colors']) - 1)
        for i in range(self.palette_table_size):
            f = i / self.palette_table_size
            sector = math.floor(f / sector_size)
            f = f % sector_size / sector_size
            c1, c2 = palette['colors'][sector], palette['colors'][sector + 1]
            # Allow full spectrum if extremes are 0 and 1 in any order
            # otherwise pick shortest path between colors
            h1, h2 = c2[0] - c1[0], c2[0] - 1.0 - c1[0]
            palette_table.append((
                f * (h1 if abs(h1) < abs(h2) or h1 == 1.0 else h2) + c1[0],
                f * (c2[1] - c1[1]) + c1[1],
                f * (c2[2] - c1[2]) + c1[2],
            ))
        self.palette_table = palette_table
        self.palette_length = len(palette['colors'])

    def get_palette_color(self, t):
        'Get color from current palette corresponding to index between 0 and 1'
        return self.palette_table[int(t * self.palette_table_size) % self.palette_table_size]

    def get_palette_length(self):
        'Get length of current palette color array'
        return self.palette_length

    def set_palette(self, key, value):
        'Update palette'
        self.palettes[key] = value

    def delete_palette(self, key):
        'Delete palette'
        del self.palettes[key]

    def begin_animation_thread(self):
        'Start animating'
        self.timer = RepeatedTimer(1.0 / self.refresh_rate, self.update_leds)
        self.timer.start()

    def update_leds(self):
        'Determine time, render frame, and display'
        last_t = self.time
        self.time = self.timer.last_start - self.start
        delta_t = self.time - last_t

        # Begin render
        # Create local references to patterns
        pattern_1 = self.pattern_functions[self.params['primary_pattern']]
        pattern_2 = self.secondary_pattern_functions[self.params['secondary_pattern']]

        # Calculate times
        # time component = time (s) * speed (cycle/s)
        primary_time = self.time * self.params['primary_speed']
        primary_delta_t = delta_t * self.params['primary_speed']
        secondary_time = self.time * self.params['secondary_speed']
        secondary_delta_t = delta_t * self.params['secondary_speed']

        mode = animpatterns.ColorMode.hsv

        try:
            # Determine current pattern mode
            c, mode = pattern_1(0, 0.1, 0, 0, (0, 0, 0))

            # Run primary pattern to determine initial color
            # State is an array of (color, secondary_value) pairs
            s_1 = [(pattern_1(primary_time,
                              primary_delta_t,
                              self.primary_mapping[i][0],
                              self.primary_mapping[i][1],
                              self.primary_prev_state[i][0])[0],
                    1) for i in range(self.led_count)]
            self.primary_prev_state = s_1

            # Run secondary pattern to get new brightness and modify color
            if pattern_2 is None:
                s_2 = s_1
            else:
                s_2 = [pattern_2(secondary_time,
                                 secondary_delta_t,
                                 self.secondary_mapping[i][0],
                                 self.secondary_mapping[i][1],
                                 self.secondary_prev_state[i],
                                 s_1[i][0]) for i in range(self.led_count)]
                self.secondary_prev_state = s_2

            # Direct control mode override
            if self.params['direct_control_mode']:
                s_2 = self.control_client.get_frame(self.led_count)
                mode = animpatterns.ColorMode.hsv

        except Exception as e:
            msg = traceback.format_exception(type(e), e, e.__traceback__)
            print(f'Pattern execution: {msg}')
            s_2 = [((0, 0, 0), 0) for i in range(self.led_count)]

        # Write colors to LEDs
        if mode == animpatterns.ColorMode.hsv:
            self.led_controller.leds.set_all_pixels_hsv_float(
                [(c[0][0] % 1, c[0][1], c[0][2] * c[1]) for c in s_2],
                self.correction,
                self.params['master_saturation'],
                self.params['master_brightness'],
                self.params['master_gamma']
            )
        elif mode == animpatterns.ColorMode.rgb:
            self.led_controller.leds.set_all_pixels_rgb_float(
                [(c[0][0] * c[1], c[0][1] * c[1], c[0][2] * c[1]) for c in s_2],
                self.correction,
                self.params['master_saturation'],
                self.params['master_brightness'],
                self.params['master_gamma']
            )

    def end_animation_thread(self):
        'Stop rendering in the animation thread'
        self.timer.stop()
