import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    WTF_CSRF_ENABLED = True
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')

    DATABASE_URL = os.getenv('DATABASE_URL')

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/ielts_db'  # Local fallback

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')

