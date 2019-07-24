"""
File:app/__init__.py
Author:Young
"""
import rq
import rq_dashboard
from flask import Flask
from redis import Redis

from app.extensions import db, migrate, cors, mail
from config import Config
from app.api import bp as api_bp


def create_app(config_class=Config):
    """定义app的工厂方法, 给flask_app添加功能"""
    app = Flask(__name__)
    configure_app(app, config_class)
    configure_blueprints(app)
    configure_extensions(app)

    return app


def configure_app(app, config_class):
    """加载app配置"""
    app.config.from_object(config_class)
    app.url_map.strict_slashes = False
    # 整合rq任务队列
    app.redis = Redis.from_url(app.config["REDIS_URL"])
    app.task_queue = rq.Queue('madblog-tasks', connection=app.redis, default_timeout=3600)  # 设置任务队列中各任务的执行最大超时时间为 1 小时


def configure_blueprints(app):
    """注册蓝图"""
    app.register_blueprint(api_bp, url_prefix='/api')

    app.config.from_object(rq_dashboard.default_settings)
    app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")


def configure_extensions(app):
    """加载扩展"""
    db.init_app(app)
    migrate.init_app(app)
    cors.init_app(app)
    mail.init_app(app)
