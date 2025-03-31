from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_session import Session
import logging

mail = Mail()
db = SQLAlchemy()
login_manager = LoginManager()
logger = logging.getLogger(__name__)

session = Session()
