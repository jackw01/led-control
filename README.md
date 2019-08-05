# led-control
WS2812 LED controller with web interface for Raspberry Pi

## Install
1. Install the rpi_ws2812x library and connect an LED strip to your Raspberry Pi: https://learn.adafruit.com/neopixels-on-raspberry-pi
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
