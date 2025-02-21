from flask import Flask
from app.config import Config
from app.extensions import db, login_manager
from app.models import User
from flask_migrate import Migrate  # ✅ Import Flask-Migrate
from app.blueprints.auth.routes import auth_bp
from app.blueprints.writing.routes import writing_bp
from app.blueprints.speaking.routes import speaking_bp
from app.blueprints.dashboard.routes import dashboard_bp
from app.blueprints.payments.routes import payments_bp 

migrate = Migrate()  # ✅ Initialize Flask-Migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Set file upload limit to 100MB
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

    # ✅ Ensure UPLOAD_FOLDER is properly set
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)  # ✅ Enable Flask-Migrate
    login_manager.init_app(app)  # ✅ Initialize Flask-Login
    login_manager.login_view = 'auth.login'  # Redirects unauthorized users

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(writing_bp, url_prefix='/writing')
    app.register_blueprint(speaking_bp, url_prefix='/speaking')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(payments_bp, url_prefix='/payments')

    return app

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login requires this function to load a user from the database."""
    return User.query.get(int(user_id))