# led-control WS2812B LED Controller Server
# Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

import time, os
from threading import Event, Thread

class IntervalTimer:
    'Repeat function call at a regular interval'

    def __init__(self, interval, function, *args, **kwargs):
        self._interval = interval
        self._function = function
        self._args = args
        self._kwargs = kwargs
        self._count = 0
        self._last_perf_avg_count = -1
        self._wait_time = 0
        self.last_start = time.perf_counter()
        self._last_measurement_c = 0
        self._last_measurement_t = 0
        self._perf_avg = 0
        self._event = Event()
        self._thread = Thread(target=self.target, daemon=True)
        self._is_windows = (os.name == 'nt')

    def start(self):
        'Starts the timer thread'
        self._thread.start()

    def target(self):
        'Waits until ready and executes target function'
        while not self._event.wait(self._wait_time):
            current_start = time.perf_counter()
            self._function(*self._args, **self._kwargs)
            self._count += 1
            cycle_time = time.perf_counter() - current_start
            self._perf_avg += cycle_time

            # Calculate wait for next iteration
            # Needed because of timer resolution on windows or something like that???
            if self._is_windows:
                self._wait_time = self._interval - (current_start - self.last_start)
            else:
                self._wait_time = self._interval - cycle_time
            self.last_start = current_start
            if (self._wait_time < 0):
                self._wait_time = 0

    def get_count(self):
        'Returns cycle count'
        return self._count

    def get_perf_avg(self):
        'Returns average function execution time and clears accumulator'
        average = self._perf_avg / (self._count - self._last_perf_avg_count)
        self._perf_avg = 0
        self._last_perf_avg_count = self._count
        return average

    def get_rate(self):
        'Returns current rate in cycles per second'
        result = ((self._count - self._last_measurement_c) /
                  (self.last_start - self._last_measurement_t))
        self._last_measurement_c = self._count
        self._last_measurement_t = self.last_start
        return result

    def stop(self):
        'Stops the timer thread'
        self._event.set()
        self._thread.join()
