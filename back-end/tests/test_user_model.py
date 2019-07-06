"""
File:test_user_model.py
Author:Young
"""
import unittest
from app import create_app, db
from app.models import User
from tests import TestConfig


class UserModelTestCase(unittest.TestCase):
    """用户模型测试类"""
    def setUp(self):
        """每个测试用例执行前启动"""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """测试用例执行完毕后启动"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        """测试设置密码"""
        u = User(username='john')
        u.password = 'pass1234'
        self.assertTrue(u.check_password('pass1234'))
        self.assertFalse(u.check_password('123456'))

    def test_avatar(self):
        """测试头像"""
        u = User(username='john', email='john@163.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/'
                                         '5ad2197b80f2010461c700d80fd35e9d'
                                         '?d=identicon&s=128'))