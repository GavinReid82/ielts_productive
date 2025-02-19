import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    SQLALCHEMY_DATABASE_URI = 'postgresql://gavinreid@localhost/ielts_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ✅ Ensure UPLOAD_FOLDER is defined
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')