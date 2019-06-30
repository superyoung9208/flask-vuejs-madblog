from flask import g
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from app.models import User
from app.api.error import error_response


basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

@basic_auth.verify_password
def verify_password(username,password):
    '''用于检查用户提供的用户名和密码'''
    user = User.query.filter_by(username=username).first()
    if user is None:
        return False
    g.current_user = user
    return user.check_password(password)

@token_auth.verify_token
def verify_token(token):
    """检查token是否有效"""

    user = User.verify_token(token)
    g.current_user = user if user else None
    return g.current_user is not None


@basic_auth.error_handler
def basic_auth_error():
    """认证失败,并返回401信息"""
    return error_response(401)

@token_auth.error_handler
def token_auth_error():
    """token认证失败"""
    return error_response(401)