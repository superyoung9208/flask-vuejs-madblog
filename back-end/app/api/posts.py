"""
File:posts.py
Author:Young
"""
from flask import abort
from flask import g
from flask import request, jsonify
from flask import url_for

from app import db
from app.api.auth import token_auth
from app.api.error import bad_request, error_response
from app.models import Post
from . import bp

# RestfulApi 设计

# get api/posts 返回全部博客文章
# post api/posts 创建一篇博客
# get api/posts/<id> 返回一篇文章
# put api/posts/<id> 修改一篇文章
# delete api/posts/<id> 删除一篇博客

@bp.route('/posts',methods=["GET"])
def get_posts():
    """获取所有文章"""
    page = request.args('page',1,type=int)
    per_page = request.args('per_page',10,type=int)
    Post.to_collection_dict(Post.timestamp.desc(),page,per_page, 'api.get_posts')

@bp.route('/posts',methods=["POST"])
@token_auth.login_required
def create_post():
    """创建一篇文章"""
    json_data = request.json
    if not json_data:
        return bad_request('You must post Json data')
    message={}
    if 'title' not in json_data and not json_data.get('title'):
        message['title'] =  'Title is required.'
    elif len(json_data.get('title')) > 255:
        message['title'] = 'Title must less than 255 characters.'
    if 'body' not in json_data and not json_data.get('body'):
        message['body'] = 'Body is required'

    if message:
        return bad_request(message)

    # 构建post对象

    post = Post()
    post.from_dict(json_data)
    post.author = g.current_user  # 通过 auth.py 中 verify_token() 传递过来的（同一个request中，需要先进行 Token 认证）
    db.session.add(post)
    db.session.commit()
    response = jsonify(post.to_dict())
    response.status_code = 201
    # HTTP协议要求201响应包含一个值为新资源URL的Location头部
    response.headers['Location'] = url_for('api.get_post', id=post.id)
    return response

@bp.route('/posts/<int:id>',methods=["GET"])
def get_post(id):
    """获取一篇文章"""
    post = Post.query.get_or_404(id)
    if not post:
        abort(404)
    post.views += 1
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict())

@bp.route('/posts/<int:id>',methods=["PUT"])
@token_auth.login_required
def update_post(id):
    """更新一篇文章"""
    post = Post.query.get_or_404(id)
    if g.current_user.id != post.author_id:
        return error_response(403)
    json_data = request.json

    if not json_data:
        return bad_request("you must post Json data")
    message ={}
    if 'title' not in json_data and not json_data.get("title"):
        message["title"] = "title is required"
    elif len(json_data["title"]) > 255:
        message["title"] = "title must less than 255"
    if "body" not in json_data and not json_data.get("body"):
        message["body"] = "body is required"
    if message:
        return bad_request(message)

    post.from_dict(json_data)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict())

@bp.route('/posts/<int:id>',methods=["DELETE"])
@token_auth.login_required
def delete_post(id):
    """删除一篇文章"""
    post = Post.query.get_or_404(id)
    if post.id != g.current_user.id:
        return error_response(403)
    db.session.delete(post)
    db.session.commit()

    return "",204