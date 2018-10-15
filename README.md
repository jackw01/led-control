# led-control
WS2812 LED controller with web interface for Raspberry Pi

## Install
Install the rpi_ws2812x library: https://learn.adafruit.com/neopixels-on-raspberry-pi/software

Run `pip install led-control` to install led-control

## Usage
```
usage: ledcontrol [-h] [--port PORT] [--host HOST] [--strip STRIP] [--fps FPS]
                  [--led_pin LED_PIN] [--led_data_rate LED_DATA_RATE]
                  [--led_dma_channel LED_DMA_CHANNEL]
                  [--led_pixel_order LED_PIXEL_ORDER]

optional arguments:
  -h, --help            show this help message and exit
  --port PORT           Port to use for web interface. Default: 80
  --host HOST           Hostname to use for web interface. Default: 0.0.0.0
  --strip STRIP         Configure for a LED strip of this length.
  --fps FPS             Refresh rate for LEDs, in FPS. Default: 24
  --led_pin LED_PIN     Pin for LEDs. Default: 18
  --led_data_rate LED_DATA_RATE
                        Data rate for LEDs. Default: 800000 Hz
  --led_dma_channel LED_DMA_CHANNEL
                        DMA channel for LEDs. Default: 5
  --led_pixel_order LED_PIXEL_ORDER
                        LED color channel order. Either RGB or GRB. Default: GRB
```
