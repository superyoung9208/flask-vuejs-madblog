"""
File:models.py
Author:laoyang
"""
import base64
import json
from _md5 import md5

from datetime import datetime, timedelta
from time import time
import jwt
from flask import current_app
from flask import url_for

from app.extensions import db
from werkzeug.security import check_password_hash, generate_password_hash

followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('timestamp', db.DateTime, default=datetime.utcnow)
)


class PaginatedAPIMixin(object):
    """用户扩展类"""

    # 根据传入的参数来进行所有用户的序列化操作
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)

        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                "page": page,
                "per_page": per_page,
                "total_pages": resources.pages,
                "total_items": resources.total,
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


# 黑名单
blacklist = db.Table(
    'blacklist',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('block_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('timestamp', db.DateTime, default=datetime.utcnow())
)

# 喜欢文章
posts_likes = db.Table(
    'posts_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id')),
    db.Column('timestamp', db.DateTime, default=datetime.utcnow())
)


class Task(PaginatedAPIMixin, db.Model):
    """后台任务"""
    __tablename__ = 'tasks'
    id = db.Column(db.String(36), primary_key=True)  # 不适用数值id,而是使用rq为每个任务生成的字符串id
    # 任务名
    name = db.Column(db.String(128), index=True)
    # 任务描述
    description = db.Column(db.String(128))
    # 任务所属用户
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 是否执行完成
    complate = db.Column(db.Boolean, default=False)

    def get_progress(self):
        """获取实时进度"""
        try:
            rq_job = current_app.task_queue.fetch_job(self.id)
        except Exception as e:
            rq_job = None
        return rq_job.meta.get('progress', 0) if rq_job is not None else 100

    def to_dict(self):
        data = {
            'id':self.id,
            'name':self.name,
            'description':self.description,
            'progress':self.get_progress(),
            'complate':self.complate,
            '_links': url_for('api.get_user',id=self.user_id)
        }
        return data

    def __repr__(self):
        return '<Task {}>'.format(self.id)


