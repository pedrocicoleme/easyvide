# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify, Response

import time, datetime, logging

from threading import Thread

import numpy as np
import cv2
import imutils

from collections import deque

from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

running_cameras = {}

engine = create_engine('sqlite:///easyvide.db', convert_unicode=True)
db = scoped_session(sessionmaker(bind=engine))

cv2.setUseOptimized(True)

camera_table_sql = u"""
CREATE TABLE IF NOT EXISTS camera (
    cameraID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name VARCHAR(255) NOT NULL,
    source VARCHAR(1024) NOT NULL,
    color BOOLEAN NOT NULL DEFAULT 1,
    res_w INTEGER NOT NULL DEFAULT 640,
    res_h INTEGER NOT NULL DEFAULT 480,
    fps INTEGER NOT NULL DEFAULT 1,
    ev_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ev_flag INTEGER NOT NULL DEFAULT 0,
    ev_status BOOLEAN NOT NULL DEFAULT 1);
"""
db.execute(camera_table_sql)

metadata = MetaData(bind=engine)

cameraTbl = Table(u'camera', metadata, autoload=True)

camera = Blueprint(u'camera', __name__, template_folder=u'templates')

# cameras_list = [
#     {u'cameraID': 0, u'name': u'Sala de Entrada', u'source': u'http://192.168.1.8:81/videostream.asf?user=admin&password=admin', u'fps': 1, u'color': False, u'resolution': u'640x480'},
#     {u'cameraID': 1, u'name': u'Notebook', u'source': u'0', u'fps': 1, u'color': True, u'resolution': u'640x480'}]

run_state = True
def get_run_state(val=None):
    global run_state

    if val != None:
        run_state = val

        check_should_refresh(val)

    return run_state

should_refresh_cameras_options = True
def check_should_refresh(val=None):
    global should_refresh_cameras_options

    if val != None:
        should_refresh_cameras_options = val

    return should_refresh_cameras_options

def get_cameras_list():
    cameras_list = []

    cams = cameraTbl.select().execute().fetchall()

    for cam in cams:
        cam = dict(cam)

        cam[u'resolution'] = u'%sx%s' % (cam[u'res_w'], cam[u'res_h'])

        cameras_list.append(cam)

    return cameras_list

conf = {
    u'show_video': True,
    u'use_dropbox': True,
    u'dropbox_key': u'YOUR_DROPBOX_KEY',
    u'dropbox_secret': u'YOUR_DROPBOX_SECRET',
    u'dropbox_base_path': u'YOUR_DROPBOX_PATH',
    u'min_upload_second': 3.0,
    u'min_motion_frames': 1,
    u'camera_warmup_time': 2.5,
    u'delta_thresh': 20,
    u'resolution': [640, 480],
    u'fps': 3,
    u'min_area': 1000}

running_cameras = {}

