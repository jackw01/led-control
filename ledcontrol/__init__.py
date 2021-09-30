# led-control WS2812B LED Controller Server
# Copyright 2021 jackw01. Released under the MIT License (see LICENSE for details).

__version__ = '1.0.0'

import argparse
import json
from ledcontrol.app import create_app
from werkzeug.serving import run_simple

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=80,
                        help='Port to use for web interface. Default: 80')
    parser.add_argument('--host', default='0.0.0.0',
                        help='Hostname to use for web interface. Default: 0.0.0.0')
    parser.add_argument('--led_count', type=int, default=0,
                        help='Number of LEDs')
    parser.add_argument('--pixel_mapping_json', type=argparse.FileType('r'),
                        help='JSON file containing pixel mapping (see README)')
    parser.add_argument('--fps', type=int, default=60,
                        help='Refresh rate limit for LEDs, in FPS. Default: 60')
    parser.add_argument('--led_pin', type=int, default=18,
                        help='Pin for LEDs (see https://github.com/jgarff/rpi_ws281x). Default: 18')
    parser.add_argument('--led_data_rate', type=int, default=800000,
                        help='Data rate for LEDs. Default: 800000 Hz')
    parser.add_argument('--led_dma_channel', type=int, default=10,
                        help='DMA channel for LEDs. DO NOT USE CHANNEL 5 ON Pi 3 B. Default: 10')
    parser.add_argument('--led_pixel_order', default='GRB',
                        help='LED color channel order. Any combination of RGB with or without a W at the end. Default: GRB, try GRBW for SK6812')
    parser.add_argument('--led_color_correction', default='#FFB0F0',
                        help='LED color correction in RGB hex form. Use #FFB0F0 for 5050 package RGB LEDs, #FFA8FF for 5050 RGBW LEDs, and #FFE08C for through-hole package LEDs or light strings. Default: #FFB0F0')
    parser.add_argument('--led_brightness_limit', type=float, default=1.0,
                        help='LED maximum brightness limit for the web UI. Float from 0.0-1.0. Default: 1.0')
    parser.add_argument('--save_interval', type=int, default=60,
                        help='Interval for automatically saving settings in seconds. Default: 60')
    parser.add_argument('--sacn', action='store_true',
                        help='Enable sACN / E1.31 support. Default: False')
    parser.add_argument('--no_timer_reset', action='store_true',
                        help='Do not reset the animation timer and state when patterns are changed. Default: False')
    args = parser.parse_args()

    pixel_mapping = None
    if args.pixel_mapping_json is not None:
        pixel_mapping = json.load(args.pixel_mapping_json)
        args.pixel_mapping_json.close()

    color_correction_hex = args.led_color_correction.lstrip('#')

    app = create_app(args.led_count,
                     pixel_mapping,
                     args.fps,
                     args.led_pin,
                     args.led_data_rate,
                     args.led_dma_channel,
                     args.led_pixel_order.upper(),
                     [int(color_correction_hex[i:i + 2], 16) for i in (0, 2, 4)],
                     args.led_brightness_limit,
                     args.save_interval,
                     args.sacn,
                     args.no_timer_reset)
    run_simple(args.host, args.port, app,
               use_reloader=False,
               use_debugger=True,
               use_evalex=True)
