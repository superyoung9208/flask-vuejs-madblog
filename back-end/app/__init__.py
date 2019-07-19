"""
File:app/__init__.py
Author:Young
"""
from flask import Flask
from app.extensions import db,migrate,cors, mail
from config import Config
from app.api import bp as api_bp


def create_app(config_class=Config):
    """定义app的工厂方法, 给flask_app添加功能"""
    app = Flask(__name__)
    configure_app(app,config_class)
    configure_blueprints(app)
    configure_extensions(app)

    return app

def configure_app(app,config_class):
    """加载app配置"""
    app.config.from_object(config_class)
    app.url_map.strict_slashes = False

def configure_blueprints(app):
    """注册蓝图"""
    app.register_blueprint(api_bp,url_prefix='/api')

def configure_extensions(app):
    """加载扩展"""
    db.init_app(app)
    migrate.init_app(app)
    cors.init_app(app)
    mail.init_app(app)