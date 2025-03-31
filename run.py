from app import create_app
import logging
import os
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add file handler for Azure's log directory
log_dir = os.getenv('LOG_DIR', '/home/LogFiles')
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)
file_handler = RotatingFileHandler(
    os.path.join(log_dir, 'flask_app.log'),
    maxBytes=10240,
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

try:
    logger.info("Starting application initialization...")
    
    # Log environment variables (excluding sensitive values)
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'production')}")
    logger.info(f"FLASK_SECRET_KEY present: {bool(os.getenv('FLASK_SECRET_KEY'))}")
    logger.info(f"FLASK_SECRET_KEY length: {len(os.getenv('FLASK_SECRET_KEY', ''))}")
    
    # Create upload folder if it doesn't exist
    from app.config import Config
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    logger.info(f"Upload folder configured: {Config.UPLOAD_FOLDER}")
    
    # Create the application
    app = create_app()
    logger.info("Application created successfully")
    
    # Log configuration details
    logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI'].split('@')[1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else 'local'}")
    logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    logger.info(f"SECRET_KEY configured: {bool(app.config.get('SECRET_KEY'))}")
    logger.info(f"SECRET_KEY length: {len(app.config.get('SECRET_KEY', ''))}")
    logger.info(f"SESSION_TYPE: {app.config.get('SESSION_TYPE')}")
    
    if __name__ == '__main__':
        logger.info("Starting server on port 8000")
        app.run(host='0.0.0.0', port=8000)

except Exception as e:
    logger.error(f"Failed to start application: {str(e)}", exc_info=True)
    raise
