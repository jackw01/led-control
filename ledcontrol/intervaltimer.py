import time
from threading import Event, Thread

class IntervalTimer:
    'Repeat function call at a regular interval'

    def __init__(self, interval, function, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.count = 0
        self.wait_time = 0
        self.last_start = time.perf_counter()
        self.last_measurement_c = 0
        self.last_measurement_t = 0
        self.perf_avg = 0
        self.event = Event()
        self.thread = Thread(target=self.target, daemon=True)

    def start(self):
        'Starts the timer thread'
        self.thread.start()

    def target(self):
        'Waits until ready and executes target function'
        while not self.event.wait(self.wait_time):
            self.last_start = time.perf_counter()
            self.function(*self.args, **self.kwargs)
            self.perf_avg += (time.perf_counter() - self.last_start)

            self.count += 1
            if self.count % 100 == 0:
                #print('Average execution time (s): {}'.format(self.perf_avg / 100))
                #print('Average speed (cycles/s): {}'.format(self.get_rate()))
                self.perf_avg = 0

            # Calculate wait for next iteration
            self.wait_time = self.interval - (time.perf_counter() - self.last_start)
            if (self.wait_time < 0):
                self.wait_time = 0

    def get_rate(self):
        'Returns current rate in cycles per second'
        result = ((self.count - self.last_measurement_c) /
                  (self.last_start - self.last_measurement_t))
        self.last_measurement_c = self.count
        self.last_measurement_t = self.last_start
        return result

    def stop(self):
        'Stops the timer thread'
        self.event.set()
        self.thread.join()
