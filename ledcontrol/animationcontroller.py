import colorsys, time
from threading import Event, Thread
from ledcontrol.ledmodes import LEDColorAnimationMode, LEDSecondaryAnimationMode

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

class ColorHSV:
    def __init__(self, triplet):
        self.h = triplet[0]
        self.s = triplet[1]
        self.v = triplet[2]

    def rgb():
        # TODO: FastLED style conversion
        return colorsys.hsv_to_rgb(h, s, v)

class AnimationController:
    def __init__(self, led_locations, refresh_rate):
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
        self.points = led_locations
        self.refresh_rate = refresh_rate

    def set_param(self, key, value):
        self.params[key] = value
        print(self.params)

    def begin_animation_thread(self):
        self.timer = RepeatedTimer(1 / self.refresh_rate, self.update_leds)

    def get_next_frame(self):
        led_states = []
        for point in self.points:
            if self.params['color_animation_mode'] == LEDColorAnimationMode.SolidColor:
                led_states.append(ColorHSV(self.params['colors'][0]))
            else:
                led_states.append(ColorHSV(0, 0, 0))

        return led_states

    def update_leds(self):
        led_states = self.get_next_frame()
        for i, state in led_states:
            rgb = state.rgb()

    def end_animation_thread(self):
        self.timer.stop()
