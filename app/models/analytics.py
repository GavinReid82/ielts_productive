from app.extensions import db
from datetime import datetime

class DemoAnalytics(db.Model):
    __tablename__ = 'demo_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    session_duration = db.Column(db.Integer, nullable=True)  # Duration in seconds
    sections_viewed = db.Column(db.JSON, nullable=True)  # Track which sections were viewed
    is_landing_page = db.Column(db.Boolean, default=False)  # Track if this is a landing page visit
    converted_to_signup = db.Column(db.Boolean, default=False)  # Track if visitor later signed up
    referrer = db.Column(db.String(500), nullable=True)  # Track where they came from
    device_type = db.Column(db.String(50), nullable=True)  # Track device type (mobile/desktop)
    browser = db.Column(db.String(50), nullable=True)  # Track browser type
    
    def __repr__(self):
        return f"<DemoAnalytics {self.page} at {self.timestamp}>" 