class User(PaginatedAPIMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))  # 不保存原始密码
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    confirmed = db.Column(db.Boolean, default=False)  # 确认邮箱
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', cascade='all,delete-orphan', lazy='dynamic')
    last_recived_comments_read_time = db.Column(db.DateTime)  # 最后一次收到评论的时间
    # 用户最后一次查看 用户的粉丝 页面的时间，用来判断哪些粉丝是新的
    last_follows_read_time = db.Column(db.DateTime)
    # 用户最后一次查看 收到的点赞 页面的时间，用来判断哪些点赞是新的
    last_likes_read_time = db.Column(db.DateTime)
    # 用户最后一次查看 关注的人的博客 页面的时间，用来判断哪些文章是新的
    last_followeds_posts_read_time = db.Column(db.DateTime)
    # 用户最后一次查看 收到的文章被喜欢的时间,用来判断哪些喜欢是最新的
    last_posts_likes_read_time = db.Column(db.DateTime)
    last_messages_read_time = db.Column(db.DateTime)  # 最后一次读取私信时间
    # 用户的关注
    followeds = db.relationship('User', secondary=followers,
                                primaryjoin=(followers.c.follower_id == id),
                                secondaryjoin=(followers.c.followed_id == id),
                                backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    # 关联的通知
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all,delete-orphan')
    # 用户发送的私信
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id',
                                    backref='sender', lazy='dynamic', cascade='all,delete-orphan')
    # 用户接收的私信
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic', cascade='all,delete-orphan')
    # 骚扰者
    harassers = db.relationship('User', secondary=blacklist,
                                primaryjoin=(blacklist.c.user_id == id),
                                secondaryjoin=(blacklist.c.block_id == id),
                                backref=db.backref('sufferers', lazy='dynamic'), lazy='dynamic')
    # 用户的后台任务
    tasks = db.relationship('Task', backref='user', lazy='dynamic')

    def new_recived_messages(self) -> int:
        """最新未读的私信个数"""
        last_read_time = self.last_messages_read_time or datetime(1900, 0, 0)

        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()

    @property
    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.author_id).filter(
                followers.c.follower_id == self.id
            ))
        return followed.order_by(Post.timestamp.desc())

    def is_following(self, user) -> bool:
        """判断是否关注user对象"""
        return self.followeds.filter(
            followers.c.followed_id == user.id
        ).count() > 0

    def follow(self, user):
        """关注user对象"""
        if not self.is_following(user):
            self.followeds.append(user)

    def unfollow(self, user):
        """取消user对象的关注"""
        if self.is_following(user):
            self.followeds.remove(user)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    # 把调用方法装饰为属性
    @property
    def password(self):
        raise AttributeError("当前属性不允许读取")

    # 把设置属性的方法装饰为赋值
    @password.setter
    def password(self, value: str):
        self.password_hash = generate_password_hash(value)

    # 密码检查返回布尔类型
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_email=False):
        # 序列化抽象模型类
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'location': self.location,
            'member_since': self.member_since.isoformat() + 'Z',
            'last_seen': self.last_seen.isoformat() + 'Z',
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        # 接收前段json数据并执行反序列化
        for field in ['username', 'email', 'name', 'location', 'about_me']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.password = data['password']
            if self.role is None:
                if self.email in current_app.config['ADMINS']:
                    self.role = Role.query.filter_by(slug='administrator').first()
                else:
                    self.role = Role.query.filter_by(default=True).first()

    def get_token(self, expires_in=600):
        # 获取当前时间
        now = datetime.utcnow()
        payload = {
            'user_id': self.id,
            'user_name': self.name if self.name else self.username,
            'user_avatar': base64.b64encode(self.avatar(24).
                                            encode('utf-8')).decode('utf-8'),
            'confirmed': self.confirmed,
            'permissions': self.role.get_permissions(),
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

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def new_recived_comments(self):
        """用户下未读评论计数"""
        last_read_time = self.last_recived_comments_read_time or datetime(1900, 1, 1)
        # 用户发布的文章的id
        user_posts_ids = [post.id for post in self.posts.all()]
        q1 = set(Comment.query.fileter(Comment.post_id.in_(user_posts_ids), Comment.author == self))
        q2 = set()
        for c in self.comments:
            q2 = q2 | c.get_descendants()
        recived_comments = q1 | q2
        return len([c for c in recived_comments if c.timestamp > last_read_time])

    def new_recived_messages(self):
        """用户未读私信计数"""
        last_read_time = self.last_messages_read_time or datetime(1900, 0, 0)
        return Message.query.filter_by(Message.recipient == self).filter(Message.timestamp > last_read_time).count()

    def add_notification(self, name, data):
        """为用户添加一个通知"""
        self.notifications.filter(name == name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def new_follows(self):
        """新的粉丝记数"""
        last_read_time = self.last_follows_read_time or datetime(1900, 0, 0)
        return self.followers.filter(followers.c.timestamp > last_read_time).count()

    def new_likes(self):
        """用户收到的点赞数量"""
        last_read_time = self.last_likes_read_time or datetime(1900, 0, 0)
        comment = self.comments.join(comments_likes).all()
        news_likes_count = 0
        for c in comment:
            # 获取点赞时间
            for u in c.likes:
                res = db.engine.execute(
                    "select * from comments_likes where user_id={} and comment_id={}".format(u.id, c.id))
                timestapm = datetime.strptime(list(res)[0][2], '%Y-%m-%d %H:%M:%S.%f')
                if timestapm > last_read_time:
                    news_likes_count += 1
        return news_likes_count

    def new_posts_likes(self) -> int:
        """用户收到的文章被喜欢的计数"""
        last_read_time = self.last_posts_likes_read_time or datetime(1990, 0, 0)
        new_likes_count = 0
        # 查找到自己所有的被喜欢的文章
        posts = self.posts.join(posts_likes).all()
        for p in posts:
            for u in p.likes:
                if u != self:  # 用户自己喜欢的文章不用通知
                    res = db.engine.execute(
                        "select * from posts_likes WHERE user_id={} and post_id={}".format(u.id, p.id))
                    timestamp = datetime.strptime(list(res)[0][2], "%Y-%m-%d %H:%M:%S.%f")
                    if timestamp > last_read_time:
                        new_likes_count += 1

        return new_likes_count

    def new_follows(self):
        """关注者发布的文章记数"""
        last_read_time = self.last_followeds_posts_read_time or datetime(1900, 0, 0)
        return self.followed_posts().filter(Post.timestamp > last_read_time).count()

    def is_blocking(self, user) -> bool:
        """判断当前用户是否被拉黑"""
        return self.harassers.filter(blacklist.c.block_id == user.id).count() > 0

    def block(self, user):
        """当前用户拉黑一个用户"""
        if not self.is_blocking(user):
            self.harassers.append(user)

    def unblock(self, user):
        """解除拉黑一个用户"""
        if self.is_blocking(user):
            self.harassers.remove(user)

    def generate_confirmed_jwt(self, expires_in=3600):
        """生成验证token"""
        now = datetime.utcnow()
        payload = {
            "confirm": self.id,
            'exp': now + timedelta(seconds=expires_in),
            'iat': now
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    def verify_confirm_jwt(self, token):
        """验证邮箱token"""
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithm='HS256')
        except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError, jwt.exceptions.InvalidSignatureError):
            # 验证未通过,过期或者token被篡改
            return False
        if payload.get("confirm") != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_password_jwt(self, expires_in=3600):
        """
        生成重置密码的验证token
        :return jwttoken
        """
        now = datetime.utcnow()
        payload = {
            "reset_password": self.id,
            'exp': now + expires_in,
            'iat': now
        }
        return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm='HS256').decode('utf-8')

    def verify_reset_password_jwt(self, token):
        try:
            payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithm='HS256')
        except (jwt.exceptions.InvalidTokenError, jwt.exceptions.InvalidSignatureError,
                jwt.exceptions.ExpiredSignatureError) as e:
            return None

        return User.query.get(payload.get("reset_password"))

    def can(self, perm):
        """检查用户是否具有某个权限"""
        return self.role is not None and self.role.has_permission(perm)

    def is_administartor(self):
        """检查是否是管理员权限"""
        return self.can(Permission.ADMIN)

    def get_task_in_process(self, name):
        """获取正在运行的任务"""
        return Task.query.filter_by(name=name, user=self, compile=False)

    def lanuch_tasks(self, name, description, *args, **kwargs):
        """用户发布一个任务"""
        rq_job = current_app.task_queue.enqueue('app.utils.tasks.' + name, *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
        db.session.add()
        return task


class Post(PaginatedAPIMixin, db.Model):
    """文章模型类"""
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    summary = db.Column(db.Text)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime(), index=True, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade='all,delete-orphan')
    # 喜欢博客的人和被喜欢的文章是多对多的关系,一个人可以喜欢多个文章,一个文章可以被多个人喜欢
    likers = db.relationship('User', secondary=posts_likes, backref=db.backref('liked_posts', lazy='dynamic'),
                             lazy="dynamic")

    def __repr__(self):
        return "<POST{}>".format(self.title)

    def from_dict(self, data: dict):
        """接收表单数据构建post对象并返回"""
        for filed in ["title", "body", "summary"]:
            if filed in data:
                setattr(self, filed, data[filed])

    def to_dict(self):

        data = {
            'id': self.id,
            'title': self.title,
            'body': self.body,
            'summary': self.summary,
            'author_id': self.author_id,
            '_links': {
                'self': url_for('api.get_post', id=self.id),
                'author_url': url_for('api.get_users', id=self.author_id)
            }
        }

        return data

    def is_liked_by(self, user):
        """是否收藏过文章"""
        return user in self.likers

    def liked_by(self, user):
        """收藏文章"""
        if not self.is_liked_by(user):
            self.likers.append(user)

    def unliked_by(self, user):
        """取消收藏文章"""
        if self.is_liked_by(user):
            self.likers.remove(user)