class Camera(Thread):
    def __init__(self, cam):
        Thread.__init__(self)

        self.cameraID = cam[u'cameraID']
        self.source = cam[u'source']
        self.fps = cam[u'fps']
        self.spf = 1.0 / self.fps
        self.res_w = cam[u'res_w']
        self.res_h = cam[u'res_h']
        self.resolution = u'%sx%s' % (cam[u'res_w'], cam[u'res_h'])

        self.cap = None

        self.queue_capture = deque([], 10*self.fps)
        self.queue_analysis = deque([], 10*self.fps)
        self.queue_web = deque([], 10*self.fps)

        self.block_video = False

        self.status = False

    def __del__(self):
        del self.cap

    def get_cap(self):
        if self.cap:
            return self.cap

        if unicode(self.source).isdecimal():
            input_resource = int(self.source)
        else:
            input_resource = self.source

        self.cap = cv2.VideoCapture(input_resource)
        self.cap.set(cv2.cv.CV_CAP_PROP_FPS, 2)

        return self.cap

    #@profile
    def detect_motion(self):
        print u'starting detection for cameraID %s...' % self.cameraID

        was_occupied = occupied = False

        while True:
            try:
                # initialize the camera and grab a reference to the raw camera capture
                camera = self.get_cap()
                
                # allow the camera to warmup, then initialize the average frame, last
                # uploaded timestamp, and frame motion counter
                print u'[INFO] warming up...'
                time.sleep(conf[u'camera_warmup_time'])
                avg = None
                lastUploaded = datetime.datetime.now()
                motionCounter = 0

                last_time = time.time()

                # capture frames from the camera
                while True:
                    # grab the raw NumPy array representing the image and initialize
                    # the timestamp and occupied/unoccupied text

                    sleep_interval = self.spf - (time.time() - last_time)
                    if sleep_interval > 0:
                        time.sleep(0.020)
                        camera.grab()
                        continue

                    last_time = time.time()

                    grabbed, frame = camera.read()

                    if not grabbed:
                        self.status = False

                        time.sleep(3)
                        break
                    else:
                        self.status = True

                    self.queue_capture.appendleft(frame)

                    ret, jpeg = cv2.imencode('.jpg', frame)
                    self.queue_web.appendleft(jpeg.tobytes())

                    timestamp = datetime.datetime.now()
                    text = u'Unoccupied'
                 
                    # resize the frame, convert it to grayscale, and blur it
                    frame = imutils.resize(frame, width=500)
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    # equalize histogram
                    gray = cv2.equalizeHist(gray)
                    gray = cv2.GaussianBlur(gray, (21, 21), 0)
                 
                    # if the average frame is None, initialize it
                    if avg is None:
                        print u'[INFO] starting background model...'
                        avg = gray.copy().astype(u'float')
                        continue
                 
                    # accumulate the weighted average between the current frame and
                    # previous frames, then compute the difference between the current
                    # frame and running average
                    cv2.accumulateWeighted(gray, avg, 0.5)
                    frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

                    # threshold the delta image, dilate the thresholded image to fill
                    # in holes, then find contours on thresholded image
                    thresh = cv2.threshold(frameDelta, conf[u'delta_thresh'], 255, cv2.THRESH_BINARY)[1]
                    thresh = cv2.dilate(thresh, None, iterations=2)
                    (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    was_occupied = occupied
                 
                    now_occupied = False
                    # loop over the contours
                    for c in cnts:
                        # if the contour is too small, ignore it
                        if cv2.contourArea(c) < conf[u'min_area']:
                            continue
                 
                        # compute the bounding box for the contour, draw it on the frame,
                        # and update the text
                        (x, y, w, h) = cv2.boundingRect(c)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        text = u'Occupied'

                        if len(self.queue_capture) == self.queue_capture.maxlen:
                            now_occupied = True

                    if now_occupied:
                        occupied = True
                    else:
                        occupied = False
                        if was_occupied:
                            pass
                            #self.make_a_video()

                    # draw the text and timestamp on the frame
                    ts = timestamp.strftime(u'%A %d %B %Y %H:%M:%S')
                    cv2.putText(frame, u'Room Status: {}'.format(text), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

                    #cv2.imshow(u'frame', frame)
                    frame2 = im = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                    # create a CLAHE object (Arguments are optional).
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                    cl1 = clahe.apply(frame2)

                    # ret, jpeg = cv2.imencode('.jpg', cl1)
                    # self.queue_analysis.appendleft(jpeg.tobytes())

                    self.queue_analysis.appendleft(cl1)

                    if not get_run_state() or check_should_refresh():
                        break
            except Exception as e:
                logging.exception(u'error trying to get picture')

                self.status = False

                time.sleep(1)

            if not get_run_state() or check_should_refresh():
                break

        self.cap.release()
        self.cap = None

    def make_a_video(self):
        if self.block_video:
            return True

        self.block_video = True
        print u'making a video!'

        queue_copy = list(self.queue_capture)

        # images are grayscale, so...
        layers = 1
        height, width, layers = queue_copy[0].shape

        print queue_copy[0].shape

        video_filename = '/home/pedro/video%s.avi' % (int(round(time.time() * 1000)))

        video = cv2.VideoWriter()
        video.open(video_filename, cv2.cv.CV_FOURCC(*'XVID'), self.fps, (width, height), True)

        for img in reversed(queue_copy):
            video.write(img)

        video.release()

        import subprocess

        dir = video_filename.strip(".avi")
        command = "avconv -i %s.avi -c:v libx264 -c:a copy %s.mp4" % (dir, dir)

        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        self.block_video = False

        print u'video finished'

        #send_video_via_telegram(video_filename.replace('avi', 'mp4'))

        return True

    def run(self):
        self.detect_motion()

def send_video_via_telegram(filename):
    import telegram

    bot = telegram.Bot(token='token')

    print bot.getMe()

    chat_id = bot.getUpdates()[-1].message.chat_id

    bot.sendMessage(chat_id=chat_id, text="We found a suspect motion, see the video")

    bot.sendVideo(chat_id=chat_id, video=open(filename, 'rb'))


#input_resource = u'http://192.168.1.8:81/videostream.cgi?user=admin&password=admin&rate=2&x=.mjpeg'
#input_resource = u'rtsp://admin:admin@192.168.1.8:81/h.264.sdp?x=tcp'
input_resource = u'http://192.168.1.8:81/videostream.asf?user=admin&password=admin'

def cam_threads_controller():
    global running_cameras

    while True:
        if get_run_state():
            if check_should_refresh():
                for sid, running_camera in running_cameras.iteritems():
                    running_camera.join()
                    print u'retornou a cameraID %s' % sid

                check_should_refresh(False)

                for camera in get_cameras_list():
                    sid = u'%s' % camera[u'cameraID']

                    running_cameras[sid] = Camera(camera)
                    running_cameras[sid].daemon = True
                    running_cameras[sid].start()
            else:
                time.sleep(1)
        else:
            time.sleep(1)

threads_master = Thread(target=cam_threads_controller)
threads_master.daemon = True
threads_master.start()

@camera.route(u'/api/state')
@camera.route(u'/api/state/<int:state>')
def set_get_state(state=None):
    if state != None:
        get_run_state(True if int(state) == 1 else False)
    
    state = {
        u'enable_motion': get_run_state()}
    
    return jsonify(**state)

@camera.route(u'/api/camera/list')
def index():
    cameras = {
        u'cameras': get_cameras_list()}
    
    return jsonify(**cameras)

@camera.route(u'/api/camera', methods=[u'POST'])
@camera.route(u'/api/camera/<int:cameraID>', methods=[u'PUT'])
def upsert_camera(cameraID=None):
    global should_refresh_cameras_options

    cam = dict()

    cam[u'name'] = request.json[u'name']
    cam[u'source'] = request.json[u'source']

    cam[u'color'] = True if request.json[u'color'] else False
    cam[u'fps'] = int(request.json[u'fps'])

    try:
        cam[u'res_w'], cam[u'res_h'] = [int(x) for x in request.json[u'resolution'].split(u'x', 1)]
    except:
        cam[u'res_w'] = 640
        cam[u'res_h'] = 480

    result = {}
    if not cameraID:
        cam[u'cameraID'] = None
        ins = cameraTbl.insert().values(cam).execute()
    else:
        cam[u'cameraID'] = cameraID
        ins = cameraTbl.update().where(cameraTbl.c.cameraID == cameraID).values(cam).execute()

    db.commit()
    db.flush()
    db.close()

    should_refresh_cameras_options = True

    result = dict()
    result[u'status'] = u'SUCCESS'
    result[u'message'] = u'New camera created successfully' if not cameraID else u'Camera updated successfully'
    # except Exception as e:
    #     raise(e)

    #     result[u'status'] = u'ERROR'
    #     result[u'message'] = u'An error ocurred while %s the camera' % u'creating' if not cameraID else u'updating'

    return jsonify(**result)

@camera.route(u'/api/camera/<int:cameraID>', methods=[u'DELETE'])
def delete_camera(cameraID):
    global should_refresh_cameras_options

    ins = cameraTbl.delete().where(cameraTbl.c.cameraID == cameraID).execute()
    db.commit()
    db.flush()
    db.close()

    should_refresh_cameras_options = True

    result = dict()
    result[u'status'] = u'SUCCESS'
    result[u'message'] = u'Camera deleted'
    
    return jsonify(**result)

def live_stream_helper(cameraID, fps=1):
    sid = u'%s' % cameraID
    
    spf = 1.0 / fps

    last_time = time.time()

    while True:
        if not get_run_state() or check_should_refresh():
            break
            
        sleep_interval = spf - (time.time() - last_time)
        if sleep_interval > 0:
            time.sleep(sleep_interval)

        last_time = time.time()
        
        try:
            if running_cameras[sid].status:
                frame = running_cameras[sid].queue_web[0]

                yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            else:
                time.sleep(1)
        except Exception as e:
            logging.exception(u'error sending frame via http')

@camera.route(u'/live_stream')
@camera.route(u'/live_stream/<int:source>')
@camera.route(u'/live_stream/<int:cameraID>/<int:fps>')
def live_stream(cameraID=None, fps=1):
    return Response(live_stream_helper(cameraID=cameraID, fps=fps), mimetype=u'multipart/x-mixed-replace; boundary=frame')