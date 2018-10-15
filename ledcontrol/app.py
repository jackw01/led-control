# led-control WS2812B LED Controller Server
# Copyright 2018 jackw01. Released under the MIT License (see LICENSE for details).

import json
import re
import atexit
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from ledcontrol.animationcontroller import AnimationController, Point
from ledcontrol.ledcontroller import LEDController
from ledcontrol.ledmodes import LEDColorAnimationMode, LEDSecondaryAnimationMode

def camel_case_to_title(text):
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', text)

def snake_case_to_title(text):
    return text.replace('_', ' ').title()

class FormItem:
    def __init__(self, control, key, type,
                 label='', min=0, max=1, step=0.01, options=(), val=0, unit='', e_class=''):
        self.control = control
        self.label = label if label != '' else snake_case_to_title(key)
        self.key = key
        self.type = type
        self.min = min
        self.max = max
        self.step = step
        self.options = options
        self.val = type(val)
        self.unit = unit
        self.e_class = e_class

def create_app(led_strip, refresh_rate, led_pin, led_data_rate, led_dma_channel, led_pixel_order):
    points = []
    if led_strip > 0:
        points = [Point(i, 0) for i in range(0, led_strip)]

    app = Flask(__name__)
    led_controller = LEDController(len(points), led_pin, led_data_rate, led_dma_channel, led_pixel_order)
    animation_controller = AnimationController(points, refresh_rate, led_controller)

    filename = Path.cwd() / 'ledcontrol.json'
    filename.touch(exist_ok=True)

    with open(str(filename), mode='r') as data_file:
        try:
            settings = json.load(data_file)
            animation_controller.params = settings['params']
            animation_controller.colors = settings['colors']
            print('Loaded saved settings from {}'.format(filename))
        except:
            print('Could not open saved settings at {}, ignoring.'.format(filename))

    form = (
        FormItem('range', 'master_brightness', float, min=0, max=1),
        FormItem('select', 'color_animation_mode', int,
                 options=[camel_case_to_title(e.name) for e in LEDColorAnimationMode]),
        FormItem('range', 'color_animation_speed', float, min=0.01, max=1, unit='Hz'),
        FormItem('range', 'color_animation_scale', float, min=1, max=100, step=1, unit='LEDs'),
        FormItem('select', 'secondary_animation_mode', int,
                 options=[camel_case_to_title(e.name) for e in LEDSecondaryAnimationMode]),
        FormItem('range', 'secondary_animation_speed', float, min=0.01, max=1, unit='Hz', e_class='a2'),
        FormItem('range', 'secondary_animation_scale', float, min=1, max=100, step=1, unit='LEDs', e_class='a2'),
        FormItem('range', 'saturation', float, min=0, max=1, e_class='saturation'),
        FormItem('range', 'red_frequency', float, min=0, max=1, e_class='sine'),
        FormItem('range', 'green_frequency', float, min=0, max=1, e_class='sine'),
        FormItem('range', 'blue_frequency', float, min=0, max=1, e_class='sine'),
        FormItem('range', 'red_phase_offset', float, min=0, max=1, e_class='sine'),
        FormItem('range', 'green_phase_offset', float, min=0, max=1, e_class='sine'),
        FormItem('range', 'blue_phase_offset', float, min=0, max=1, e_class='sine'),
    )

    @app.route('/')
    def index():
        for item in form:
            item.val = item.type(animation_controller.params[item.key])
        return render_template('index.html', form=form,
                                             params=animation_controller.params,
                                             colors=animation_controller.colors)

    @app.route('/setparam')
    def set_param():
        key = request.args.get('key', type=str)
        value = request.args.get('value')
        animation_controller.set_param(key, next(filter(lambda i: i.key == key, form)).type(value))
        return jsonify(result = '')

    @app.route('/setcolor')
    def set_color():
        index = request.args.get('index', type=int)
        component = request.args.get('component', type=int)
        value = request.args.get('value', type=float)
        animation_controller.set_color(index, component, value)
        return jsonify(result = '')

    def save_settings():
        data = { 'params': animation_controller.params, 'colors': animation_controller.colors }
        with open(str(filename), 'w') as data_file:
            try:
                json.dump(data, data_file, sort_keys=True, indent=4, separators=(',', ': '))
                print('Saved settings to {}'.format(filename))
            except:
                print('Could not save settings to {}'.format(filename))

    animation_controller.begin_animation_thread()
    atexit.register(save_settings)
    atexit.register(animation_controller.end_animation_thread)

    return app
