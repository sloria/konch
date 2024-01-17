# vi: set ft=python :
import flask
from flask import Flask

import konch

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello world"


konch.config({"context": [flask.url_for, flask.Flask, flask.render_template]})

# Make sure we're in a request context so we can use
# url_for
ctx = app.test_request_context()


def setup():
    ctx.push()
    app.preprocess_request()


def teardown():
    app.process_response(app.response_class())
    ctx.pop()
