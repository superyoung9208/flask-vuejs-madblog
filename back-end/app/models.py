import base64
import os
from datetime import datetime, timedelta
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

    token = db.Column(db.String(32),index=True,unique=True)
    token_expiration = db.Column(db.DateTime)

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
            '_links':{
                'self':url_for('api.get_user',id=self.id)
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

    def get_token(self,expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now+timedelta(seconds=60):
            return self.token
        # 生产随机的二进制token数据再进行decode解码
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = datetime.utcnow() + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        """取消token,设置token时间为当前时间-1秒"""
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            # token有效时间小于当前的时间
            return None
        return user