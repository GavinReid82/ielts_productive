from flask import render_template, Blueprint
from flask_login import login_required
from app.blueprints.dashboard import dashboard_bp

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required  # ✅ Only logged-in users can access
def dashboard_home():
    return render_template('dashboard/home.html')

@dashboard_bp.route('/reading')
def reading():
    return render_template('reading/home.html')

@dashboard_bp.route('/writing')
def writing():
    return render_template('writing/home.html')

@dashboard_bp.route('/speaking')
def speaking():
    return render_template('speaking/home.html')

@dashboard_bp.route('/listening')
def listening():
    return render_template('listening/home.html')