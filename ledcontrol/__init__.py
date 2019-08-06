# led-control WS2812B LED Controller Server
# Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

__version__ = '1.0.0'

import argparse
from ledcontrol.app import create_app
from werkzeug.serving import run_simple

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument('--port', type=int, default=80,
						help='Port to use for web interface. Default: 80')
	parser.add_argument('--host', default='0.0.0.0',
						help='Hostname to use for web interface. Default: 0.0.0.0')
	parser.add_argument('--strip', type=int, default=0,
						help='Length of the LED strip.')
	parser.add_argument('--fps', type=int, default=24,
						help='Refresh rate for LEDs, in FPS. Default: 24')
	parser.add_argument('--led_pin', type=int, default=18,
						help='Pin for LEDs (GPIO10, GPIO12, GPIO18 or GPIO21). Default: 18')
	parser.add_argument('--led_data_rate', type=int, default=800000,
						help='Data rate for LEDs. Default: 800000 Hz')
	parser.add_argument('--led_dma_channel', type=int, default=10,
						help='DMA channel for LEDs. Default: 10')
	parser.add_argument('--led_pixel_order', default='GRB',
						help='LED color channel order. Either RGB or GRB. Default: GRB')
	args = parser.parse_args()

	app = create_app(args.strip, args.fps,
					 args.led_pin, args.led_data_rate, args.led_dma_channel, args.led_pixel_order)
	run_simple(args.host, args.port, app,
			   use_reloader=False,
			   use_debugger=True,
			   use_evalex=True)
