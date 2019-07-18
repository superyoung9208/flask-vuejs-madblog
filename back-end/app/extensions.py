"""
File:extensions.py
Author:laoyang
"""
''' Create instance of these flask extensions '''
from sqlalchemy import MetaData
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import MetaData
from flask_mail import Mail

# Flask-Cors plugin
cors = CORS()
# Flask-SQLAlchemy plugin
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
# Flask-Migrate plugin
migrate = Migrate(db=db)
# Flask-Mail plugin
mail = Mail()