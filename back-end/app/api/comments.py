"""
File:comments.py
Author:Young
"""
from flask import current_app
from flask import g, jsonify
from flask import request
from flask import url_for

from app import db
from app.models import Comment, Post
from app.api.auth import token_auth
from app.api.error import bad_request, error_response
from . import bp

# 定义restful接口
# 发表评论 POST /api/comments/
# 获取评论 GET /api/comments/
# 获取一条评论 GET /api/comments/<id>
# 修改一个评论 PUT /api/comments/<id>
# 删除一个评论 DELETE /api/comments/<id>
# 点赞 GET /api/comments/<id>/like
# 取消点赞 GET /api/comments/<id>/unlike

@bp.route('/comments/',methods=["POST"])
@token_auth.login_required
def create_comment():
    """发布一条评论"""
    json_data = request.json
    if not json_data:
        return bad_request('You must post JSON data.')
    if 'body' not in json_data or not json_data.get('body').strip():
        return bad_request('Body is required.')
    if 'post_id' not in json_data or not json_data.get('post_id'):
        return bad_request('Post id is required.')

    post = Post.query.get_or_404(int(json_data.get('post_id')))

    comment = Comment()
    comment.from_dict(json_data)
    comment.author = g.current_user
    comment.post = post
    db.session.add(comment)
    db.session.commit()
    # 获取当前评论所有的祖先评论的作者
    users = set()
    users.add(comment.post.author)
    if comment.parent:
        ancestors_authors = {c.author for c in comment.get_ancestors()}
        users = users|ancestors_authors
    # 给所有的祖先评论作者发送通知
    for u in users:
        u.add_notification('unread_recived_comments_count',
                           u.new_recived_comments())
    db.session.commit()

    response = jsonify(comment.to_dict())
    response.status_code = 201

    # 201响应的请求头中要包含一个location
    response.headers['Location']= url_for('api.get_comment',id=comment.id)
    # 给用户发送新评论的通知
    post.author.add_notification('unread_recived_comments_count',post.author.new_recived_comments())
    return response

@bp.route('/comments/',methods=["GET"])
def get_comments():
    """获取所有评论"""
    page = request.args.get('page',1,type=int)
    per_page = min(request.args.get('per_page',current_app.config['COMMENTS_PER_PAGE'],type=int),100)
    data = Comment.to_collection_dict(Comment.query.order_by(Comment.timestamp.desc()),page,per_page,'api.get_comments',)
    return jsonify(data)

@bp.route('/comments/<int:id>',methods=["GET"])
def get_comment(id):
    """获取单个评论"""
    comment = Comment.query.get_or_404(id)
    return jsonify(comment.to_dict())

@bp.route('/comments/<int:id>',methods=["PUT"])
@token_auth.login_required
def update_comment(id):
    """修改单个评论"""
    comment = Comment.query.get_or_404(id)
    if g.current_user != comment.author and g.current_user != comment.post.author:
        return error_response(403)
    json_data = request.json
    if not json_data:
        return bad_request('You must post JSON data.')

    comment.from_dict(json_data)

    db.session.commit()
    return jsonify(comment.to_dict())

@bp.route('/comments/<int:id>',methods=["DELETE"])
@token_auth.login_required
def delete_comment(id):
    """删除单个评论"""
    comment = Comment.query.get_or_404(id)
    if g.current_user != comment.author and g.current_user != comment.post.author:
        return error_response(403)

    # 获取当前评论所有的祖先评论的作者
    users = set()
    users.add(comment.post.author)
    if comment.parent:
        ancestors_authors = {c.author for c in comment.get_ancestors()}
        users = users | ancestors_authors

    db.session.delete(comment)
    db.session.commit()

    # 给所有的祖先评论作者发送通知
    for u in users:
        u.add_notification('unread_recived_comments_count',
                           u.new_recived_comments())

    return '', 204

@bp.route('/comments/<int:id>/like',methods=["GET"])
@token_auth.login_required
def like_comment(id):
    """点赞一个评论"""
    comment = Comment.query.get_or_404(id)
    comment.liked_by(g.current_user)
    db.session.add(comment)
    db.session.commit()

    return jsonify({
        'status':'success',
        'message':'You are now liking comment [ id: %d ].' % id
    })

@bp.route('/comments/<int:id>/unlike',methods=["GET"])
@token_auth.login_required
def unlike_comment(id):
    """取消一个评论的点赞"""
    comment = Comment.query.get_or_404(id)
    comment.un_liked_by(g.current_user)
    db.session.add(comment)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'You are not liking comment [ id: %d ] anymore.' % id
    })