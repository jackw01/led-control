from flask import Flask
from werkzeug.serving import run_simple

port = 8080

def create_app():
    app = Flask(__name__)

    return app

def main():
    app = create_app()
    run_simple('127.0.0.1', int(port), app,
               use_reloader=True,
               use_debugger=True,
               use_evalex=True)