# 评论点赞
comments_likes = db.Table(
    'comments_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('comments_id', db.Integer, db.ForeignKey('comments.id')),
    db.Column('timestamp', db.DateTime, default=datetime.utcnow)
)


class Comment(PaginatedAPIMixin, db.Model):
    """评论模型类"""
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.TEXT)
    timestamp = db.Column(db.DateTime, index=True)
    mark_read = db.Column(db.Boolean, default=False)  # 是否已读
    disabled = db.Column(db.Boolean, default=False)  # 屏蔽显示
    # 评论者的id
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 评论博文的id
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    # 父评论id
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id', ondelete='CASCADE'))
    parent = db.relationship('Comment', backref= \
        db.backref('children', cascade='all,delete-orphan'), remote_side=[id])
    likers = db.relationship('User', secondary=comments_likes, backref=db.backref('liked_comments', lazy='dynamic'))

    def __repr__(self):
        """控制台输出"""
        return "<Comment {}>".format(self.id)

    def get_descendants(self):
        '''获取一级评论的所有子孙'''
        data = set()

        def descendants(comment):
            if comment.children:
                data.update(comment.children)
                for child in comment.children:
                    descendants(child)

        descendants(self)
        return data

    def get_ancestors(self):
        """获取评论的所有爸爸们"""
        data = []

        def ancestors(comment):
            if comment.parent:
                data.append(comment.parent)
                ancestors(comment.parent)

        ancestors(self)
        return data

    def from_dict(self, data: dict):
        """填充数据至当前模型类"""
        for filed in ['body', 'timestamp', 'mark_read', 'disabled', 'post_id', 'parent_id']:
            setattr(self, filed, data[filed])

    def to_dict(self) -> dict:
        """序列化评论模型"""
        data = {
            'id': self.id,
            'body': self.body,
            'timestamp': self.timestamp,
            'mark_read': self.mark_read,
            'disabled': self.disabled,
            'author': {
                'id': self.author.id,
                'username': self.author.username,
                'name': self.author.name,
                'avatar': self.author.avatar(128)
            },
            'post': {
                'id': self.post.id,
                'title': self.post.title,
                'author_id': self.post.author.id
            },
            'parent_id': self.parent_id if self.parent else None,
            '_links': {
                'self': url_for('api.get_comment', id=self.id),
                'author_url': url_for('api.get_user', id=self.author_id),
                'post_url': url_for('api.get_post', id=self.post_id),
                'parent_url': url_for('api.get_comment', id=self.parent_id) if self.parent else None,
                'children_url': [url_for('api.get_comment', id=child.id) for child in
                                 self.children] if self.childeren else None
            }
        }

        return data

    def is_liked_by(self, user):
        """用户是否点赞"""
        return user in self.likers

    def liked_by(self, user):
        """点赞评论"""
        if not self.is_liked_by(user):
            self.likers.append(user)

    def un_liked_by(self, user):
        """取消点赞"""
        if self.is_liked_by(user):
            self.likers.remove(user)


