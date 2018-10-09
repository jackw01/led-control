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
                        help='Configure for a LED strip of this length.')
    parser.add_argument('--fps', type=int, default=24,
                        help='Refresh rate for LEDs, in FPS.')
    args = parser.parse_args()

    app = create_app(args.strip, args.fps)
    run_simple(args.host, int(args.port), app,
               use_reloader=False,
               use_debugger=True,
               use_evalex=True)
