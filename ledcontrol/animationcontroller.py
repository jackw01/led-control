import colorsys
from ledcontrol.ledmodes import LEDColorAnimationMode, LEDSecondaryAnimationMode

class ColorHSV:
    def __init__(self, triplet):
        self.h = triplet[0]
        self.s = triplet[1]
        self.v = triplet[2]

    def rgb():
        return colorsys.hsv_to_rgb(h, s, v)

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class AnimationController:
    def __init__(self, points):
        self.params = {
            'master_brightness' : 1,
            'color_animation_mode' : LEDColorAnimationMode.SolidColor,
            'color_animation_speed' : 10,
            'color_animation_scale' : 100,
            'secondary_animation_mode' : LEDSecondaryAnimationMode.Static,
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
        self.points = points
        self.time = 0

    def set_param(self, key, value):
        self.params[key] = value
        print(self.params)

    def next_frame(self, timestep):
        led_states = []
        for point in self.points:
            led_states.append(ColorHSV(self.params['colors'][0]))
        self.time += timestep
        return led_states
