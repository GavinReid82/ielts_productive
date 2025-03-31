import pytest
from datetime import datetime, UTC
from app import create_app, db
from app.models import DemoAnalytics
from app.routes.analytics import track_demo_view
from app.config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_track_demo_view(app):
    """Test that demo view tracking works correctly"""
    with app.test_client() as client:
        # Test data
        test_data = {
            'page': '/',
            'timestamp': datetime.now(UTC).isoformat(),
            'sections_viewed': ['register', 'try_it_out'],
            'session_duration': 120
        }
        
        # Send POST request
        response = client.post('/track-demo-view', 
                             json=test_data,
                             headers={'Content-Type': 'application/json'})
        
        # Check response
        assert response.status_code == 200
        assert response.json['status'] == 'success'
        
        # Verify data was saved
        with app.app_context():
            analytics = DemoAnalytics.query.first()
            assert analytics is not None
            assert analytics.page == test_data['page']
            assert analytics.sections_viewed == test_data['sections_viewed']
            assert analytics.session_duration == test_data['session_duration']

def test_track_demo_view_with_headers(app):
    """Test that demo view tracking captures headers correctly"""
    with app.test_client() as client:
        # Test data with headers
        test_data = {
            'page': '/',
            'timestamp': datetime.now(UTC).isoformat(),
            'sections_viewed': [],
            'session_duration': 0
        }
        
        # Send POST request with headers
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://google.com'
        }
        
        response = client.post('/track-demo-view', 
                             json=test_data,
                             headers=headers)
        
        # Check response
        assert response.status_code == 200
        
        # Verify headers were captured
        with app.app_context():
            analytics = DemoAnalytics.query.first()
            assert analytics is not None
            assert 'Macintosh' in analytics.user_agent
            assert analytics.referrer == 'https://google.com'

def test_track_demo_view_with_ip(app):
    """Test that demo view tracking captures IP and country"""
    with app.test_client() as client:
        # Test data
        test_data = {
            'page': '/',
            'timestamp': datetime.now(UTC).isoformat(),
            'sections_viewed': [],
            'session_duration': 0
        }
        
        # Send POST request with IP
        headers = {
            'Content-Type': 'application/json',
            'X-Forwarded-For': '8.8.8.8'  # Google's DNS IP
        }
        
        response = client.post('/track-demo-view', 
                             json=test_data,
                             headers=headers)
        
        # Check response
        assert response.status_code == 200
        
        # Verify IP was captured
        with app.app_context():
            analytics = DemoAnalytics.query.first()
            assert analytics is not None
            assert analytics.ip_address == '8.8.8.8'
            # Note: Country detection requires GeoIP database to be present
            # assert analytics.country == 'US'  # Uncomment if GeoIP is set up

def test_track_demo_view_invalid_data(app):
    """Test that demo view tracking handles invalid data gracefully"""
    with app.test_client() as client:
        # Invalid test data
        test_data = {
            'invalid_field': 'test'
        }
        
        # Send POST request
        response = client.post('/track-demo-view', 
                             json=test_data,
                             headers={'Content-Type': 'application/json'})
        
        # Check response
        assert response.status_code == 400
        assert response.json['status'] == 'error' 