import re
from flask import Flask, render_template, request, jsonify
from ledcontrol.animationcontroller import AnimationController
from ledcontrol.ledmodes import LEDAnimationMode

def camel_case_to_title(text):
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', text)

def snake_case_to_title(text):
    return text.replace('_', ' ').title()

class FormItem:
    def __init__(self, control, key, type, label='', min=0, max=1, step=0.01, options=(), val=0, unit=''):
        self.control = control
        self.label = label if label != '' else snake_case_to_title(key)
        self.key = key
        self.type = type
        self.min = min
        self.step = step
        self.options = options
        self.val = type(val)
        self.unit = unit

def create_app():
    app = Flask(__name__)
    animation_controller = AnimationController()

    @app.route('/')
    def index():
        form = (
            FormItem('select', 'animation_mode', int,
                     options=[camel_case_to_title(e.name) for e in LEDAnimationMode]),
            FormItem('range', 'master_brightness', float, min=0, max=1, step=0.001),
            FormItem('range', 'animation_speed', float, min=0, max=100, step=10, unit='LEDs/sec')
        )

        for item in form:
            item.val = item.type(animation_controller.params[item.key])

        return render_template('index.html', form=form, params=animation_controller.params)

    @app.route('/setparam')
    def set_param():
        key = request.args.get('key', type=str)
        value = request.args.get('value')
        animation_controller.set_param(key, value)
        return jsonify(result = '')

    return app
