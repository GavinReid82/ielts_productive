from flask import Blueprint

writing_bp = Blueprint('writing', __name__, template_folder='templates')

from app.blueprints.writing import routes
