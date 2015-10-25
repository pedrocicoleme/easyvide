# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify

camera = Blueprint(u'camera', __name__, template_folder=u'templates')

@camera.route(u'/api/camera/list')
def index():
    cameras = {
        u'cameras': [
            {u'name': u'Sala de Entrada', u'source': u'/live_stream/0/0.3'},
            {u'name': u'Sala de Entrada 2', u'source': u'/live_stream/0/0.7'},
            {u'name': u'Sala de Entrada 3', u'source': u'/live_stream/0/1.0'}]}
    
    return jsonify(**cameras)