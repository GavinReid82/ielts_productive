import os
from urllib.parse import urlparse, uses_netloc

class Config:
    WTF_CSRF_ENABLED = True
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')

    # ✅ Ensure compatibility with PostgreSQL URLs in Heroku
    uses_netloc.append("postgres")
    DATABASE_URL = os.getenv('DATABASE_URL')

    if DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)  # Fix Heroku's old-style URL
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = 'postgresql://gavinreid@localhost/ielts_db'
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ✅ Ensure UPLOAD_FOLDER is defined
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')