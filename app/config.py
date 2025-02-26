import os
from dotenv import load_dotenv
import logging

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

    # Ensure upload folder is writable
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/tmp/uploads')
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        logger.info(f"Created upload folder at {UPLOAD_FOLDER}")
    except Exception as e:
        logger.error(f"Failed to create upload folder: {str(e)}")
        UPLOAD_FOLDER = '/tmp'  # Fallback to /tmp if we can't create the folder
