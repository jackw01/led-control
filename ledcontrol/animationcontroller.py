# led-control WS2812B LED Controller Server
# Copyright 2021 jackw01. Released under the MIT License (see LICENSE for details).

import math
import random
import time
import traceback
import RestrictedPython
import sacn
from itertools import zip_longest
from ledcontrol.intervaltimer import IntervalTimer

import ledcontrol.animationpatterns as animpatterns
import ledcontrol.colorpalettes as colorpalettes
import ledcontrol.driver as driver
import ledcontrol.utils as utils

class AnimationController:
    def __init__(self,
                 led_controller,
                 refresh_rate,
                 led_count,
                 mapping_func,
                 led_color_correction,
                 enable_sacn,
                 no_timer_reset):
        self.led_controller = led_controller
        self.refresh_rate = refresh_rate
        self.led_count = led_count
        self.mapping_func = mapping_func
        self._enable_sacn = enable_sacn
        self._no_timer_reset = no_timer_reset

        # Initialize prev state arrays
        self.reset_prev_states()

        # Map led indices to normalized position vectors
        self.mapped = [self.mapping_func(i) for i in range(self.led_count)]

        # Create lists used to cache current mapping
        # so it doesn't have to be recalculated every frame
        self.primary_mapping = []
        self.secondary_mapping = []

        # Used to render main slider/select list
        self.params = {
            'brightness': 0.15,
            'color_temp': 6500,
            'gamma': 1.0,
            'saturation': 1.0,
            'primary_pattern': 0,
            'primary_speed': 0.2,
            'primary_scale': 1.0,
            'secondary_pattern': 0,
            'secondary_speed': 0.2,
            'secondary_scale': 1.0,
            'palette': 0,
            'sacn': 0,
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
        self.reset_timer()
        self.time = 0
        self.update_needed = True # Is the LED state going to change this frame?

        # Initialize sACN / E1.31
        if enable_sacn:
            self._last_sacn_time = 0
            self._sacn_perf_avg = 0
            self._sacn_count = 0

    def _sacn_callback(self, packet):
        'Callback for sACN / E1.31 client'
        sacn_time = time.perf_counter()
        self._sacn_perf_avg += (sacn_time - self._last_sacn_time)
        self._last_sacn_time = sacn_time

        self._sacn_count += 1
        if self._sacn_count % 100 == 0:
            print('Average sACN rate (packets/s): {}'.format(1 / (self._sacn_perf_avg / 100)))
            self._sacn_perf_avg = 0

        data = [x / 255.0 for x in packet.dmxData[:self.led_count * 3]]
        self.led_controller.set_all_pixels_rgb_float(
            list(zip_longest(*(iter(data),) * 3)),
            self.correction,
            1.0,
            self.params['brightness'],
            1.0
        )

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
            'palette_mirrored': self.get_palette_color_mirrored,
            'palette_length': self.get_palette_length,
            'hsv': animpatterns.ColorMode.hsv,
            'rgb': animpatterns.ColorMode.rgb,
            'clamp': utils.clamp,
            'wave_pulse': driver.wave_pulse,
            'wave_triangle': driver.wave_triangle,
            'wave_sine': driver.wave_sine,
            'wave_cubic': driver.wave_cubic,
            'plasma_sines': driver.plasma_sines,
            'plasma_sines_octave': driver.plasma_sines_octave,
            'perlin_noise_3d': driver.perlin_noise_3d,
            'fbm_noise_3d': driver.fbm_noise_3d,
            'impulse_exp': utils.impulse_exp,
            'fract': utils.fract,
            'blackbody_to_rgb': driver.blackbody_to_rgb,
            'blackbody_correction_rgb': driver.blackbody_correction_rgb,
            'hsv_to_rgb': self.hsv_to_rgb,
        }
        restricted_locals = {}
        arg_names = ['t', 'dt', 'x', 'y', 'z', 'prev_state']

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

    def reset_timer(self):
        'Reset animation timer'
        self.start = time.perf_counter()

    def calculate_color_correction(self):
        'Calculate and store color temperature correction'
        rgb = driver.blackbody_to_rgb(self.params['color_temp'])
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
                    (self.mapped[i][1] / self.params['primary_scale']) % 1,
                    (self.mapped[i][2] / self.params['primary_scale']) % 1,
                ))
        else:
            p = [(0, 0, 0) for i in range(self.led_count)]

        if self.params['secondary_scale'] != 0:
            for i in range(self.led_count):
                s.append((
                    (self.mapped[i][0] / self.params['secondary_scale']) % 1,
                    (self.mapped[i][1] / self.params['secondary_scale']) % 1,
                    (self.mapped[i][2] / self.params['secondary_scale']) % 1
                ))
        else:
            s = [(0, 0, 0) for i in range(self.led_count)]

        self.primary_mapping = p
        self.secondary_mapping = s

    def _update_sacn_state(self):
        if self.params['sacn']:
            self._receiver = sacn.sACNreceiver()
            self._receiver.listen_on('universe', universe=1)(self._sacn_callback)
            self._receiver.start()
        else:
            self._receiver.stop()

    def _check_reset_animation_state(self):
        if not self._no_timer_reset:
            self.reset_timer()

    def set_param(self, key, value):
        'Set an animation parameter'
        self.params[key] = value
        self.update_needed = True
        if key == 'color_temp':
            self.calculate_color_correction()
        elif key == 'primary_pattern':
            self._check_reset_animation_state()
        elif key == 'primary_scale' or key == 'secondary_scale':
            self.calculate_mappings()
        elif key == 'palette':
            self.calculate_palette_table()
        elif key == 'sacn' and self._enable_sacn:
            self._update_sacn_state()

    def set_pattern_function(self, key, source):
        'Update the source code and recompile a pattern function'
        errors, warnings, pattern = self.compile_pattern(source)
        if len(errors) == 0:
            self.pattern_functions[key] = pattern
            self._check_reset_animation_state()
        elif key not in self.pattern_functions:
            self.pattern_functions[key] = animpatterns.blank
        self.update_needed = True
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
            h1 = c2[0] - c1[0]
            if abs(h1) != 1:
                if h1 < -0.5:
                    h1 += 1
                if h1 > 0.5:
                    h1 -= 1
            palette_table.append((
                f * h1 + c1[0],
                f * (c2[1] - c1[1]) + c1[1],
                f * (c2[2] - c1[2]) + c1[2],
            ))
        self.palette_table = palette_table
        self.palette_length = len(palette['colors'])
        self.update_needed = True

    def hsv_to_rgb(h, s, v):
        if s == 0.0: v*=255; return (v, v, v)
        i = int(h*6.) # XXX assume int() truncates!
        f = (h*6.)-i; p,q,t = int(255*(v*(1.-s))), int(255*(v*(1.-s*f))), int(255*(v*(1.-s*(1.-f)))); v*=255; i%=6
        if i == 0: return (v, t, p)
        if i == 1: return (q, v, p)
        if i == 2: return (p, v, t)
        if i == 3: return (p, q, v)
        if i == 4: return (t, p, v)
        if i == 5: return (v, p, q)

    def get_palette_color(self, t):
        'Get color from current palette corresponding to index between 0 and 1'
        # This gives a surprising performance improvement over doing the math in python
        # If the palette size is ever changed here, it needs to be changed in animation_utils.h
        return self.palette_table[driver.float_to_int_1000(t)]

    def get_palette_color_mirrored(self, t):
        'Version of get_palette_color that samples a mirrored version of the palette'
        return self.palette_table[driver.float_to_int_1000_mirror(t)]

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
        self.timer = IntervalTimer(1.0 / self.refresh_rate, self.update_leds)
        self.timer.start()

    def update_leds(self):
        'Determine time, render frame, and display'
        last_t = self.time
        self.time = self.timer.last_start - self.start
        delta_t = self.time - last_t

        if self.update_needed and self.params['sacn'] == 0:
            # Begin render
            pattern_1 = self.pattern_functions[self.params['primary_pattern']]
            pattern_2 = self.secondary_pattern_functions[self.params['secondary_pattern']]

            # Calculate times
            # Reset time every week to prevent strange math issues
            time_2 = self.time % 604800
            # time component = time (s) * speed (cycle/s)
            primary_time = time_2 * self.params['primary_speed']
            primary_delta_t = delta_t * self.params['primary_speed']
            secondary_time = time_2 * self.params['secondary_speed']
            secondary_delta_t = delta_t * self.params['secondary_speed']

            mode = animpatterns.ColorMode.hsv

            try:
                # Determine current pattern mode
                c, mode = pattern_1(0, 0.1, 0, 0, 0, (0, 0, 0))

                # Run primary pattern to determine initial color
                # State 1 is an array of color tuples
                s_1 = [pattern_1(primary_time,
                                 primary_delta_t,
                                 self.primary_mapping[i][0],
                                 self.primary_mapping[i][1],
                                 self.primary_mapping[i][2],
                                 self.primary_prev_state[i])[0]
                       for i in range(self.led_count)]
                self.primary_prev_state = s_1

                # If no secondary pattern is set, write colors to LEDs
                if pattern_2 is None:
                    if mode == animpatterns.ColorMode.hsv:
                        self.led_controller.set_all_pixels_hsv_float(
                            s_1,
                            self.correction,
                            self.params['saturation'],
                            self.params['brightness'],
                            self.params['gamma']
                        )
                    elif mode == animpatterns.ColorMode.rgb:
                        self.led_controller.set_all_pixels_rgb_float(
                            s_1,
                            self.correction,
                            self.params['saturation'],
                            self.params['brightness'],
                            self.params['gamma']
                        )

                 # Run secondary pattern to get new brightness and modify color
                else:
                    s_2 = [pattern_2(secondary_time,
                                     secondary_delta_t,
                                     self.secondary_mapping[i][0],
                                     self.secondary_mapping[i][1],
                                     self.secondary_mapping[i][2],
                                     self.secondary_prev_state[i],
                                     s_1[i]) for i in range(self.led_count)]
                    self.secondary_prev_state = s_2

                    # Write colors to LEDs
                    if mode == animpatterns.ColorMode.hsv:
                        self.led_controller.set_all_pixels_hsv_float(
                            [(c[0][0], c[0][1], c[0][2] * c[1]) for c in s_2],
                            self.correction,
                            self.params['saturation'],
                            self.params['brightness'],
                            self.params['gamma']
                        )
                    elif mode == animpatterns.ColorMode.rgb:
                        self.led_controller.set_all_pixels_rgb_float(
                            [(c[0][0] * c[1], c[0][1] * c[1], c[0][2] * c[1]) for c in s_2],
                            self.correction,
                            self.params['saturation'],
                            self.params['brightness'],
                            self.params['gamma']
                        )

            except Exception as e:
                msg = traceback.format_exception(type(e), e, e.__traceback__)
                print(f'Pattern execution: {msg}')
                r = 0.1 * driver.wave_pulse(time_2, 0.5)
                self.led_controller.set_all_pixels_rgb_float(
                    [(r, 0, 0) for i in range(self.led_count)],
                    self.correction,
                    1.0,
                    1.0,
                    1.0
                )

            # If displaying a static pattern with no secondary pattern, brightness is 0,
            # or speed is 0: no update is needed the next frame
            self.update_needed = not (
                ((self.params['primary_pattern'] in animpatterns.static_patterns or self.params['primary_speed'] == 0) and self.params['secondary_pattern'] == 0) or self.params['brightness'] == 0)

    def clear_leds(self):
        'Turn all LEDs off'
        self.led_controller.set_all_pixels_rgb_float(
            [(0, 0, 0) for i in range(self.led_count)],
            self.correction,
            self.params['saturation'],
            self.params['brightness'],
            self.params['gamma']
        )

    def end_animation(self):
        'Stop rendering in the animation thread and stop sACN receiver'
        self.timer.stop()
        try:
            if self._enable_sacn and self._receiver:
                self._receiver.stop()
        except:
            pass
