from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_session import Session
from flask.sessions import SessionInterface
import json
import logging

mail = Mail()

db = SQLAlchemy()
login_manager = LoginManager()
logger = logging.getLogger(__name__)

class CustomSessionInterface(SessionInterface):
    def get_signing_serializer(self, app):
        if not app.secret_key:
            return None
        return self.serializer_class(
            app.secret_key,
            salt=self.salt,
            serializer=self.serializer,
            signer_kwargs={'key_derivation': self.key_derivation}
        )

    def save_session(self, app, session, response):
        try:
            domain = self.get_cookie_domain(app)
            path = self.get_cookie_path(app)
            
            if not session:
                if session.modified:
                    response.delete_cookie(
                        app.config['SESSION_COOKIE_NAME'],
                        domain=domain,
                        path=path
                    )
                return

            httponly = self.get_cookie_httponly(app)
            secure = self.get_cookie_secure(app)
            samesite = self.get_cookie_samesite(app)
            expires = self.get_expiration_time(app, session)
            
            # Ensure session ID is a string
            session_id = session.sid
            if isinstance(session_id, bytes):
                try:
                    session_id = session_id.decode('utf-8')
                except UnicodeDecodeError:
                    logger.error("Failed to decode session ID from bytes")
                    return
            
            # Set cookie with string session ID
            response.set_cookie(
                app.config['SESSION_COOKIE_NAME'],
                session_id,
                expires=expires,
                httponly=httponly,
                domain=domain,
                path=path,
                secure=secure,
                samesite=samesite
            )
        except Exception as e:
            logger.error(f"Error saving session: {str(e)}", exc_info=True)
            # Don't raise the exception, just log it
            return

session = Session()
