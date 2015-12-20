# -*- coding: utf-8 -*-

import logging

from flask import Flask, render_template, Response
app = Flask(__name__)

import view_camera
import time

from camera import get_run_state, check_should_refresh
from camera import camera

app.register_blueprint(camera)

@app.route(u'/')
def index():
    return render_template(u'index.html')

if __name__ == u'__main__':
    app.run(debug=True, use_reloader=False, threaded=True)