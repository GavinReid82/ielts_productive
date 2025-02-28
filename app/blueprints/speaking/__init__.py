from flask import Blueprint

speaking_bp = Blueprint('speaking', __name__, template_folder='templates')

from app.blueprints.speaking import routes
