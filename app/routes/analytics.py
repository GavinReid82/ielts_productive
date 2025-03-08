from flask import Blueprint, request, jsonify, render_template
from app.extensions import db
from app.models import DemoAnalytics
from datetime import datetime
import json
from functools import wraps
from flask_login import current_user

analytics_bp = Blueprint('analytics', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

@analytics_bp.route('/track-demo-view', methods=['POST'])
def track_demo_view():
    try:
        data = request.get_json()
        
        # Create new analytics entry
        analytics = DemoAnalytics(
            page=data.get('page'),
            timestamp=datetime.fromisoformat(data.get('timestamp')),
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
            sections_viewed=data.get('sections_viewed', []),
            session_duration=data.get('session_duration')
        )
        
        db.session.add(analytics)
        db.session.commit()
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@analytics_bp.route('/admin/analytics', methods=['GET'])
@admin_required
def view_analytics():
    if request.headers.get('Accept') == 'application/json':
        # Return JSON data for AJAX requests
        analytics = DemoAnalytics.query.order_by(DemoAnalytics.timestamp.desc()).all()
        analytics_data = []
        for entry in analytics:
            analytics_data.append({
                'page': entry.page,
                'timestamp': entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'ip_address': entry.ip_address,
                'country': entry.country,
                'user_agent': entry.user_agent,
                'sections_viewed': entry.sections_viewed if entry.sections_viewed else [],
                'session_duration': entry.session_duration
            })
        return jsonify(analytics_data)
    
    # Render the template for normal page requests
    return render_template('admin/analytics.html') 