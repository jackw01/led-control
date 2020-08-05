# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

import os
import json
import atexit
from recordclass import recordclass
from threading import Timer
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from ledcontrol.animationcontroller import AnimationController
from ledcontrol.ledcontroller import LEDController

import ledcontrol.pixelmappings as pixelmappings
import ledcontrol.animationpatterns as animpatterns
import ledcontrol.utils as utils

# Record class for form items
fields = [
    'control',
    'key',
    'type',
    'min',
    'max',
    'step',
    'options',
    'val',
    'label',
    'unit',
]

defaults = [
    'range',
    None,
    None,
    0,
    1,
    0.01,
    [],
    0,
    '',
    '',
]

FormItem = recordclass('FormItem', fields, defaults=defaults)

def create_app(led_count, refresh_rate,
               led_pin, led_data_rate, led_dma_channel,
               led_strip_type, led_pixel_order,
               led_color_correction, led_brightness_limit,
               save_interval):
    app = Flask(__name__)
    leds = LEDController(led_count, led_pin,
                         led_data_rate, led_dma_channel,
                         led_strip_type, led_pixel_order)
    controller = AnimationController(leds, refresh_rate, led_count,
                                     pixelmappings.line(led_count),
                                     led_color_correction)

    patterns = dict(animpatterns.default)

    # Create file if it doesn't exist already
    filename = Path('/etc') / 'ledcontrol.json'
    filename.touch(exist_ok=True)

    # Init controller params and custom patterns from settings file
    with open(str(filename), mode='r') as data_file:
        try:
            settings = json.load(data_file)
            controller.params = settings['params']
            # Enforce brightness limit
            controller.params['master_brightness'] = min(
                controller.params['master_brightness'], led_brightness_limit)
            controller.calculate_color_correction()
            controller.calculate_mappings()
            for k, v in settings['patterns'].items():
                # JSON keys are always strings
                if int(k) not in animpatterns.default:
                    patterns[int(k)] = v
                    controller.set_pattern_function(int(k), v['source'])
                else:
                    patterns[int(k)].update(v)
            controller.colors = settings['colors']
            print(f'Loaded saved settings from {filename}.')
        except Exception:
            print(f'Could not open saved settings at {filename}, ignoring.')

    # Define form and create user-facing labels based on keys
    form = [
        FormItem('range', 'master_brightness', float, 0, led_brightness_limit,
                 0.05),
        FormItem('range', 'master_color_temp', int, 1000, 12000, 10, unit='K'),
        FormItem('range', 'master_gamma', float, 0.01, 3),
        FormItem('range', 'master_saturation', float, 0, 1),
        FormItem('select', 'primary_pattern', int),
        FormItem('range', 'primary_speed', float, 0.01, 2, unit='Hz'),
        FormItem('range', 'primary_scale', float, -10, 10),
        FormItem('code', 'pattern_source', str),
        FormItem('select', 'secondary_pattern', int,
                 options=list(animpatterns.default_secondary_names.values()),
                 val=controller.params['secondary_pattern']),
        FormItem('range', 'secondary_speed', float, 0.01, 2, unit='Hz'),
        FormItem('range', 'secondary_scale', float, -10, 10),
    ]

    for item in form:
        item.label = utils.snake_to_title(item.key)

    @app.route('/')
    def index():
        'Returns web app page'
        for item in form:
            if (item.key in controller.params):
                item.val = item.type(controller.params[item.key])
        return render_template('index.html',
                               form=form,
                               params=controller.params,
                               colors=controller.colors)

    @app.route('/setparam')
    def set_param():
        'Sets a key/value pair in controller parameters'
        key = request.args.get('key', type=str)
        value = request.args.get('value')
        if key == 'primary_pattern':
            save_current_pattern_params()
            controller.set_param('primary_speed', patterns[int(value)]['primary_speed'])
            controller.set_param('primary_scale', patterns[int(value)]['primary_scale'])
        controller.set_param(key, next(filter(lambda i: i.key == key, form)).type(value))
        return jsonify(result='')

    @app.route('/getpatternparams')
    def get_pattern_params():
        'Returns pattern parameters for the given key in JSON dict form'
        key = request.args.get('key', type=int)
        return jsonify(speed=patterns[key]['primary_speed'],
                       scale=patterns[key]['primary_scale'])

    @app.route('/getpatternsources')
    def get_pattern_sources():
        'Returns pattern sources in JSON dict form'
        return jsonify(sources={k: v['source'] for k, v in patterns.items()},
                       names={k: v['name'] for k, v in patterns.items()},
                       defaults=list(animpatterns.default.keys()),
                       current=controller.params['primary_pattern'])

    @app.route('/compilepattern')
    def compile_pattern():
        'Compiles a pattern, returns errors and warnings in JSON array form'
        key = request.args.get('key', type=int)
        source = request.args.get('source', type=str)
        if key not in patterns:
            patterns[key] = {
                'name': key,
                'primary_speed': controller.params['primary_speed'],
                'primary_scale': controller.params['primary_scale']
            }
        patterns[key]['source'] = source
        errors, warnings = controller.set_pattern_function(key, source)
        return jsonify(errors=errors, warnings=warnings)

    @app.route('/deletepattern')
    def delete_pattern():
        'Deletes a pattern'
        key = request.args.get('key', type=int)
        del patterns[key]
        return jsonify(result='')

    @app.route('/setpatternname')
    def set_pattern_name():
        'Sets a pattern name for the given key'
        key = request.args.get('key', type=int)
        name = request.args.get('name', type=str)
        patterns[key]['name'] = name
        return jsonify(result='')

    @app.route('/setcolor')
    def set_color():
        'Sets a color in the palette'
        index = request.args.get('index', type=int)
        h = round(request.args.get('h', type=float), 3)
        s = round(request.args.get('s', type=float), 3)
        v = round(request.args.get('v', type=float), 3)
        controller.set_color(index, (h, s, v))
        return jsonify(result = '')

    @app.route('/setcolorcomponent')
    def set_color_component():
        'Sets a component of a color in the palette'
        index = request.args.get('index', type=int)
        component = request.args.get('component', type=int)
        value = request.args.get('value', type=float)
        controller.set_color_component(index, component, value)
        return jsonify(result = '')

    def save_current_pattern_params():
        'Remembers speed and scale for current pattern'
        patterns[controller.params['primary_pattern']]['primary_speed']\
            = controller.params['primary_speed']
        patterns[controller.params['primary_pattern']]['primary_scale']\
            = controller.params['primary_scale']

    def save_settings():
        'Save controller settings'
        save_current_pattern_params()
        patterns_save = {}
        for k,v in patterns.items():
            if k not in animpatterns.default:
                patterns_save[k] = v
            else:
                patterns_save[k] = {n: v[n] for n in ('primary_speed', 'primary_scale')}
        data = {
            'params': controller.params,
            'patterns': patterns_save,
            'colors': controller.colors,
        }
        with open(str(filename), 'w') as data_file:
            try:
                json.dump(data, data_file,
                          sort_keys=True, indent=4, separators=(',', ': '))
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
    atexit.register(leds.clear)
    atexit.register(controller.end_animation_thread)
    auto_save_settings()

    return app
