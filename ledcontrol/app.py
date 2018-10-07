import re
from flask import Flask, render_template, request, jsonify
from ledcontrol.animationcontroller import AnimationController, Point
from ledcontrol.ledmodes import LEDColorAnimationMode, LEDSecondaryAnimationMode

def camel_case_to_title(text):
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', text)

def snake_case_to_title(text):
    return text.replace('_', ' ').title()

class FormItem:
    def __init__(self, control, key, type,
                 label='', min=0, max=1, step=0.1, options=(), val=0, unit='', e_class=''):
        self.control = control
        self.label = label if label != '' else snake_case_to_title(key)
        self.key = key
        self.type = type
        self.min = min
        self.step = step
        self.options = options
        self.val = type(val)
        self.unit = unit
        self.e_class = e_class

def create_app():
    points = []
    for i in range(0, 150):
        points.append(Point(i, 0))

    app = Flask(__name__)
    animation_controller = AnimationController(points)

    @app.route('/')
    def index():
        form = (
            FormItem('range', 'master_brightness', float, min=0, max=1, step=0.001),
            FormItem('select', 'color_animation_mode', int,
                     options=[camel_case_to_title(e.name) for e in LEDColorAnimationMode]),
            FormItem('range', 'color_animation_speed', float, min=0, max=100, step=1, unit=''),
            FormItem('range', 'color_animation_scale', float, min=0, max=100, step=1, unit='LEDs'),
            FormItem('select', 'secondary_animation_mode', int,
                     options=[camel_case_to_title(e.name) for e in LEDSecondaryAnimationMode]),
            FormItem('range', 'secondary_animation_speed', float, max=100, step=1, e_class='secondary'),
            FormItem('range', 'secondary_animation_scale', float, max=100, step=1, unit='LEDs', e_class='secondary'),
            FormItem('range', 'red_frequency', float, min=0, max=1, step=0.01, e_class='sine'),
            FormItem('range', 'green_frequency', float, min=0, max=1, step=0.01, e_class='sine'),
            FormItem('range', 'blue_frequency', float, min=0, max=1, step=0.01, e_class='sine'),
            FormItem('range', 'red_phase_offset', float, min=0, max=1, step=0.01, e_class='sine'),
            FormItem('range', 'green_phase_offset', float, min=0, max=1, step=0.01, e_class='sine'),
            FormItem('range', 'blue_phase_offset', float, min=0, max=1, step=0.01, e_class='sine'),
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
