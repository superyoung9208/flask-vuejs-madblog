"""
File:config.py
Author:Young
"""
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    """app配置类"""
    DEBUG = 1
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POSTS_PER_PAGE = 10
    USERS_PER_PAGE = 10
    COMMENTS_PER_PAGE = 10
    MESSAGES_PER_PAGE = 10