class Notification(db.Model):
    """用户通知"""
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.Float, index=True, default=time)
    payload_json = db.Column(db.Text)

    def __repr__(self):
        return "<Notification {}>".format(self.id)

    def get_data(self):
        """加载payload数据"""
        return json.loads(str(self.payload_json))

    def to_dict(self):
        """序列化模型类数据"""
        data = {
            'id': self.id,
            'name': self.name,
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'name': self.user.name,
                'avatar': self.user.avatar(128)
            },
            'timestamp': self.timestamp,
            'payload': self.get_data(),
            '_links': {
                'self': url_for('api.get_notification', id=self.id),
                'user_url': url_for('api.get_user', id=self.user_id)
            }
        }

        return data

    def from_dict(self, data):
        """装载数据至模型类"""
        for field in ["name", "payload"]:
            if field in data:
                setattr(self, field, data[field])


class Message(PaginatedAPIMixin, db.Model):
    """用户私信"""
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return "<Message {}>".format(self.id)

    def to_dict(self):
        """序列化输出私信模型"""
        data = {
            'id': self.id,
            'body': self.body,
            'timestamp': self.timestamp if self.timestamp else datetime(1900, 0, 0),
            'sender': self.sender.to_dict(),
            'recipient': self.recipient.to_dict(),
            '_links': {
                'self': url_for('api.get_message', id=self.id),
                'sender_url': url_for('api.get_user', id=self.sender_id),
                'recipient_url': url_for('api.get_user', id=self.recipient_id),
            }
        }

        return data

    def from_dict(self, data: dict):
        """装载数据至私信模型"""
        for filed in ['body', 'timestamp']:
            if filed in data:
                setattr(self, filed, data[filed])


