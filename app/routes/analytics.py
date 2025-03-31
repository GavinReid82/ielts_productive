from flask import Blueprint, request, jsonify, render_template
from app.extensions import db
from app.models import DemoAnalytics, User
from datetime import datetime
import json
from functools import wraps
from flask_login import current_user
import geoip2.database
import os
import re

analytics_bp = Blueprint('analytics', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

def get_device_type(user_agent):
    """Determine device type from user agent string."""
    mobile_pattern = re.compile(r'Mobile|Android|iPhone|iPad|Windows Phone')
    if mobile_pattern.search(user_agent):
        return 'mobile'
    return 'desktop'

def get_browser(user_agent):
    """Determine browser type from user agent string."""
    if 'Chrome' in user_agent:
        return 'Chrome'
    elif 'Firefox' in user_agent:
        return 'Firefox'
    elif 'Safari' in user_agent:
        return 'Safari'
    elif 'Edge' in user_agent:
        return 'Edge'
    elif 'MSIE' in user_agent or 'Trident/' in user_agent:
        return 'Internet Explorer'
    return 'Other'

@analytics_bp.route('/track-demo-view', methods=['POST'])
def track_demo_view():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['page', 'timestamp', 'sections_viewed', 'session_duration']
        if not all(field in data for field in required_fields):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        # Get user agent and determine device/browser
        user_agent = request.headers.get('User-Agent', '')
        device_type = get_device_type(user_agent)
        browser = get_browser(user_agent)
        
        # Get country from IP address if GeoIP database is available
        country = None
        try:
            reader = geoip2.database.Reader('GeoLite2-Country.mmdb')
            response = reader.country(request.remote_addr)
            country = response.country.iso_code
        except:
            pass  # Silently fail if GeoIP lookup fails
        
        # Create analytics entry
        analytics = DemoAnalytics(
            page=data['page'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            sections_viewed=data['sections_viewed'],
            session_duration=data['session_duration'],
            ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
            user_agent=user_agent,
            country=country,
            referrer=request.headers.get('Referer'),
            device_type=device_type,
            browser=browser,
            is_landing_page=data['page'] == '/',  # Check if this is the landing page
            converted_to_signup=False  # This will be updated later if user signs up
        )
        
        # Save to database
        db.session.add(analytics)
        db.session.commit()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@analytics_bp.route('/admin/analytics', methods=['GET'])
@admin_required
def view_analytics():
    if request.headers.get('Accept') == 'application/json':
        # Get date range from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Base query
        query = DemoAnalytics.query
        
        # Apply date filters if provided
        if start_date:
            query = query.filter(DemoAnalytics.timestamp >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(DemoAnalytics.timestamp <= datetime.fromisoformat(end_date))
        
        # Get analytics data
        analytics = query.order_by(DemoAnalytics.timestamp.desc()).all()
        
        # Calculate summary statistics
        total_views = len(analytics)
        landing_page_views = len([a for a in analytics if a.is_landing_page])
        unique_countries = len(set(entry.country for entry in analytics if entry.country))
        avg_session_duration = sum(entry.session_duration or 0 for entry in analytics) / total_views if total_views > 0 else 0
        
        # Calculate conversion rate (visitors who later signed up)
        converted_visitors = len([a for a in analytics if a.converted_to_signup])
        conversion_rate = (converted_visitors / landing_page_views * 100) if landing_page_views > 0 else 0
        
        # Calculate device and browser statistics
        device_stats = {}
        browser_stats = {}
        for entry in analytics:
            device_stats[entry.device_type] = device_stats.get(entry.device_type, 0) + 1
            browser_stats[entry.browser] = browser_stats.get(entry.browser, 0) + 1
        
        analytics_data = {
            'entries': [{
                'page': entry.page,
                'timestamp': entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'ip_address': entry.ip_address,
                'country': entry.country,
                'user_agent': entry.user_agent,
                'sections_viewed': entry.sections_viewed if entry.sections_viewed else [],
                'session_duration': entry.session_duration,
                'is_landing_page': entry.is_landing_page,
                'converted_to_signup': entry.converted_to_signup,
                'referrer': entry.referrer,
                'device_type': entry.device_type,
                'browser': entry.browser
            } for entry in analytics],
            'summary': {
                'total_views': total_views,
                'landing_page_views': landing_page_views,
                'unique_countries': unique_countries,
                'avg_session_duration': round(avg_session_duration, 2),
                'conversion_rate': round(conversion_rate, 2),
                'device_stats': device_stats,
                'browser_stats': browser_stats
            }
        }
        
        return jsonify(analytics_data)
    
    # Render the template for normal page requests
    return render_template('admin/analytics.html') 