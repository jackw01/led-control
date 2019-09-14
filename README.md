# led-control
Advanced WS2812/SK6812 LED controller with Python animation programming and web code editor/control interface for Raspberry Pi

## Features
* Lightweight, responsive web interface works on both desktop and mobile devices
* In-browser code editor with smart indentation, syntax highlighting, and syntax error detection makes creating animation patterns easy
* Supports cheap and readily available WS281x and SK6812 LED strips and strings
* Capable of achieving up to 280 FPS on 60 LEDs and 120 FPS on 150 LEDs on a Raspberry Pi Zero (see note below)
* Web backend written in Python using the [Flask](https://github.com/pallets/flask) web framework
* Color conversions, color correction, and final rendering steps are done in a C extension module for maximum performance

### Framerate Note
Only very simple animation patterns will run this fast. More complex patterns will run slower, but framerates should stay above 24FPS even with large numbers of LEDs (150). This should not be an issue unless you are trying to display very fast-moving animations on long LED strips. All of the framerate numbers here were obtained from testing on a Raspberry Pi Zero, and almost any other Raspberry Pi will be able to run animations faster.

## Install
### Software Setup
1. Read [this Adafruit guide](https://learn.adafruit.com/neopixels-on-raspberry-pi) and follow the directions to connect an LED strip to your Raspberry Pi, install the Python library, and test the strip. More information on connecting LED strips and PWM/DMA usage is available [here](https://github.com/jgarff/rpi_ws281x).
2. `git clone https://github.com/jackw01/led-control.git`
3. `cd led-control`
4. `python3 setup.py install`. Python 3.6 or newer is required.
5. `sudo ledcontrol --port 8080 --strip 150 --fps 30`

### Command Line Configuration Arguments
Web server and LED hardware parameters must be specified as command line arguments when running ledcontrol.
```
usage: ledcontrol [-h] [--port PORT] [--host HOST] [--strip STRIP] [--fps FPS]
                  [--led_pin LED_PIN] [--led_data_rate LED_DATA_RATE]
                  [--led_dma_channel LED_DMA_CHANNEL]
                  [--led_strip_type LED_STRIP_TYPE]
                  [--led_pixel_order LED_PIXEL_ORDER]
                  [--led_color_correction LED_COLOR_CORRECTION]
optional arguments:
  -h, --help            show this help message and exit
  --port PORT           Port to use for web interface. Default: 80
  --host HOST           Hostname to use for web interface. Default: 0.0.0.0
  --led_count LED_COUNT Length of the LED strip.
  --fps FPS             Refresh rate limit for LEDs, in FPS. Default: 60
  --led_pin LED_PIN     Pin for LEDs (GPIO10, GPIO12, GPIO18 or GPIO21). Default: 18
  --led_data_rate LED_DATA_RATE
                        Data rate for LEDs. Default: 800000 Hz
  --led_dma_channel LED_DMA_CHANNEL
                        DMA channel for LEDs. DO NOT USE CHANNEL 5 ON Pi 3 B.
                        Default: 10
  --led_strip_type LED_STRIP_TYPE
                        LED chipset. Either WS2812 or SK6812. Default: WS2812
  --led_pixel_order LED_PIXEL_ORDER
                        LED color channel order. Any combination of RGB with
                        or without a W at the end. Default: GRB
  --led_color_correction LED_COLOR_CORRECTION
                        LED color correction in RGB hex form. Use #FFB0F0 for
                        5050 package LEDs on strips and arrays and #FFE08C for
                        through-hole package LEDs or light strings. Default:
                        #FFB0F0
```

## Animation Editing
Animation patterns are defined as Python functions. The LEDControl web interface allows editing and creation of patterns using a subset of Python. Patterns are compiled using [RestrictedPython](https://github.com/zopefoundation/RestrictedPython) and run with a restricted set of builtin functions and global variables. This should prevent filesystem access and code execution, but the scripting system **should not be considered completely secure** and the web interface **should not be exposed to untrusted users**.

### Pattern Function Guide
Each animation frame, the pattern function is called once per LED/pixel with time, position, and previous state as inputs to determine the next color of that pixel.

```python
# cycle_hue_1d
def pattern(t, dt, x, y, prev_state):
    return (t + x, 1, 1), hsv
```

#### Arguments
##### `t`
Time in cycles (an arbitary unit that represents one animation cycle as a floating point number). Calculated by multiplying real time in seconds by animation speed in Hz (cycles/second).

##### `dt`
Delta time in cycles.

##### `x`, `y`
Normalized (0 to 1) value representing the position of the current LED in arbitrary units (after mapping LED indices to positions and scaling). Straight LED strips are mapped to the x axis only. One position unit represents the scale factor multiplied by the length of the axis. At a scale of less than 1, one position unit represents a fraction of the axis length and the animation is repeated to fill all the LEDs.

##### `prev_state`
Previous color state of the current LED as an HSV or RGB tuple. Initialized to `(0, 0, 0)` on the first animation frame.

#### Return Values
Pattern functions must return a color in tuple form and either `hsv` or `rgb` depending on the format of the color. All values must be in the 0 to 1 range, except for hue. Hue values less than 0 or greater than 1 will wrap. RGB values less than zero or greater than one will be clamped to the 0-1 range.

### Supported Python Globals
* Builtins: `None`, `False`, `True`, `abs`, `bool`, `callable`, `chr`, `complex`, `divmod`, `float`, `hash`, `hex`, `id`, `int`, `isinstance`, `issubclass`, `len`, `oct`, `ord`, `pow`, `range`, `repr`, `round`, `slice`, `str`, `tuple`, `zip`
* All functions and constants from the [`math` module](https://docs.python.org/3/library/math.html)
* All functions from the [`random` module](https://docs.python.org/3/library/random.html)

### Wave Functions
All waveforms have a period of 1 time unit, a range from 0 to 1, and a peak (`f(t)=1`) at `t=0`. These wave functions are implemented in C which gives a suprisingly significant performance improvement over Python.

#### `wave_sine(t)`
Returns the instantaneous value of a 1Hz sine wave at time `t`.

#### `wave_cubic(t)`
Returns the instantaneous value of a 1Hz cubic approximated sine wave (triangle wave with cubic easing) at time `t`. Appears to spend more time near 0 and 1 than a sine wave.

#### `wave_triangle(t)`
Returns the instantaneous value of a 1Hz triangle wave at time `t`.

#### `wave_pulse(t, duty_cycle)`
Returns the instantaneous value of a 1Hz pulse wave of the specified duty cycle (range 0 to 1) at time `t`.

### Additional Utility Functions
#### `clamp(x, min, max)`
Returns `min` if `x < min` and max if `x > max`, otherwise returns `x`

#### `fract(x)`
Returns the floating point component of `x` (`x - floor(x)`)

#### `impulse_exp(t)`
Asymmetrical exponential "impulse" wave function. Peaks at `t=1`.

#### `blackbody_to_rgb(kelvin)`
Returns a normalized RGB tuple for a color temperature in Kelvin.

#### `blackbody_correction_rgb(rgb, kelvin)`
Tints an RGB color (normalized RGB tuple) to a color temperature in Kelvin. Returns a normalized RGB tuple.
