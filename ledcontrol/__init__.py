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
    args = parser.parse_args()

    app = create_app()
    run_simple(args.host, int(args.port), app,
               use_reloader=True,
               use_debugger=True,
               use_evalex=True)
