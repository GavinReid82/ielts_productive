from flask import render_template, Blueprint
from flask_login import login_required, current_user
from app.models import Transcript
from app.blueprints.dashboard import dashboard_bp

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required  # ✅ Only logged-in users can access
def dashboard_home():
    return render_template('dashboard/home.html')

@dashboard_bp.route('/my-tasks')
@login_required
def my_tasks():
    # Get all transcripts for the current user, ordered by creation date
    transcripts = Transcript.query.filter_by(user_id=current_user.id).order_by(Transcript.created_at.desc()).all()
    return render_template('dashboard/my_tasks.html', transcripts=transcripts)

@dashboard_bp.route('/reading')
@login_required
def reading():
    return render_template('reading/home.html')

@dashboard_bp.route('/writing')
@login_required
def writing():
    return render_template('writing/home.html')

@dashboard_bp.route('/speaking')
@login_required
def speaking():
    return render_template('speaking/home.html')

@dashboard_bp.route('/listening')
@login_required
def listening():
    return render_template('listening/home.html')