from flask import Blueprint

dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')

from app.blueprints.dashboard import routes
