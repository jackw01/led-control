import colorsys
from ledcontrol.ledmodes import LEDColorAnimationMode, LEDSecondaryAnimationMode

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
            'color_animation_mode' : LEDColorAnimationMode.SolidColor,
            'color_animation_speed' : 10,
            'color_animation_scale' : 100,
            'secondary_animation_mode' : LEDColorAnimationMode.SolidColor,
            'secondary_animation_speed' : 10,
            'secondary_animation_scale' : 100,
            'red_frequency': 1.0,
            'green_frequency': 0.666,
            'blue_frequency': 0.333,
            'red_phase_offset': 0.0,
            'green_phase_offset': 0.5,
            'blue_phase_offset': 1.0,
            'colors' : [ (0.0, 0.0, 255.0) ]
        }
        self.time = 0

    def set_param(self, key, value):
        self.params[key] = value
        print(self.params)

    def next_frame(self, timestep):
        pass
