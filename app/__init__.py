from flask import Flask, redirect, url_for, render_template, request
from flask_mail import Mail
from flask_session import Session
from app.config import Config
from app.extensions import db, login_manager, session
from app.models import User, Task
from flask_migrate import Migrate
from flask_login import current_user, login_required
import logging
from app.routes.analytics import analytics_bp
import os
from flask_moment import Moment
from flask_bootstrap import Bootstrap
import redis

mail = Mail()
migrate = Migrate()
logger = logging.getLogger(__name__)
moment = Moment()
bootstrap = Bootstrap()

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # Add detailed startup logging
    logger.info("Starting application initialization...")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Environment variables loaded: {bool(os.getenv('FLASK_SECRET_KEY'))}")
    logger.info(f"Config class being used: {config_class.__name__}")
    
    try:
        # Configure the app
        app.config.from_object(config_class)
        
        # Ensure secret key is set
        if not app.config.get('SECRET_KEY'):
            logger.error("SECRET_KEY is not set in configuration!")
            raise RuntimeError("SECRET_KEY must be set in configuration")
        
        # Log configuration after loading
        logger.info(f"App configured with SECRET_KEY: {bool(app.config.get('SECRET_KEY'))}")
        logger.info(f"App configured with WTF_CSRF_ENABLED: {app.config.get('WTF_CSRF_ENABLED')}")
        
        # Initialize extensions
        db.init_app(app)
        migrate.init_app(app, db)
        mail.init_app(app)
        login_manager.init_app(app)
        moment.init_app(app)
        bootstrap.init_app(app)
        
        # Configure login manager
        login_manager.login_view = 'auth.login'
        
        # Session configuration
        if os.getenv('FLASK_ENV') == 'production':
            redis_url = os.getenv('REDIS_URL')
            if not redis_url:
                logger.error("REDIS_URL not set in production environment")
                raise RuntimeError("REDIS_URL must be set in production environment")
            
            try:
                # Test Redis connection
                redis_client = redis.from_url(redis_url, ssl=True)
                redis_client.ping()
                logger.info("Successfully connected to Redis")
                
                app.config['SESSION_TYPE'] = 'redis'
                app.config['SESSION_REDIS'] = redis_client
                app.config['SESSION_REDIS_SSL'] = True
                app.config['SESSION_REDIS_RETRY_ON_TIMEOUT'] = True
                app.config['SESSION_REDIS_RETRY_NUMBER'] = 3
                app.config['SESSION_REDIS_RETRY_DELAY'] = 0.1
                logger.info("Configured Redis session storage")
            except Exception as e:
                logger.error(f"Failed to configure Redis session storage: {str(e)}")
                raise RuntimeError("Failed to configure Redis session storage")
        else:
            app.config['SESSION_TYPE'] = 'filesystem'
            app.config['SESSION_FILE_DIR'] = os.path.join(app.root_path, 'flask_session')
            os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
            logger.info("Configured filesystem session storage")
        
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        
        # Initialize session
        session.init_app(app)
        
        # Register blueprints
        from app.blueprints.landing.routes import landing_bp
        from app.blueprints.auth.routes import auth_bp
        from app.blueprints.writing.routes import writing_bp
        from app.blueprints.speaking.routes import speaking_bp
        from app.blueprints.dashboard.routes import dashboard_bp
        from app.blueprints.payments.routes import payments_bp
        from app.blueprints.legal.routes import legal_bp
        
        app.register_blueprint(landing_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(writing_bp, url_prefix='/writing')
        app.register_blueprint(speaking_bp, url_prefix='/speaking')
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(payments_bp, url_prefix='/payments')
        app.register_blueprint(legal_bp, url_prefix='/legal')
        app.register_blueprint(analytics_bp)
        
        logger.info("Application initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
        raise
    
    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
