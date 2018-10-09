import time
from threading import Event, Thread
from ledcontrol.ledcontroller import ColorHSV
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
            if self.params['color_animation_mode'] == LEDColorAnimationMode.SolidColor:
                color = self.params['colors'][0]
            elif self.params['color_animation_mode'] == LEDColorAnimationMode.CycleHue:
                color = ((self.time * self.params['color_animation_speed'] +
                          i / float(self.params['color_animation_scale'])) % 1.0,
                         1.0, 1.0)
            led_states.append(ColorHSV(color))

        self.time += 1.0 / self.refresh_rate
        return led_states

    def update_leds(self):
        self.led_controller.set_led_states(self.get_next_frame())

    def end_animation_thread(self):
        self.timer.stop()
