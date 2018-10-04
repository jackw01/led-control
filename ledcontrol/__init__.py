import argparse
from ledcontrol.app import create_app
from werkzeug.serving import run_simple

port = 8080

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=80,
                        help='Port to use for web interface. Default: 80')
    parser.add_argument('--host', default='127.0.0.1',
                        help='Hostname to use for web interface. Default: 127.0.0.1')
    args = parser.parse_args()

    app = create_app()
    run_simple(args.host, int(args.port), app,
               use_reloader=True,
               use_debugger=True,
               use_evalex=True)
