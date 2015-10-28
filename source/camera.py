# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify

camera = Blueprint(u'camera', __name__, template_folder=u'templates')

cameras_list = [
    {u'cameraID': 0, u'name': u'Sala de Entrada', u'source': u'http://192.168.1.8:81/videostream.asf?user=admin&password=admin', u'fps': 0.3, u'color': False, u'resolution': u'640x480'},
    {u'cameraID': 1, u'name': u'Notebook', u'source': u'0', u'fps': 0.7, u'color': True, u'resolution': u'640x480'}]

@camera.route(u'/api/camera/list')
def index():
    cameras = {
        u'cameras': cameras_list}
    
    return jsonify(**cameras)