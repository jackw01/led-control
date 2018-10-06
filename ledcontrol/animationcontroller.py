import colorsys
from ledcontrol.ledmodes import LEDAnimationMode

class ColorHSV:
    def __init__(self, h, s, v):
        self.h = h
        self.s = s
        self.v = v

    def rgb():
        return colorsys.hsv_to_rgb(h, s, v)

class AnimationController:
    def __init__(self):
        self.params = {
            'master_brightness' : 1,
            'animation_mode' : LEDAnimationMode.SolidColor,
            'colors' : [ ColorHSV(0.0, 0.0, 255.0) ]
        }
        self.time = 0

    def set_param(self, key, value):
        self.params[key] = value
        print(self.params)

    def next_frame(self, timestep):
        pass
