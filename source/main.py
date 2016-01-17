# -*- coding: utf-8 -*-

import logging

from flask import Flask, render_template, Response
app = Flask(__name__)

from camera import camera

app.register_blueprint(camera)

@app.route(u'/')
def index():
    return render_template(u'index.html')

if __name__ == u'__main__':
    app.run(host='0.0.0.0', debug=True, use_reloader=False, threaded=True)