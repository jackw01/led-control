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
from ledcontrol.homekit import homekit_start

import ledcontrol.pixelmappings as pixelmappings
import ledcontrol.animationfunctions as animfunctions
import ledcontrol.colorpalettes as colorpalettes
import ledcontrol.utils as utils

def create_app(led_count,
               config_file,
               pixel_mapping_file,
               refresh_rate,
               led_pin,
               led_data_rate,
               led_dma_channel,
               led_pixel_order,
               led_brightness_limit,
               save_interval,
               enable_sacn,
               enable_hap,
               no_timer_reset,
               dev):
    app = Flask(__name__)

    # Create pixel mapping function
    if pixel_mapping_file is not None:
        pixel_mapping = json.load(pixel_mapping_file)
        pixel_mapping_file.close()
        led_count = len(pixel_mapping)
        print(f'Using pixel mapping from file ({led_count} LEDs)')
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

    presets = {}
    functions = dict(animfunctions.default)

    # Create file if it doesn't exist already
    if config_file is not None:
        filename = Path(config_file)
    else:
        filename = Path('/etc') / 'ledcontrol.json'
    filename.touch(exist_ok=True)

    # Init controller params and custom animations from settings file
    with filename.open('r') as data_file:
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
                            'render_mode': 'local',
                            'render_target': '',
                            'mapping': [],
                            'name': 'main',
                            'brightness': 1.0,
                            'color_temp': 6500,
                            'saturation': 1.0,
                            'function': 0,
                            'speed': params['primary_speed'],
                            'scale': params['primary_scale'],
                            'palette': 0,
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

            # Enforce calibration off when starting up
            settings['settings']['calibration'] = 0

            # Set controller settings, (automatically) recalculate things that depend on them
            controller.update_settings(settings['settings'])

            # Read presets
            if 'presets' in settings:
                presets.update(settings['presets'])

            # Read custom animations and changed params for default animations
            for k, v in settings['functions'].items():
                if v['default'] == False:
                    functions[int(k)] = v
                    controller.set_pattern_function(int(k), v['source'])
                elif int(k) in functions:
                    functions[int(k)].update(v)

            # Read color palettes
            for k, v in settings['palettes'].items():
                controller.set_palette(int(k), v)
            controller.calculate_palette_tables()

            print(f'Loaded saved settings from {filename}')

        except Exception as e:
            if settings_str == '':
                print(f'Creating new settings file at {filename}.')
            else:
                print(f'Some saved settings at {filename} are out of date or invalid. Making a backup of the old file to {filename}.error and creating a new one with default settings.')
                shutil.copyfile(filename, filename.with_suffix('.json.error'))

    @app.before_request
    def before_request():
        'Log post request json for testing'
        if dev and request.method == 'POST':
            print(request.endpoint)
            print(request.json)

    @app.route('/')
    def index():
        'Returns web app page'
        return app.send_static_file('index.html')

    @app.get('/getsettings')
    def get_settings():
        'Get settings'
        return jsonify(controller.get_settings())

    @app.post('/updatesettings')
    def update_settings():
        'Update settings'
        new_settings = request.json
        controller.update_settings(new_settings)
        return jsonify(result='')

    @app.get('/getpresets')
    def get_presets():
        'Get presets'
        return jsonify(presets)

    @app.post('/updatepreset')
    def update_preset():
        'Update a preset'
        presets[request.json['key']] = request.json['value']
        return jsonify(result='')

    @app.post('/removepreset')
    def remove_preset():
        'Remove a preset'
        del presets[request.json['key']]
        return jsonify(result='')

    @app.post('/removegroup')
    def remove_group():
        'Remove a group'
        controller.delete_group(request.json['key'])
        return jsonify(result='')

    @app.get('/getfunctions')
    def get_functions():
        'Get functions'
        return jsonify(functions)

    @app.post('/compilefunction')
    def compile_function():
        'Compiles a function, returns errors and warnings in JSON array form'
        key = request.json['key']
        errors, warnings = controller.set_pattern_function(key, functions[key]['source'])
        return jsonify(errors=errors, warnings=warnings)

    @app.post('/updatefunction')
    def update_function():
        'Update a function'
        functions[request.json['key']] = request.json['value']
        return jsonify(result='')

    @app.post('/removefunction')
    def remove_function():
        'Remove a function'
        del functions[request.json['key']]
        return jsonify(result='')

    @app.get('/getpalettes')
    def get_palettes():
        'Get palettes'
        return jsonify(controller.get_palettes())

    @app.post('/updatepalette')
    def update_palette():
        'Update a palette'
        controller.set_palette(request.json['key'], request.json['value'])
        controller.calculate_palette_table(request.json['key'])
        return jsonify(result='')

    @app.post('/removepalette')
    def remove_palette():
        'Remove a palette'
        controller.delete_palette(request.json['key'])
        return jsonify(result='')

    @app.get('/getfps')
    def get_fps():
        'Returns latest animation frames per second'
        return jsonify(fps=controller.get_frame_rate())

    @app.get('/resettimer')
    def reset_timer():
        'Resets animation timer'
        controller.reset_timer()
        return jsonify(result='')

    def save_settings():
        'Save controller settings, patterns, and palettes'
        functions_2 = {}
        for k, v in functions.items():
            if not v['default']:
                functions_2[str(k)] = v
            else:
                functions_2[str(k)] = {n: v[n] for n in ('default', 'primary_speed', 'primary_scale')}

        palettes_2 = {str(k): v for (k, v) in controller.get_palettes().items() if not v['default']}

        data = {
            'save_version': 2,
            'settings': controller.get_settings(),
            'presets': presets,
            'functions': functions_2,
            'palettes': palettes_2,
        }
        with filename.open('w') as data_file:
            try:
                json.dump(data, data_file, sort_keys=True, indent=4)
                print(f'Saved settings to {filename}')
            except Exception as e:
                traceback.print_exc()
                print(f'Could not save settings to {filename}')

    def auto_save_settings():
        'Timer for automatically saving settings'
        save_settings()
        t = Timer(save_interval, auto_save_settings)
        t.daemon = True
        t.start()

    controller.begin_animation_thread()
    atexit.register(save_settings)
    atexit.register(controller.clear_leds)
    atexit.register(controller.end_animation)
    auto_save_settings()

    if enable_hap:
        def setter_callback(char_values):
            new_settings = {}
            if 'On' in char_values:
                new_settings['on'] = char_values['On']
            if 'Brightness' in char_values:
                new_settings['global_brightness'] = char_values['Brightness'] / 100.0
            if 'Saturation' in char_values:
                new_settings['global_saturation'] = char_values['Saturation'] / 100.0
            controller.update_settings(new_settings)

        hap_accessory = homekit_start(setter_callback)
        hap_accessory.on.set_value(controller.get_settings()['on'])
        hap_accessory.brightness.set_value(controller.get_settings()['global_brightness'] * 100.0)
        hap_accessory.saturation.set_value(controller.get_settings()['global_saturation'] * 100.0)

    return app
