# led-control
WS2812 LED controller with web interface for Raspberry Pi

## Note
Version 2.0 is currently in development in the master branch. Version 1.0 is contained in the 1.0 branch, but is no longer usable as Adafruit's setup instructions and the name and installation method for the library used for WS2812 LEDs have changed.

## Install
1. Read this Adafruit guide and follow the directions to connect an LED strip to your Raspberry Pi, install the Python library, and test the strip: https://learn.adafruit.com/neopixels-on-raspberry-pi
2. `git clone https://github.com/jackw01/led-control.git`
3. `cd led-control`
4. `python3 setup.py install`
5. `sudo ledcontrol --port 8080 --strip 150 --fps 30`

## Arguments
```
usage: ledcontrol [-h] [--port PORT] [--host HOST] [--strip STRIP] [--fps FPS]
                  [--led_pin LED_PIN] [--led_data_rate LED_DATA_RATE]
                  [--led_dma_channel LED_DMA_CHANNEL]
                  [--led_pixel_order LED_PIXEL_ORDER]
optional arguments:
  -h, --help            show this help message and exit
  --port PORT           Port to use for web interface. Default: 80
  --host HOST           Hostname to use for web interface. Default: 0.0.0.0
  --strip STRIP         Length of the LED strip.
  --fps FPS             Refresh rate for LEDs, in FPS. Default: 24
  --led_pin LED_PIN     Pin for LEDs (GPIO10, GPIO12, GPIO18 or GPIO21). Default: 18
  --led_data_rate LED_DATA_RATE
                        Data rate for LEDs. Default: 800000 Hz
  --led_dma_channel LED_DMA_CHANNEL
                        DMA channel for LEDs. Default: 5
  --led_pixel_order LED_PIXEL_ORDER
                        LED color channel order. Either RGB or GRB. Default: GRB
```

## Features
* Supports cheap and readily available WS281x and SK6812 LED strips, strings, and arrays
* Capable of achieving up to 120 FPS on 60 LEDs and 60 FPS on 150 LEDs with low-end hardware (Raspberry Pi Zero)

## Animation Scripting
Animation patterns are defined as Python functions. The LEDControl web interface allows editing and creation of patterns using a subset of Python. Scripts are compiled using [RestrictedPython](https://github.com/zopefoundation/RestrictedPython) and run with a restricted set of builtin functions and global variables. This should prevent filesystem access and code execution, but the scripting system **should not be considered completely secure** and the web interface **should not be exposed to untrusted users**.

### Supported Python Globals

* Builtins: `None`, `False`, `True`, `abs`, `bool`, `callable`, `chr`, `complex`, `divmod`, `float`, `hash`, `hex`, `id`, `int`, `isinstance`, `issubclass`, `len`, `oct`, `ord`, `pow`, `range`, `repr`, `round`, `slice`, `str`, `tuple`, `zip`
* All functions and constants from the [`math` module](https://docs.python.org/3/library/math.html)
* All functions from the [`random` module](https://docs.python.org/3/library/random.html)

### Additional Utility Functions

#### `clamp(x, min, max)`
Returns min if x < min and max if x > max, otherwise returns x

#### `wave_pulse(t, duty_cycle=0.5)`
Returns the instantaneous value of a 1Hz pulse wave of the specified duty cycle at time `t`

#### `wave_triangle(t)`
Returns the instantaneous value of a 1Hz triangle wave at time `t`

#### `wave_sine(t)`
Returns the instantaneous value of a 1Hz sine wave at time `t`

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
Delta time in cycles

##### `x`, `y`
Normalized (0 to 1) value representing the position of the current LED in arbitrary units (after mapping LED indices to positions and scaling). Straight LED strips are mapped to the x axis only. One position unit represents the scale factor multiplied by the length of the axis. At a scale of less than 1, one position unit represents a fraction of the axis length and the animation is repeated to fill all the LEDs.

##### `prev_state`
Previous color state of the current LED as an HSV or RGB tuple. Initialized to (0, 0, 0) on the first animation frame.

#### Return Values
Pattern functions must return a color in tuple form and either `hsv` or `rgb` depending on the format of the color.
