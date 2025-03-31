from flask import Flask, redirect, url_for, render_template, request
from flask_mail import Mail
from flask_session import Session
from app.config import Config
from app.extensions import db, login_manager
from app.models import User, Task
from flask_migrate import Migrate
from flask_login import current_user, login_required
import logging
from app.routes.analytics import analytics_bp

mail = Mail()
migrate = Migrate()
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    app = Flask(__name__)
    
    # Configure the app
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    Session(app)
    
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
    
    return app

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
