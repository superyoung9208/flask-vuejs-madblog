from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config



# Flask-SQLAlchemy plugin
db = SQLAlchemy()
# # Flask-Migrate plugin
migrate = Migrate()

# 再此处定义app的工厂方法,给flask_app添加功能
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    DEBUG = True
    # Enable CORS
    CORS(app)
    # Init Flask-SQLAlchemy
    db.init_app(app)
    # Init Flask-Migrate
    migrate.init_app(app, db)

    # 注册 blueprint
    from .api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app

from . import models