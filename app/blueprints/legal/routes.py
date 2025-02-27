from flask import Blueprint, render_template
from datetime import datetime

legal_bp = Blueprint('legal', __name__)

@legal_bp.route('/privacy')
def privacy_policy():
    return render_template('legal/privacy_policy.html', 
                         last_updated=datetime.now().strftime('%B %d, %Y'))

@legal_bp.route('/terms')
def terms():
    return render_template('legal/terms.html', 
                         last_updated=datetime.now().strftime('%B %d, %Y')) 