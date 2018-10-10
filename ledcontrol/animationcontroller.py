import math
import time
import colorsys
from threading import Event, Thread
from ledcontrol.ledmodes import LEDColorAnimationMode, LEDSecondaryAnimationMode

def hsv_to_rgb(triplet):
    return [int(x * 255) for x in colorsys.hsv_to_rgb(triplet[0], triplet[1], triplet[2])]

def hsv_to_rgb_norm(triplet):
    return colorsys.hsv_to_rgb(triplet[0], triplet[1], triplet[2])

class RepeatedTimer:
    """Repeat `function` every `interval` seconds."""

    def __init__(self, interval, function, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.start = time.time()
        self.event = Event()
        self.thread = Thread(target=self._target, daemon=True)
        self.thread.start()

    def _target(self):
        while not self.event.wait(self._time):
            self.function(*self.args, **self.kwargs)

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start) % self.interval)

    def stop(self):
        self.event.set()
        self.thread.join()

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class AnimationController:
    def __init__(self, led_locations, refresh_rate, led_controller):
        self.params = {
            'master_brightness' : 1.0,
            'color_animation_mode' : LEDColorAnimationMode.CycleHue,
            'color_animation_speed' : 0.2,
            'color_animation_scale' : 10,
            'secondary_animation_mode' : LEDSecondaryAnimationMode.Static,
            'secondary_animation_speed' : 0.2,
            'secondary_animation_scale' : 10,
            'saturation': 1.0,
            'red_frequency': 1.0,
            'green_frequency': 0.666,
            'blue_frequency': 0.333,
            'red_phase_offset': 0.0,
            'green_phase_offset': 0.5,
            'blue_phase_offset': 1.0,
            'colors' : [ (0.0, 0.0, 1.0) ]
        }
        self.points = led_locations
        self.refresh_rate = refresh_rate
        self.led_controller = led_controller
        self.time = 0

    def set_param(self, key, value):
        self.params[key] = value

    def begin_animation_thread(self):
        self.timer = RepeatedTimer(1 / self.refresh_rate, self.update_leds)

    def get_next_frame(self):
        led_states = []
        for i, point in enumerate(self.points):
            color = (0.0, 0.0, 0.0)
            color_anim_time = self.time * self.params['color_animation_speed']
            color_anim_scale = i / float(self.params['color_animation_scale'])

            if self.params['color_animation_mode'] == LEDColorAnimationMode.SolidColor:
                color = self.params['colors'][0]

            elif self.params['color_animation_mode'] == LEDColorAnimationMode.CycleHue:
                color = ((color_anim_time + color_anim_scale) % 1.0,
                         self.params['saturation'], 1.0)

            elif self.params['color_animation_mode'] == LEDColorAnimationMode.Sines:
                rgb = hsv_to_rgb_norm(self.params['colors'][0])
                r_half, g_half, b_half = [x / 2 for x in rgb]
                r = r_half * math.sin(color_anim_time * self.params['red_frequency'] +
                                      self.params['red_phase_offset'] + color_anim_scale) + r_half
                g = g_half * math.sin(color_anim_time * self.params['green_frequency'] +
                                      self.params['green_phase_offset'] + color_anim_scale) + g_half
                b = b_half * math.sin(color_anim_time * self.params['blue_frequency'] +
                                      self.params['blue_phase_offset'] + color_anim_scale) + b_half
                color = colorsys.rgb_to_hsv(r, g, b)

            color = (color[0], color[1], color[2] * self.params['master_brightness'])
            led_states.append(hsv_to_rgb(color))

        self.time += 1.0 / self.refresh_rate
        return led_states

    def update_leds(self):
        self.led_controller.set_led_states(self.get_next_frame())

    def end_animation_thread(self):
        self.timer.stop()
