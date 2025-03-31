from flask import Flask, redirect, url_for, render_template, request
from flask_mail import Mail
from flask_session import Session
from app.config import Config
from app.extensions import db, login_manager, CustomSessionInterface, session
from app.models import User, Task
from flask_migrate import Migrate
from flask_login import current_user, login_required
import logging
from app.routes.analytics import analytics_bp
import os

mail = Mail()
migrate = Migrate()
logger = logging.getLogger(__name__)

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
        
        # Configure session with simple settings
        session_dir = os.getenv('AZURE_LOCAL_STORAGE_PATH', '/tmp/flask_session')
        try:
            os.makedirs(session_dir, exist_ok=True)
            logger.info(f"Created session directory at {session_dir}")
        except Exception as e:
            logger.error(f"Failed to create session directory: {str(e)}")
            session_dir = '/tmp'  # Fallback to /tmp if we can't create the directory
        
        # Session configuration with better compatibility
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_USE_SIGNER'] = True
        app.config['SESSION_KEY_PREFIX'] = 'ielts_prod_'
        app.config['SESSION_FILE_DIR'] = session_dir
        app.config['SESSION_FILE_THRESHOLD'] = 100
        app.config['SESSION_FILE_MODE'] = 0o600
        
        # Cookie settings with better compatibility
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        app.config['SESSION_COOKIE_NAME'] = 'ielts_prod_session'
        app.config['SESSION_COOKIE_PATH'] = '/'
        
        # Additional session settings for better compatibility
        app.config['SESSION_REFRESH_EACH_REQUEST'] = True
        app.config['SESSION_COOKIE_MAX_AGE'] = 3600  # 1 hour
        app.config['SESSION_COOKIE_DOMAIN'] = None  # Let browser set domain
        app.config['SESSION_COOKIE_ENCODING'] = 'utf-8'  # Ensure proper string encoding
        app.config['SESSION_SERIALIZER'] = 'json'  # Use JSON serializer for better compatibility
        app.config['SESSION_USE_SIGNER'] = True  # Sign the session cookie
        app.config['SESSION_KEY_PREFIX'] = 'ielts_prod_'  # Prefix for session keys
        
        # Azure-specific settings
        if os.getenv('AZURE_WEBSITE_HOSTNAME'):
            app.config['SESSION_COOKIE_DOMAIN'] = os.getenv('AZURE_WEBSITE_HOSTNAME')
            logger.info(f"Setting session cookie domain to: {app.config['SESSION_COOKIE_DOMAIN']}")
        
        try:
            # Initialize session with custom interface
            app.session_interface = CustomSessionInterface()
            session.init_app(app)
            logger.info("Session initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize session: {str(e)}", exc_info=True)
            # Fallback to simple session if Flask-Session fails
            app.config['SESSION_TYPE'] = 'null'
            session.init_app(app)
            logger.warning("Using null session type as fallback")
        
        # Initialize login manager
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        
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
        
        # Root route
        @app.route('/', endpoint='root')
        def index():
            """Root route handler"""
            if current_user.is_authenticated:
                return redirect(url_for('writing.writing_home'))
            
            # Get task #31 for the demo
            demo_task = Task.query.get(31)
            if not demo_task:
                return render_template('landing/home.html')
            
            return render_template(
                'writing/task_1_report_lessons.html',
                task=demo_task,
                is_demo=True
            )
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
        raise
    
    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
