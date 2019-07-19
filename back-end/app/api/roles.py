"""
File:roles.py
Author:laoyang
"""
from flask import current_app, jsonify
from flask import request
from flask import url_for

from app.extensions import db
from app.api.auth import token_auth
from app.api.error import bad_request
from app.models import Role
from utils.decorator import admin_required
from . import bp


@bp.router('/roles', methods=["GET"])
@token_auth.login_required
@admin_required
def get_roles():
    """获取全部角色的信息"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Role.to_collection_dict(Role.query, page, per_page, url_for('api.get_roles'))
    jsonify(data)


@bp.route('/roles', methods=["POST"])
@token_auth.login_required
@admin_required
def create_roles():
    """创建角色"""
    json_data = request.json
    if json_data is None:
        return bad_request('You must Post JSON data')

    # 校验数据
    message = {}
    if 'slug' not in json_data or not json_data.get('slug'):
        message['slug'] = 'Please provide a valid slug'
    if 'name' not in json_data or not json_data.get('name'):
        message['name'] = 'Please provide a valid name'
    if Role.query.filter_by(slug=json_data.get('slug', None)).first():
        message['slug'] = 'Please use a different slug.'

    if message:
        return bad_request(message)

    permission = 0

    for perm in json_data.get('permission', 0):
        permission += perm

    json_data['permission'] = permission

    role = Role()
    role.from_dict(json_data)

    db.session.add(role)
    db.session.commit()

    response = jsonify({role.to_dict()})

    response.status_code = 201
    response.headers['Location'] = url_for('api.get_roles', id=role.id)

    return response


@bp.route('/roles/<int:id>', methods=["PUT"])
@token_auth.login_required
@admin_required
def updata_role(id):
    """修改一个角色"""
    role = Role.query.get_or_404(id)
    json_data = request.json
    if not json_data:
        return bad_request("You must post a Json data")

    # 校验数据
    message = {}
    if 'slug' not in json_data or not json_data.get('slug'):
        message['slug'] = 'Please provide a valid slug'
    if 'name' not in json_data or not json_data.get('name'):
        message['name'] = 'Please provide a valid name'

    r = Role.query.filter_by(slug=json_data.get('slug', None)).first()

    if r and r.id != role.id:
        print(r.id)
        print(role.id)
        message['slug'] = 'Please use a different slug'
    if message:
        return bad_request(message)

    permission = 0

    for perm in json_data.get('permission', 0):
        permission += perm

    role.from_dict(json_data)
    db.session.commit()
    return jsonify(role.to_dict())



@bp.route('/roles/<int:id>', methods=["DELETE"])
@token_auth.login_required
@admin_required
def delete_role(id):
    """删除一个角色"""
    role = Role.query.get_or_404(id)
    db.session.delete(role)
    db.session.commit()
    return "",204