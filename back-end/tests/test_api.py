"""
File:test_api.py
Author:Young
"""
import json
from base64 import b64encode
from app.models import User
from . import TestConfig
import unittest,re
from app import create_app, db


class ApiTestCase(unittest.TestCase):
    """Api接口测试类"""

    def setUp(self):
        """每个测试开始前执行"""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()  # 获得应用上下文
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()  # flask测试客户端

    def tearDown(self):
        """每个测试结束后执行"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_404(self):
        """测试404处理"""
        response = self.client.get('/api/wrong/url')
        self.assertEqual(response.status_code, 404)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['error'], 'Not Found')

    def get_basic_auth_headers(self, username: str, password: str) -> dict:
        """创建basic认证的headers"""
        return {
            'Authorization': 'Basic ' + b64encode((username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def get_token_auth_headers(self, username, password):
        """创建Json web Token 认证的headers"""
        headers = self.get_basic_auth_headers(username, password)
        response = self.client.post('/api/tokens', headers=headers)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('token'))
        token = json_response.get('token')

        return {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def test_get_token(self):
        """测试用户登陆获取JWT"""
        # 创建用户
        u = User(username="laoyang123")
        u.password = "asdf456"
        db.session.add(u)
        db.session.commit()
        # 提交至数据库

        # 输入错误的用户密码
        headers = self.get_basic_auth_headers("laoyang123","123456")
        response = self.client.post('/api/tokens',headers=headers)
        self.assertEqual(response.status_code,401)

        # 输入正确的密码
        headers = self.get_basic_auth_headers('laoyang123', 'asdf456')
        response = self.client.post('/api/tokens', headers=headers)
        self.assertEqual(response.status_code,200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('token'))
        pat = re.compile(r'(.+)\.(.+)\.(.+)')
        self.assertTrue(pat.match(json_response['token']))

    def test_not_attach_jwt(self):
        """测试请求头中没有携带jwt的访问"""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code,401)

    def test_attach_jwt(self):
        """测试携带请求头的访问"""
        u = User(username = "laoyang555",email='john@163.com')
        u.password = "asdf456"
        db.session.add(u)
        db.session.commit()

        headers = self.get_token_auth_headers("laoyang555","asdf456")
        response = self.client.get("/api/users/",headers=headers)
        self.assertEqual(response.status_code,200)

    def test_anonymous(self):
        """测试不需要认证的接口"""
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code,200)