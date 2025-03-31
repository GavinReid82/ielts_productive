# config in the muthafukin 2025
import os
from dotenv import load_dotenv
import logging
from datetime import timedelta

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class Config:
    WTF_CSRF_ENABLED = True
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')

    # Log environment variables (excluding sensitive data)
    logger.info(f"FLASK_SECRET_KEY set: {bool(os.getenv('FLASK_SECRET_KEY'))}")
    logger.info(f"STRIPE_SECRET_KEY set: {bool(os.getenv('STRIPE_SECRET_KEY'))}")
    logger.info(f"STRIPE_PUBLISHABLE_KEY set: {bool(os.getenv('STRIPE_PUBLISHABLE_KEY'))}")

    DATABASE_URL = os.getenv('DATABASE_URL')
    logger.info(f"Database URL set: {bool(DATABASE_URL)}")

    if DATABASE_URL:
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        logger.warning("No DATABASE_URL found, falling back to local database")
        SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/ielts_db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Ensure upload folder is writable
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        logger.info(f"Created upload folder at {UPLOAD_FOLDER}")
    except Exception as e:
        logger.error(f"Failed to create upload folder: {str(e)}")
        UPLOAD_FOLDER = '/tmp'  # Fallback to /tmp if we can't create the folder

    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Disable mail in tests
    MAIL_SERVER = None
    MAIL_PORT = None
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
