"""
File:ping.py
Author:Young
"""
from flask import jsonify
from . import bp


@bp.route('/ping', methods=['GET'])
def ping():
    """前端Vue.js用来测试与后端Flask API的连通性"""
    return jsonify(message = 'Pong!')


