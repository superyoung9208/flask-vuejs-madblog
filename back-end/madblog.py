"""
File:madblog.py
Author:Young
"""
import os
import sys

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(basedir)

from app import create_app
from flask_script import Manager
from flask_migrate import MigrateCommand
from app.extensions import db
from app.models import User, Role, Notification, Message, Post, Comment, Permission

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Role': Role, 'User': User, 'Post': Post, 'Comment': Comment,
            'Notification': Notification, 'Message': Message,'Permission':Permission}

manager = Manager(app)
manager.add_command('db',MigrateCommand)


if __name__ == '__main__':
    manager.run()

