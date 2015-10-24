# -*- coding: utf-8 -*-

from flask import Flask, render_template, Response
app = Flask(__name__)

import view_camera
import time

fps = 1
spf = 1.0 / fps

def live_stream_helper(source, fps=fps):
    spf = 1.0 / fps

    last_time = time.time()

    while True:
        sleep_interval = spf - (time.time() - last_time)
        if sleep_interval > 0:
            time.sleep(sleep_interval)

        last_time = time.time()
        
        frame = view_camera.last_frame
        #frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route(u'/')
def index():
    return render_template(u'index.html')

@app.route(u'/live_stream')
@app.route(u'/live_stream/<int:source>')
@app.route(u'/live_stream/<int:source>/<float:fps>')
def live_stream(source=None, fps=1):
    return Response(live_stream_helper(source=source, fps=fps), mimetype=u'multipart/x-mixed-replace; boundary=frame')

if __name__ == u'__main__':
    app.run(debug=True, use_reloader=False)