"""
File:message.py
Author:laoyang
"""
from datetime import datetime

from flask import current_app
from flask import g, jsonify
from flask import request
from flask import url_for

from app import db
from app.api.auth import token_auth
from app.api.error import bad_request, error_response
from app.models import Message, User
from . import bp

# restful接口设计
# 发送私信 POST /api/messages/
# 获取所有私信 GET /api/messages/
# 获取一条私信 GET /api/messages/<id>
# 修改一条私信 PUT /api/messages/<id>
# 删除一条私信 DELETE /api/messages/<id>

@bp.route('/messages/',methods=["POST"])
@token_auth.login_required
def create_message():
    """发送一条私信"""
    json_data = request.json

    if not json_data:
        return bad_request('You must post JSON data')
    if 'body' not in json_data and not json_data.get('body'):
        return bad_request('body is required')
    if 'recipient_id' not in json_data and not json_data.get('recipient_id'):
        return bad_request('recipient_id is required')

    user = User.query.get_or_404(json_data['recipient_id'])
    if g.current_user == user:
        return bad_request('You cannot send private message to yourself.')

    message = Message()
    message.from_dict(json_data)
    message.sender = g.current_user
    message.recipient = user
    db.session.add(message)
    db.session.commit()

    user.add_notification('unread_messages_count',user.new_recived_messages())

    response = jsonify(message.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_message', id=message.id)

    return response

@bp.route('/messages/',methods=["GET"])
@token_auth.login_required
def get_messages():
    """获取所有私信"""
    page = request.args.get('page',1,type=int)
    per_page = min(request.args.get('per_page',current_app.config['MESSAGES_PER_PAGE'],type=int),100)
    data = Message.to_collection_dict(Message.query.order_by(Message.timestamp.desc()),page,per_page,'api.get_messages')
    return jsonify(data)

@bp.route('/messages/<int:id>',methods=["GET"])
@token_auth.login_required
def get_message(id):
    """获取一条私信"""
    message = Message.query.get_or_404(id)
    return jsonify(message.to_dict())

@bp.route('/messages/<int:id>',methods=["PUT"])
@token_auth.login_required
def update_message(id):
    """修改一条私信"""
    message = Message.query.get_or_404(id)
    if g.current_user != message.sender:
        return error_response(403)
    json_data = request.json

    if not json_data:
        return bad_request('You must post JSON data.')
    if 'body' not in json_data or not json_data.get('body'):
        return bad_request('Body is required.')

    message.from_dict(json_data)
    db.session.commit()

    return jsonify(message.to_dict())

@bp.route('/messages/<int:id>',methods=["DELETE"])
@token_auth.login_required
def delete_message(id):
    """删除一条私信"""
    message = Message.query.get_or_404(id)
    if g.current_user != message.sender:
        return error_response(403)
    db.session.delete(message)
    db.session.commit()

    message.recipient.add_notification('unread_messages_count',message.recipient.new_recived_messages())

    return '',204
