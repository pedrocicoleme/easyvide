# -*- coding: utf-8 -*-

from flask import Blueprint, request, jsonify

from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('sqlite:///easyvide.db', convert_unicode=True)
db = scoped_session(sessionmaker(bind=engine))

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
    # try:
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

fps = 1
spf = 1.0 / fps

def live_stream_helper(cameraID, fps=fps):
    sid = u'%s' % cameraID
    
    spf = 1.0 / fps

    last_time = time.time()

    while True:
        sleep_interval = spf - (time.time() - last_time)
        if sleep_interval > 0:
            time.sleep(sleep_interval)

        last_time = time.time()
        
        try:
            if view_camera.framebuffers[sid][u'status']:
                frame = view_camera.framebuffers[sid][u'queue'][0]

                yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            else:
                time.sleep(1)
        except Exception as e:
            logging.exception(u'error sending frame via http')

        if not get_run_state() or check_should_refresh():
            break

@camera.route(u'/live_stream')
@camera.route(u'/live_stream/<int:source>')
@camera.route(u'/live_stream/<int:cameraID>/<int:fps>')
def live_stream(cameraID=None, fps=1):
    return Response(live_stream_helper(cameraID=cameraID, fps=fps), mimetype=u'multipart/x-mixed-replace; boundary=frame')