# led-control WS2812B LED Controller Server
# Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

import json
import atexit
import shutil
import traceback
from threading import Timer
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from ledcontrol.animationcontroller import AnimationController
from ledcontrol.ledcontroller import LEDController

import ledcontrol.pixelmappings as pixelmappings
import ledcontrol.animationfunctions as animfunctions
import ledcontrol.colorpalettes as colorpalettes
import ledcontrol.utils as utils

def create_app(led_count,
               pixel_mapping,
               refresh_rate,
               led_pin,
               led_data_rate,
               led_dma_channel,
               led_pixel_order,
               led_brightness_limit,
               save_interval,
               enable_sacn,
               no_timer_reset):
    app = Flask(__name__)

    # Create pixel mapping function
    if pixel_mapping is not None:
        print(f'Using pixel mapping from file ({len(pixel_mapping)} LEDs)')
        led_count = len(pixel_mapping)
        mapping_func = pixelmappings.from_array(pixel_mapping)
    else:
        print(f'Using default linear pixel mapping ({led_count} LEDs)')
        mapping_func = pixelmappings.line(led_count)

    leds = LEDController(led_count,
                         led_pin,
                         led_data_rate,
                         led_dma_channel,
                         led_pixel_order)
    controller = AnimationController(leds,
                                     refresh_rate,
                                     led_count,
                                     mapping_func,
                                     enable_sacn,
                                     no_timer_reset,
                                     led_brightness_limit)

    functions = dict(animfunctions.default)

    # Create file if it doesn't exist already
    filename = Path('/etc') / 'ledcontrol.json'
    filename.touch(exist_ok=True)

    # Init controller params and custom animations from settings file
    with open(str(filename), mode='r') as data_file:
        try:
            settings_str = data_file.read()
            # Apply updates to old versions of settings file
            settings_str = settings_str.replace('master_', '')
            settings_str = settings_str.replace('pattern(t, dt, x, y, prev_state)',
                                                'pattern(t, dt, x, y, z, prev_state)')
            settings = json.loads(settings_str)

            if 'save_version' not in settings:
                print(f'Detected an old save file version at {filename}. Making a backup to {filename}.bak.')
                shutil.copyfile(filename, filename.with_suffix('.json.bak'))

                # Rename 'params' and recreate as 'settings'
                params = settings.pop('params')
                settings['settings'] = {
                    'global_brightness': params['brightness'],
                    'global_color_temp': params['color_temp'],
                    'global_color_r': 1.0,
                    'global_color_g': 1.0,
                    'global_color_b': 1.0,
                    'global_saturation': params['saturation'],
                    'groups': {
                        'main': {
                            'range_start': 0,
                            'range_end': 100000,
                            'mapping': [],
                            'brightness': 1.0,
                            'color_temp': 6500,
                            'saturation': 1.0,
                            'function': params['primary_pattern'],
                            'speed': params['primary_speed'],
                            'scale': params['primary_scale'],
                            'palette': params['palette'],
                        }
                    }
                }

                # Add default flag to animation patterns
                for k in settings['patterns']:
                    if 'source' in settings['patterns'][k]:
                        settings['patterns'][k]['default'] = False
                    else:
                        settings['patterns'][k]['default'] = True

                # Rename 'patterns'
                settings['functions'] = settings.pop('patterns')

                # Add default flag to palettes
                for k in settings['palettes']:
                    settings['palettes'][k]['default'] = False

                print('Successfully upgraded save file.')

            # Enforce sACN off when starting up
            settings['settings']['sacn'] = 0

            # Set controller settings, (automatically) recalculate things that depend on them
            controller.update_settings(settings['settings'])

            # Read custom animations and changed params for default animations
            for k, v in settings['functions'].items():
                if v['default'] == False:
                    functions[int(k)] = v
                    controller.set_pattern_function(int(k), v['source'])
                else:
                    functions[int(k)].update(v)

            # Read color palettes
            for k, v in settings['palettes'].items():
                controller.set_palette(int(k), v)
            controller.calculate_palette_tables()

            print(f'Loaded saved settings from {filename}.')

        except Exception as e:
            traceback.print_exc()
            print(f'Some saved settings at {filename} are out of date or invalid. Making a backup of the old file to {filename}.error and creating a new one with default settings.')
            shutil.copyfile(filename, filename.with_suffix('.json.error'))

    # todo: presets

    @app.route('/')
    def index():
        'Returns web app page'
        return app.send_static_file('index.html')

    @app.route('/getsettings')
    def get_settings():
        'Get settings'
        return jsonify(controller.get_settings())

    @app.route('/updatesettings', methods=['POST'])
    def update_settings():
        'Update settings'
        print(request.json)
        new_settings = request.json
        controller.update_settings(new_settings)
        return jsonify(result='')

    @app.route('/getfunctions')
    def get_functions():
        'Get functions'
        return jsonify(functions)

    @app.route('/compilefunction', methods=['POST'])
    def compile_function():
        'Compiles a function, returns errors and warnings in JSON array form'
        print(request.json)
        key = request.json['key']
        errors, warnings = controller.set_pattern_function(key, functions[key]['source'])
        return jsonify(errors=errors, warnings=warnings)

    @app.route('/updatefunction', methods=['POST'])
    def update_function():
        'Update a function'
        print(request.json)
        functions[request.json['key']] = request.json['value']
        return jsonify(result='')

    @app.route('/removefunction', methods=['POST'])
    def remove_function():
        'Remove a function'
        print(request.json)
        del functions[request.json['key']]
        return jsonify(result='')

    @app.route('/getpalettes')
    def get_palettes():
        'Get palettes'
        return jsonify(controller.get_palettes())

    @app.route('/updatepalette', methods=['POST'])
    def update_palette():
        'Update a palette'
        print(request.json)
        controller.set_palette(request.json['key'], request.json['value'])
        controller.calculate_palette_table(request.json['key'])
        return jsonify(result='')

    @app.route('/removefunction', methods=['POST'])
    def remove_palette():
        'Remove a palette'
        print(request.json)
        controller.delete_palette(key)
        return jsonify(result='')

    @app.route('/getfps')
    def get_fps():
        'Returns latest animation frames per second'
        return jsonify(fps=controller.get_frame_rate())

    @app.route('/resettimer')
    def reset_timer():
        'Resets animation timer'
        controller.reset_timer()
        return jsonify(result='')

    def save_settings():
        'Save controller settings, patterns, and palettes'
        functions_2 = {}
        for k, v in functions.items():
            if not v['default']:
                functions_2[k] = v
            else:
                functions_2[k] = {n: v[n] for n in ('default', 'primary_speed', 'primary_scale')}

        palettes_2 = {k: v for (k, v) in controller.get_palettes().items() if not v['default']}

        data = {
            'save_version': 2,
            'settings': controller.get_settings(),
            'functions': functions_2,
            'palettes': palettes_2,
        }
        with open(str(filename), 'w') as data_file:
            try:
                json.dump(data, data_file, sort_keys=True, indent=4)
                print(f'Saved settings to {filename}.')
            except Exception:
                print(f'Could not save settings to {filename}.')

    def auto_save_settings():
        'Timer for automatically saving settings'
        save_settings()
        t = Timer(save_interval, auto_save_settings)
        t.daemon = True
        t.start()

    controller.begin_animation_thread()
    atexit.register(save_settings)
    #atexit.register(controller.clear_leds)
    atexit.register(controller.end_animation)
    auto_save_settings()

    return app
