# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

import json
import re
import atexit
from recordclass import recordclass
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from ledcontrol.animationcontroller import AnimationController
from ledcontrol.ledcontroller import LEDController

import ledcontrol.pixelmappings as pixelmappings

def camel_to_title(text):
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', text)

def snake_case_to_title(text):
    return text.replace('_', ' ').title()

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
               led_color_correction):
    app = Flask(__name__)
    leds = LEDController(led_count, led_pin,
                         led_data_rate, led_dma_channel, led_strip_type, led_pixel_order)
    controller = AnimationController(leds, refresh_rate, led_count,
                                     pixelmappings.line(led_count), led_color_correction)

    # Create file if it doesn't exist already
    filename = Path.cwd() / 'ledcontrol.json'
    filename.touch(exist_ok=True)

    # Init controller params and custom patterns from settings file
    with open(str(filename), mode='r') as data_file:
        try:
            settings = json.load(data_file)
            controller.params = settings['params']
            for k, v in settings['patterns'].items():
                controller.set_pattern_function(k, v)
            #controller.colors = settings['colors']
            print('Loaded saved settings from {}'.format(filename))
        except Exception:
            print('Could not open saved settings at {}, ignoring.'.format(filename))

    # Define form and create user-facing labels based on keys
    form = [
        FormItem('range', 'master_brightness', float, 0, 1),
        FormItem('range', 'master_color_temp', float, 1000, 12000, 10, unit='K'),
        FormItem('range', 'master_saturation', float, 0, 1),
        FormItem('select', 'primary_pattern', str,
                 options=[snake_case_to_title(e) for e in controller.pattern_sources]),
        FormItem('range', 'primary_speed', float, 0.01, 2, unit='Hz'),
        FormItem('range', 'primary_scale', float, -10, 10),
        FormItem('code', 'pattern_source', str),
        FormItem('range', 'secondary_speed', float, 0.01, 2, unit='Hz'),
        FormItem('range', 'secondary_scale', float, -10, 10),
    ]

    for item in form:
        item.label = snake_case_to_title(item.key)

    @app.route('/')
    def index():
        """
        Returns web app page.
        """
        for item in form:
            if (item.key in controller.params):
                item.val = item.type(controller.params[item.key])
        return render_template('index.html',
                               form=form,
                               params=controller.params)

    @app.route('/setparam')
    def set_param():
        """
        Set a key/value pair in controller parameters.
        """
        key = request.args.get('key', type=str)
        value = request.args.get('value')
        controller.set_param(key, next(filter(lambda i: i.key == key, form)).type(value))
        return jsonify(result='')

    @app.route('/getpatternsources')
    def get_pattern_sources():
        """
        Returns pattern sources in JSON dict form.
        """
        return jsonify(sources=controller.pattern_sources)

    @app.route('/compilepattern')
    def compile_pattern():
        """
        Compiles a pattern, returns errors and warnings in JSON array form.
        """
        key = request.args.get('key', type=str)
        source = request.args.get('source', type=str)
        errors, warnings = controller.set_pattern_function(key, source)
        return jsonify(errors=errors, warnings=warnings)

    """
    @app.route('/setcolor')
    def set_color():
        index = request.args.get('index', type=int)
        component = request.args.get('component', type=int)
        value = request.args.get('value', type=float)
        controller.set_color(index, component, value)
        return jsonify(result = '')
    """

    def save_settings():
        """
        Save controller settings on shutdown.
        """
        data = {'params': controller.params, 'patterns': controller.get_edited_patterns() }
        with open(str(filename), 'w') as data_file:
            try:
                json.dump(data, data_file, sort_keys=True, indent=4, separators=(',', ': '))
                print('Saved settings to {}'.format(filename))
            except Exception:
                print('Could not save settings to {}'.format(filename))

    controller.begin_animation_thread()
    atexit.register(save_settings)
    atexit.register(leds.clear)
    atexit.register(controller.end_animation_thread)

    return app
