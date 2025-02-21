import os
from urllib.parse import urlparse, uses_netloc

class Config:
    WTF_CSRF_ENABLED = True
    FLASK_SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')

    DATABASE_URL = os.getenv('DATABASE_URL')  # Directly use Azure PostgreSQL URL

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/ielts_db'  # Fallback for local dev

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
