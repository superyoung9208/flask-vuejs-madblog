"""客户端申请 Token"""
from flask import g, jsonify
from flask import request

from app import db
from app.api.auth import basic_auth,token_auth
from . import bp

@bp.route("/tokens",methods=["POST"])
@basic_auth.login_required
def get_token():
    # 获取前端数据进行校验
    token = g.current_user.get_token()
    g.current_user.ping()
    db.session.commit()

    return jsonify({'token':token})

@bp.route("/tokens",methods=["DELETE"])
@token_auth.login_required
def del_token():
    g.current_user.revoke_token()
    db.session.commit()
    return "",204