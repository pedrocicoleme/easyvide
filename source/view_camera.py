# -*- coding: utf-8 -*-

import numpy as np
import cv2

import time
import datetime

import imutils

last_frame = u'bunda le le'

fps = 1
def get_cap(input_resource):
    cap = cv2.VideoCapture(input_resource)
    #cap.set(cv2.cv.CV_CAP_PROP_FPS, fps)
    return cap

def view_image(input_resource):
    cap = get_cap(input_resource)

    video = None

    while(True):
        # Capture frame-by-frame
        ret, frame = cap.read()

        # Our operations on the frame come here
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # preparando video
        if not video:
            print u'vai criar video'
            height , width , layers =  frame.shape

            fourcc = cv2.cv.CV_FOURCC(*'MJPG')
            video = cv2.VideoWriter(u'/home/pedro/git/oculusvidentem/video.avi', fourcc, 20.0, (width, height))

        video.write(frame)

        # Display the resulting frame
        cv2.imshow(u'frame', frame)
        if cv2.waitKey(1) & 0xFF == ord(u'q'):
            break

    if video:
        print u'vai salvar video'
        video.release()
        video = None

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

conf = {
    u'show_video': True,
    u'use_dropbox': True,
    u'dropbox_key': u'YOUR_DROPBOX_KEY',
    u'dropbox_secret': u'YOUR_DROPBOX_SECRET',
    u'dropbox_base_path': u'YOUR_DROPBOX_PATH',
    u'min_upload_second': 3.0,
    u'min_motion_frames': 1,
    u'camera_warmup_time': 2.5,
    u'delta_thresh': 10,
    u'resolution': [640, 480],
    u'fps': 3,
    u'min_area': 1000}

spf = 1.0 / fps

def detect_motion(input_resource):
    print u'starting detection...'
    # initialize the camera and grab a reference to the raw camera capture
    camera = get_cap(input_resource)
     
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

        sleep_interval = spf - (time.time() - last_time)
        if sleep_interval > 0:
            time.sleep(0.020)
            camera.grab()
            continue

        last_time = time.time()

        grabbed, frame = camera.read()

        timestamp = datetime.datetime.now()
        text = u'Unoccupied'
     
        # resize the frame, convert it to grayscale, and blur it
        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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
     
        # draw the text and timestamp on the frame
        ts = timestamp.strftime(u'%A %d %B %Y %H:%M:%S')
        cv2.putText(frame, u'Room Status: {}'.format(text), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        #cv2.imshow(u'frame', frame)
        frame2 = im = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # create a CLAHE object (Arguments are optional).
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        cl1 = clahe.apply(frame2)

        global last_frame
        ret, jpeg = cv2.imencode('.jpg', cl1)
        last_frame = jpeg.tobytes()

        if cv2.waitKey(1) & 0xFF == ord(u'q'):
            break

#input_resource = u'http://192.168.1.8:81/videostream.cgi?user=admin&password=admin&rate=2&x=.mjpeg'
#input_resource = u'rtsp://admin:admin@192.168.1.8:81/h.264.sdp?x=tcp'
input_resource = u'http://192.168.1.8:81/videostream.asf?user=admin&password=admin'
#input_resource = 0
#detect_motion(input_resource)
#view_image(input_resource)

from threading import Thread
from time import sleep

thread = Thread(target=detect_motion, args=(input_resource, ))
thread.daemon = True
thread.start()