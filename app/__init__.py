from flask import Flask, redirect, url_for, render_template, request
from flask_mail import Mail
from flask_session import Session
from app.config import Config
from app.extensions import db, login_manager
from app.models import User, Task
from flask_migrate import Migrate
from flask_login import current_user, login_required
import logging

mail = Mail()

migrate = Migrate()
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    logger.info("Starting application creation...")
    app = Flask(__name__)
    
    # Add these debug lines temporarily
    logger.info(f"Mail Username: {config_class.MAIL_USERNAME}")
    logger.info("Mail Password present: " + ("Yes" if config_class.MAIL_PASSWORD else "No"))
    
    app.config["SESSION_TYPE"] = "filesystem"  # Ensure sessions are persisted
    app.config.from_object(config_class)
    Session(app)

    # Ensure Flask-Login redirects unauthorized users to the login page
    login_manager.login_view = "auth.login"

    # Mail configuration
    app.config['MAIL_SERVER'] = config_class.MAIL_SERVER
    app.config['MAIL_PORT'] = config_class.MAIL_PORT
    app.config['MAIL_USE_TLS'] = config_class.MAIL_USE_TLS
    app.config['MAIL_USERNAME'] = config_class.MAIL_USERNAME
    app.config['MAIL_PASSWORD'] = config_class.MAIL_PASSWORD
    
    mail.init_app(app)
    
    try:
        logger.info("Loading configuration...")
        app.config.from_object(Config)
        
        # Set file upload limit to 100MB
        app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
        app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
        
        logger.info("Initializing database...")
        db.init_app(app)
        
        logger.info("Initializing migrations...")
        migrate.init_app(app, db)
        
        logger.info("Initializing login manager...")
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        
        @app.route('/', endpoint='root')
        def index():
            """Root route handler"""
            print("Root route accessed!")
            logger.info("Root route accessed")
            
            if current_user.is_authenticated:
                print(f"User is authenticated: {current_user.id}")
                logger.info(f"User is authenticated: {current_user.id}")
                return redirect(url_for('writing.writing_home'))
            
            print("User is not authenticated, showing demo")
            logger.info("User is not authenticated, showing demo")
            
            # Get task #31 for the demo
            demo_task = Task.query.get(31)
            if not demo_task:
                print("Demo task not found!")
                logger.warning("Demo task not found")
                return render_template('landing/home.html')
            
            print(f"Found demo task: {demo_task.id}")
            logger.info(f"Found demo task: {demo_task.id}")
            
            # Render the lesson template instead of the task template
            return render_template(
                'writing/task_1_report_lessons.html',
                task=demo_task,
                is_demo=True
            )

        @app.before_request
        def log_request():
            print(f"\nRequest URL: {request.url}")
            print(f"Endpoint: {request.endpoint}")
            print(f"Method: {request.method}")
            print(f"Is authenticated: {current_user.is_authenticated if not current_user.is_anonymous else False}")

        # Now register blueprints AFTER defining root route
        logger.info("Registering blueprints...")
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

        logger.info("Application creation completed successfully")
        return app
        
    except Exception as e:
        logger.error(f"Error during application creation: {str(e)}", exc_info=True)
        raise

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {str(e)}")
        return None
