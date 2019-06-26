import os
import sys

from app import create_app,db
from flask_script import Manager
from flask_migrate import MigrateCommand

from app.models import User

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

manager = Manager(app)
manager.add_command('db',MigrateCommand)


if __name__ == '__main__':
    manager.run()

