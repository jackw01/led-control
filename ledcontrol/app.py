import re
from flask import Flask, render_template, request, jsonify
from ledcontrol.animationcontroller import AnimationController
from ledcontrol.ledmodes import LEDAnimationMode

def add_spaces(text):
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', text)

def create_app():
    app = Flask(__name__)
    animation_controller = AnimationController()

    @app.route('/')
    def index():
        return render_template('index.html',
        animation_mode = int(animation_controller.params['animation_mode']),
        animation_modes = [add_spaces(e.name) for e in LEDAnimationMode])

    @app.route('/setparam')
    def set_param():
        key = request.args.get('key', type=str)
        value = request.args.get('value')
        animation_controller.set_param(key, value)
        return jsonify(result = '')

    return app