class Permission(object):
    """权限认证中的各种操作，对应二进制的位，比如
       FOLLOW: 0b00000001，转换为十六进制为 0x01
       COMMENT: 0b00000010，转换为十六进制为 0x02
       WRITE: 0b00000100，转换为十六进制为 0x04
       ...
       ADMIN: 0b10000000，转换为十六进制为 0x80

       中间还预留了第 4、5、6、7 共4位二进制位，以备后续增加操作权限"""
    FOLLOW = 0x01  # 关注权限
    COMMENT = 0x02  # 发布评论,点赞,权限
    WRITE = 0x04  # 撰写文章的权限
    ADMIN = 0x80  # 管理者权限


class Role(PaginatedAPIMixin, db.Model):
    """角色表"""
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))  # 角色表
    default = db.Column(db.Boolean, default=False, index=True)  # 是否是默认角色
    permissions = db.Column(db.Integer)  # 角色拥有的权限，各操作对应一个二进制位，能执行某项操作的角色，其位会被设为 1
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    @staticmethod
    def insert_roles():
        roles = {
            'shutup': ('小黑屋', ()),
            'reader': ('读者', (Permission.FOLLOW, Permission.COMMENT)),
            'author': ('作者', (Permission.FOLLOW, Permission.COMMENT, Permission.WRITE)),
            'administrator': ('管理员', (Permission.FOLLOW, Permission.COMMENT, Permission.WRITE, Permission.ADMIN))
        }
        default_role = 'reader'
        for r in roles:
            role = Role.query.filter_by(slug=r).first()
            if role is None:
                role = Role(slug=r, name=roles[r][0])
            role.reset_permission()
            for perm in roles[r][1]:
                role.add_permission(perm)
            role.default = (role.slug == default_role)
            db.session.add(role)
        db.session.commit()

    def reset_permission(self):
        """重置权限"""
        self.permissions = 0

    def has_permission(self, perm) -> bool:
        """是否存在此权限"""
        return self.permissions & perm == perm

    def add_permission(self, perm):
        """添加权限"""
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        """删除权限"""
        if self.has_permission(perm):
            self.permissions -= perm

    def get_permissions(self):
        """获取角色具体权限操作"""
        p = [(Permission.FOLLOW, 'follow'), (Permission.ADMIN, 'administrator'), (Permission.WRITE, 'author'),
             (Permission.COMMENT, 'reader')]

        new_p = (i[1] for i in p if self.has_permission(i[0]))
        return ",".join(new_p)

    def to_dict(self):
        """序列化输出"""
        data = {
            'id': self.id,
            'slug': self.slug,
            'name': self.name,
            'default': self.default,
            'permissions': self.permissions,
            '_links': {
                'self': url_for('api.get_role', id=self.id)
            }
        }
        return data

    def from_dict(self, data):
        for field in ['slug', 'name', 'permissions']:
            if field in data:
                setattr(self, field, data[field])

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Role {}>'.format(self.name)
