# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify

from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('sqlite:///easyvide.db', convert_unicode=True)
db = scoped_session(sessionmaker(bind=engine))

# camera_table_sql = u"""
# CREATE TABLE IF NOT EXISTS camera (
#     cameraID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
#     name VARCHAR(255) NOT NULL,
#     source VARCHAR(1024) NOT NULL,
#     color BOOLEAN NOT NULL DEFAULT 1,
#     res_w INTEGER NOT NULL DEFAULT 640,
#     res_h INTEGER NOT NULL DEFAULT 480,
#     fps INTEGER NOT NULL DEFAULT 1,
#     ev_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
#     ev_flag INTEGER NOT NULL DEFAULT 0,
#     ev_status BOOLEAN NOT NULL DEFAULT 1);
# """
# db.execute(camera_table_sql)

metadata = MetaData(bind=engine)

cameraTbl = Table(u'camera', metadata, autoload=True)

camera = Blueprint(u'camera', __name__, template_folder=u'templates')

# cameras_list = [
#     {u'cameraID': 0, u'name': u'Sala de Entrada', u'source': u'http://192.168.1.8:81/videostream.asf?user=admin&password=admin', u'fps': 1, u'color': False, u'resolution': u'640x480'},
#     {u'cameraID': 1, u'name': u'Notebook', u'source': u'0', u'fps': 1, u'color': True, u'resolution': u'640x480'}]

# for cam in cameras_list:
#     cam[u'res_w'], cam[u'res_h'] = cam[u'resolution'].split(u'x')

#     del cam[u'cameraID']
#     del cam[u'resolution']

#     ins = cameraTbl.insert()

#     db.execute(ins, [cam])

db.commit()
db.flush()
#db.close()

cams = cameraTbl.select().execute().fetchall()

cameras_list = []
for cam in cams:
    cam = dict(cam)

    cam[u'resolution'] = u'%sx%s' % (cam[u'res_w'], cam[u'res_h'])

    cameras_list.append(cam)

print cameras_list

@camera.route(u'/api/camera/list')
def index():
    cameras = {
        u'cameras': cameras_list}
    
    return jsonify(**cameras)