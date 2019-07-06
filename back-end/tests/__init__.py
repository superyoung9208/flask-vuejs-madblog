"""
File:tests/__init__.py,
Author:laoyang
"""
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'