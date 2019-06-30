import base64
import os
from _md5 import md5

from datetime import datetime, timedelta

import jwt
from flask import current_app
from flask import url_for

from . import db
from werkzeug.security import check_password_hash,generate_password_hash

class PaginatedAPIMixin(object):
    """用户扩展类"""

    # 根据传入的参数来进行所有用户的序列化操作
    @staticmethod
    def to_collection_dict(query,page,per_page,endpoint,**kwargs):
        resources = query.paginate(page,per_page,False)

        data = {
            'items':[item.to_dict() for item in resources.items],
            '_meta':{
                "page":page,
                "per_page":per_page,
                "total_pages":resources.pages,
                "total_items":resources.total,
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }

        return data



class User(PaginatedAPIMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))  # 不保存原始密码
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)


    def __repr__(self):
        return '<User {}>'.format(self.username)

    # 把调用方法装饰为属性
    @property
    def password(self):
        raise AttributeError("当前属性不允许读取")

    # 把设置属性的方法装饰为赋值
    @password.setter
    def password(self,value:str):
        self.password_hash = generate_password_hash(value)

    # 密码检查返回布尔类型
    def check_password(self,password:str) -> bool:
        return check_password_hash(self.password_hash,password)


    def to_dict(self,include_email=False):
        # 序列化抽象模型类
        data = {
            'id':self.id,
            'username':self.username,
            'email':self.email,
            'name':self.name,
            'location':self.location,
            'member_since': self.member_since.isoformat() + 'Z',
            'last_seen': self.last_seen.isoformat() + 'Z',
            '_links':{
                'self':url_for('api.get_user',id=self.id),
                'avatar':self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self,data,new_user=False):
        # 接收前段json数据并执行反序列化
        for field in ['username','email']:
            if field in data:
                setattr(self,field,data[field])
        if new_user and 'password' in data:
            self.password = data['password']

    def get_token(self,expires_in=600):
        # 获取当前时间
        now = datetime.utcnow()
        payload = {
            'user_id': self.id,
            'name': self.name if self.name else self.username,
            'exp': now + timedelta(seconds=expires_in),
            'iat': now
        }
        return jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    def ping(self):
        '''更新用户的最后访问时间'''
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    @staticmethod
    def verify_token(token):
        # 捕获异常信息
            # 解码jwt
        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms="HS256"
            )
        except (jwt.exceptions.ExpiredSignatureError, jwt.exceptions.InvalidSignatureError) as e:
            # Token过期，或被人修改，那么签名验证也会失败
            return None
        # 返回用户
        return User.query.get(payload.get('user_id'))

    def avatar(self,size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)