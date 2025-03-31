import os
import logging
from app import create_app
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Determine environment
env = os.getenv('FLASK_ENV', 'production')
logger.info(f"Environment: {env}")

# Verify secret key
secret_key = os.getenv('FLASK_SECRET_KEY')
logger.info(f"FLASK_SECRET_KEY present: {bool(secret_key)}")
logger.info(f"FLASK_SECRET_KEY length: {len(secret_key) if secret_key else 0}")

# Create upload directory if it doesn't exist
upload_folder = os.path.join('/tmp', 'uploads')
os.makedirs(upload_folder, exist_ok=True)
logger.info(f"Upload folder configured: {upload_folder}")

# Create app
app = create_app()

try:
    logger.info("Starting application initialization...")
    
    # Log environment variables (excluding sensitive values)
    logger.info(f"Environment: {env}")
    logger.info(f"FLASK_SECRET_KEY present: {bool(secret_key)}")
    logger.info(f"FLASK_SECRET_KEY length: {len(secret_key) if secret_key else 0}")
    
    # Log configuration details
    logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'local'}")
    logger.info(f"Upload folder: {upload_folder}")
    logger.info(f"SECRET_KEY configured: {bool(app.config.get('SECRET_KEY'))}")
    logger.info(f"SECRET_KEY length: {len(app.config.get('SECRET_KEY', ''))}")
    logger.info(f"SESSION_TYPE: {app.config.get('SESSION_TYPE')}")
    
    if __name__ == '__main__':
        logger.info("Starting server on port 8000")
        app.run(host='0.0.0.0', port=8000)

except Exception as e:
    logger.error(f"Failed to start application: {str(e)}", exc_info=True)
    raise
