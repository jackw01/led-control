# led-control WS2812B LED Controller Server
# Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

import math
import random
import time
import traceback
import RestrictedPython
import sacn
import collections
from itertools import zip_longest
from ledcontrol.intervaltimer import IntervalTimer

import ledcontrol.ledcontroller as ledcontroller
import ledcontrol.animationfunctions as animfunctions
import ledcontrol.colorpalettes as colorpalettes
import ledcontrol.driver as driver
import ledcontrol.utils as utils

class AnimationController:
    def __init__(self,
                 led_controller,
                 refresh_rate,
                 led_count,
                 mapping_func,
                 enable_sacn,
                 no_timer_reset,
                 global_brightness_limit):
        self._led_controller = led_controller
        self._refresh_rate = refresh_rate
        self._led_count = led_count
        self._mapping_func = mapping_func
        self._enable_sacn = enable_sacn
        self._no_timer_reset = no_timer_reset
        self._global_brightness_limit = global_brightness_limit

        # Initialize prev state array
        self._prev_state = [(0, 0, 0) for i in range(self._led_count)]

        # Map led indices to normalized position vectors
        self._mapped = [self._mapping_func(i) for i in range(self._led_count)]

        # Create dictionary of lists used to cache current mappings
        self._mappings = {}

        # All user-editable animation settings stored here
        self._settings = {
            'on': 1,
            'global_brightness': 0.15,
            'global_brightness_limit': global_brightness_limit,
            'global_color_temp': 6500,
            'global_color_r': 255,
            'global_color_g': 190,
            'global_color_b': 170,
            'global_saturation': 1.0,
            'sacn': 0,
            'calibration': 0,
            'groups': {
                'main': {
                    'range_start': 0,
                    'range_end': 100000,
                    'render_mode': 'local',
                    'render_target': '',
                    'name': 'main',
                    'mapping': [],
                    'brightness': 1.0,
                    'color_temp': 6500,
                    'saturation': 1.0,
                    'function': 0,
                    'speed': 0.2,
                    'scale': 1.0,
                    'palette': 0,
                }
            }
        }

        # Dictionary for pattern functions
        self._functions = {}

        # Initialize default pattern functions
        for k, v in animfunctions.default.items():
            self.set_pattern_function(k, v['source'])

        # Color palette used for animations
        self._palette_table_size = 1000
        self._palettes = dict(colorpalettes.default)
        self._palette_tables = {}
        self._current_palette_table = []
        self.calculate_palette_tables()

        # Set default color temp
        self.calculate_color_correction()

        # Set default mapping
        self.calculate_mapping()

        # Prepare to start
        self.reset_timer()
        self._time = 0
        self._update_needed = True # Is the LED state going to change this frame?

        # Initialize sACN / E1.31
        if enable_sacn:
            self._sacn_buffer = [(0, 0, 0) for i in range(self._led_count)]
            self._last_sacn_time = 0
            self._sacn_perf_avg = 0
            self._sacn_count = 0

    # Computing cached values

    def calculate_palette_table(self, key):
        'Calculate and store the palette lookup table for one palette'
        palette = self._palettes[key]
        palette_table = []
        sector_size = 1.0 / (len(palette['colors']) - 1)
        for i in range(self._palette_table_size):
            f = i / self._palette_table_size
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
        self._palette_tables[key] = palette_table
        self._update_needed = True

    def calculate_palette_tables(self):
        'Calculate and store the palette lookup tables for all palettes'
        for key in self._palettes:
            self.calculate_palette_table(key)

    def calculate_color_correction(self):
        'Calculate and store color temperature correction'
        rgb = driver.blackbody_to_rgb(self._settings['global_color_temp'])
        c = [self._settings['global_color_r'] * int(rgb[0] * 255) // 255,
             self._settings['global_color_g'] * int(rgb[1] * 255) // 255,
             self._settings['global_color_b'] * int(rgb[2] * 255) // 255]
        self._correction = (c[0] << 16) | (c[1] << 8) | c[2]

    def calculate_mapping(self):
        'Calculate and store spatial mapping values with current scale'
        for group in self._settings['groups']:
            scale = self._settings['groups'][group]['scale']
            if scale != 0:
                # Calculate scale components to determine animation position
                # scale component = position / scale (pattern length in units)
                # One cycle is a normalized input value's transition from 0 to 1
                self._mappings[group] = [(
                    (self._mapped[i][0] / scale) % 1,
                    (self._mapped[i][1] / scale) % 1,
                    (self._mapped[i][2] / scale) % 1
                ) for i in range(self._led_count)]

            else:
                self._mappings[group] = [(0, 0, 0) for i in range(self._led_count)]

    # Settings frontend

    def get_settings(self):
        'Get settings dict'
        return self._settings

    def update_settings(self, new_settings):
        'Update settings dict with new values'
        self._flag_correction = False
        self._flag_mapping = False
        self._flag_clear = False
        def recursive_update(d1, d2):
            for k, v in d2.items():
                if isinstance(v, collections.abc.Mapping):
                    d1[k] = recursive_update(d1.get(k, {}), v)
                else:
                    d1[k] = v

                # Perform checks for things that need to be recalculated
                if k in ['global_color_temp', 'global_color_r', 'global_color_g', 'global_color_b', 'color_temp']:
                    self._flag_correction = True
                elif k == 'global_brightness':
                    if d1[k] != 0:
                        self._settings['on'] = 1 # force homekit 'on' when brightness is changed
                    d1[k] = min(d1[k], self._global_brightness_limit)
                elif k == 'scale':
                    self._flag_mapping = True
                elif k == 'function':
                    if v not in self._functions: # for uncompiled functions
                        self._functions[v] = animfunctions.blank
                    self._check_reset_animation_state()
                elif k in ['range_start', 'range_end']:
                    self._flag_clear = True # clear LEDs to make range selection less ambiguous
                elif k in ['render_mode', 'render_target']:
                    self._flag_clear = True
                elif k == 'sacn' and self._enable_sacn:
                    if v:
                        self._receiver = sacn.sACNreceiver()
                        self._receiver.listen_on('universe', universe=1)(self._sacn_callback)
                        self._receiver.start()
                    elif hasattr(self, '_receiver'):
                        self._receiver.stop()

            return d1

        recursive_update(self._settings, new_settings)
        if self._flag_correction:
            self.calculate_color_correction()
        if self._flag_mapping:
            self.calculate_mapping()
        if self._flag_clear:
            self.clear_leds()
        self._update_needed = True

    def delete_group(self, key):
        'Delete a group'
        if key != 'main':
            del self._settings['groups'][key]

    # Functions frontend

    def set_pattern_function(self, key, source):
        'Update and recompile a pattern function'
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
            'palette': self._get_palette_color,
            'palette_mirrored': self._get_palette_color_mirrored,
            'hsv': animfunctions.ColorMode.hsv,
            'rgb': animfunctions.ColorMode.rgb,
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
        }
        restricted_locals = {}
        arg_names = ['t', 'dt', 'x', 'y', 'z', 'prev_state']

        result = RestrictedPython.compile_restricted_exec(source)
        warnings = list(result.warnings)
        for name in result.used_names:
            if name not in restricted_globals and name not in arg_names:
                warnings.append(f'NameError: name \'{name}\' is not defined')

        if result.code:
            exec(result.code, restricted_globals, restricted_locals)

        if len(result.errors) == 0 and 'pattern' in restricted_locals:
            self._functions[key] = restricted_locals['pattern']
            self._check_reset_animation_state()

        self._update_needed = True
        return result.errors, warnings

    # Palettes frontend

    def get_palettes(self):
        'Get palettes dict'
        return self._palettes

    def set_palette(self, key, value):
        'Update palette'
        self._palettes[key] = value

    def delete_palette(self, key):
        'Delete palette'
        del self._palettes[key]

    # Palettes backend

    def _get_palette_color(self, t):
        'Get color from current palette corresponding to index between 0 and 1'
        # This gives a surprising performance improvement over doing the math in python
        # If the palette size is ever changed here, it needs to be changed in animation_utils.h
        return self._current_palette_table[driver.float_to_int_1000(t)]

    def _get_palette_color_mirrored(self, t):
        'Version of get_palette_color that samples a mirrored version of the palette'
        return self._current_palette_table[driver.float_to_int_1000_mirror(t)]

    # Animation and timer

    def begin_animation_thread(self):
        'Start animating'
        self._timer = IntervalTimer(1.0 / self._refresh_rate, self.update_leds)
        self._timer.start()

    def get_frame_rate(self):
        'Get frame rate'
        return self._timer.get_rate()

    def _check_reset_animation_state(self):
        'Reset animation timer if allowed by configuration flag'
        if not self._no_timer_reset:
            self.reset_timer()

    def reset_timer(self):
        'Reset animation timer'
        self._start = time.perf_counter()

    def update_leds(self):
        'Determine time, render frame, and display'
        last_t = self._time
        self._time = self._timer.last_start - self._start
        delta_t = self._time - last_t

        if self._timer.get_count() % 100 == 0:
            print(f'Execution time: {self._timer.get_perf_avg():0.5f}s, {self._timer.get_rate():05.1f} FPS')

        if self._settings['calibration'] == 1:
            for group, settings in list(self._settings['groups'].items()):
                range_start = settings['range_start']
                range_end = min(self._led_count, settings['range_end'])
                self._led_controller.show_calibration_color(
                    range_end - range_start,
                    self._correction,
                    self._settings['global_brightness'] / 2,
                    settings['render_mode'],
                    settings['render_target']
                )

            return

        if self._update_needed:
            self._update_needed = False
            # Store dict keys as list in case they are changed during iteration
            for group, settings in list(self._settings['groups'].items()):
                try:
                    mapping = self._mappings[group]
                    range_start = settings['range_start']
                    range_end = min(self._led_count, settings['range_end'])

                    # Begin render
                    self._current_palette_table = self._palette_tables[settings['palette']]
                    computed_brightness = self._settings['on'] * self._settings['global_brightness'] * settings['brightness']
                    computed_saturation = self._settings['global_saturation'] * settings['saturation']
                    function_1 = self._functions[settings['function']]

                    # Calculate times
                    # Reset time every week to prevent strange math issues
                    time_fix = self._time % 604800
                    # time component = time (s) * speed (cycle/s)
                    time_1 = time_fix * settings['speed']
                    delta_t_1 = delta_t * settings['speed']

                except KeyError as e: # Ignore if settings haven't been calculated yet
                    continue

                try:
                    if self._settings['sacn'] == 0:
                        # Determine current pattern mode
                        c, mode = function_1(0, 0.1, 0, 0, 0, (0, 0, 0))

                        # Run pattern to determine color
                        state = [function_1(time_1,
                                            delta_t_1,
                                            mapping[i][0],
                                            mapping[i][1],
                                            mapping[i][2],
                                            self._prev_state[i])[0]
                                for i in range(range_start, range_end)]
                        self._prev_state[range_start:range_end] = state

                        self._led_controller.set_range(
                            state,
                            range_start,
                            range_end,
                            self._correction,
                            computed_saturation,
                            computed_brightness,
                            mode,
                            settings['render_mode'],
                            settings['render_target']
                        )

                    else:
                        self._led_controller.set_range(
                            [self._sacn_buffer[i] for i in range(range_start, range_end)],
                            range_start,
                            range_end,
                            self._correction,
                            1.0,
                            self._settings['global_brightness'],
                            animfunctions.ColorMode.rgb,
                            settings['render_mode'],
                            settings['render_target']
                        )

                except Exception as e:
                    msg = traceback.format_exception(type(e), e, e.__traceback__)
                    print(f'Error during animation execution: {msg}')
                    r = 0.1 * driver.wave_pulse(time_fix, 0.5)
                    self._led_controller.set_range(
                        [(r, 0, 0) for i in range(range_end - range_start)],
                        range_start,
                        range_end,
                        self._correction,
                        1.0,
                        1.0,
                        animfunctions.ColorMode.rgb,
                        settings['render_mode'],
                        settings['render_target']
                    )
                    self._led_controller.render()
                    return

                # If displaying a static pattern, brightness is 0, or speed is 0:
                # no update is needed the next frame
                if (not self._update_needed
                    and settings['function'] not in animfunctions.static_function_ids
                    and settings['speed'] != 0
                    and computed_brightness > 0):
                    self._update_needed = True

            self._led_controller.render()

    def _sacn_callback(self, packet):
        'Callback for sACN / E1.31 client'
        sacn_time = time.perf_counter()
        self._sacn_perf_avg += (sacn_time - self._last_sacn_time)
        self._last_sacn_time = sacn_time

        self._sacn_count += 1
        if self._sacn_count % 100 == 0:
            print('Average sACN rate (packets/s): {}'.format(1 / (self._sacn_perf_avg / 100)))
            self._sacn_perf_avg = 0

        data = [x / 255.0 for x in packet.dmxData[:self._led_count * 3]]
        self._sacn_buffer = list(zip_longest(*(iter(data),) * 3))

    def clear_leds(self):
        'Turn all LEDs off'
        for group, settings in list(self._settings['groups'].items()):
            self._led_controller.set_range(
                [(0, 0, 0) for i in range(self._led_count)],
                0,
                self._led_count,
                self._correction,
                1.0,
                1.0,
                animfunctions.ColorMode.rgb,
                settings['render_mode'],
                settings['render_target']
            )
        self._led_controller.render()

    def end_animation(self):
        'Stop rendering in the animation thread and stop sACN receiver'
        self._timer.stop()
        try:
            if self._enable_sacn and self._receiver:
                self._receiver.stop()
        except:
            pass


