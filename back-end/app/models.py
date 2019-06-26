from . import db
from werkzeug.security import check_password_hash,generate_password_hash


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))  # 不保存原始密码

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