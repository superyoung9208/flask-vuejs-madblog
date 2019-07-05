"""
File:user.py
Author:Young
"""
import re

from flask import request, jsonify,url_for

from app import db
from app.api.auth import token_auth
from app.api.error import bad_request
from app.models import User
from . import bp

@bp.route('/users',methods=['POST'])
def create_user():
    """创建一个用户"""
    json_data = request.json #接收请求数据
    if not json_data:
        return bad_request('You must post Json data')

    message = {} # 设置错误消息
    if 'username' not in json_data or not json_data.get('username',None):
        message['username'] = 'Please provide a username.'
    # 邮箱正则匹配
    pattern = '^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$'
    if 'email' not in json_data or not re.match(pattern,json_data.get('email',None)):
        message['email'] = 'please provide a email address'

    if 'password' not in json_data or not json_data.get('password',None):
        message['password'] = 'Please provide a valid password.'

    if User.query.filter_by(username=json_data.get('username',None)).first():
        message['username'] = 'Please use a different username.'

    if User.query.filter_by(email = json_data.get('email',None)).first():
        message['email'] = 'Please use a different email address.'

    # 返回错误消息
    if message:
        return bad_request(message)

    user = User()
    user.from_dict(data=json_data,new_user=True) #注册用户数据

    db.session.add(user)
    db.session.commit() # 保存至数据库

    response = jsonify(user.to_dict())
    response.status_code = 201
    # HTTP协议要求201响应包含一个值为新资源URL的Location头部
    response.headers['Location'] = url_for('api.get_user',id=user.id)

    return response


@bp.route('/users',methods=['GET'])
@token_auth.login_required
def get_users():
    """返回所有用户的集合"""
    page = request.args.get('page',1,type=int)
    # 最多返回100条数据
    per_page = min(request.args.get('per_page', 10, type=int), 100)

    data = User.to_collection_dict(User.query,page,per_page,'api.get_users')
    return jsonify(data)

@bp.route('/users/<int:id>',methods=['GET'])
@token_auth.login_required
def get_user(id):
    '''返回一个用户'''
    return jsonify(User.query.get_or_404(id).to_dict())

@bp.route('/users/<int:id>',methods=['PUT'])
@token_auth.login_required
def update_user(id):
    """修改单个用户"""
    user = User.query.get_or_404(id)
    json_data = request.json

    if not json_data:
        return bad_request('you must Post a data')

    message = dict()

    if 'username' in json_data and not json_data.get('username',None):
        message['username'] = 'Please provide a valid username.'

    pattern = re.compile('^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$')

    if 'email' in json_data and not re.match(pattern,json_data.get('email',None)):
        message['email'] = 'Please provide a valid email address'

    if 'username' in json_data and json_data['username']!=user.username and \
    User.query.filter_by(username=json_data.get('username',None)).first():
        message['username'] = 'Please provide a different username'

    if 'email' in json_data and json_data['email']!=user.email and \
            User.query.filter_by(email=json_data.get('email',None)).first():
        message['username'] = 'Please provide a different username'

    if message: # 返回错误信息
        return bad_request(message)

    # 修改模型属性并提交
    user.from_dict(data=json_data)
    db.session.commit()

    return jsonify(user.to_dict())

@bp.route('/users/<int:id>',methods=['DELETE'])
def delete_user(id):
    """修改单个用户"""
    pass