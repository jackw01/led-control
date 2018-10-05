import re
from flask import Flask, render_template
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
                               animation_mode = LEDAnimationMode.SolidColor,
                               animation_modes = [add_spaces(e.name) for e in LEDAnimationMode])

    return app
