from flask import Blueprint, render_template, redirect, url_for, flash, session,request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User
from app.blueprints.auth.forms import LoginForm, RegistrationForm, RequestPasswordResetForm, ResetPasswordForm
from datetime import datetime, timedelta
import secrets
from flask_mail import Message
from app.extensions import mail
import logging

auth_bp = Blueprint('auth', __name__)

logger = logging.getLogger(__name__)


def send_verification_email(user):
    token = secrets.token_urlsafe(32)
    user.verification_token = token
    user.token_expiration = datetime.utcnow() + timedelta(hours=24)
    db.session.commit()
    
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    
    msg = Message('Verify Your Email',
                  sender='your-email@example.com',
                  recipients=[user.email])
    
    msg.body = f'''Please verify your email by clicking on the following link:
{verification_url}

This link will expire in 24 hours.

If you did not register for this account, please ignore this email.
'''
    
    mail.send(msg)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        logger.info(f"Login route accessed. Referrer: {request.referrer}")
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.dashboard_home'))
            
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and user.check_password(form.password.data):
                if not user.is_verified:
                    try:
                        session['unverified_email'] = str(user.email)  # Ensure string encoding
                    except Exception as e:
                        logger.error(f"Error setting unverified_email in session: {str(e)}")
                    flash('Please verify your email before logging in. Check your inbox for the verification link.', 'warning')
                    return render_template('auth/login.html', form=form)
                    
                try:
                    login_user(user)
                    session['user_id'] = str(user.id)  # Ensure string encoding
                    flash('Logged in successfully!', 'success')
                except Exception as e:
                    logger.error(f"Error during login process: {str(e)}", exc_info=True)
                    flash('An error occurred during login. Please try again.', 'danger')
                    return render_template('auth/login.html', form=form)
                
                # Get the next parameter from the URL
                next_page = request.args.get('next')
                
                # If there's no next parameter or it's the landing page,
                # redirect to dashboard instead
                if not next_page or 'landing' in next_page or next_page == '/':
                    return redirect(url_for('dashboard.dashboard_home'))
                    
                return redirect(next_page)
                
            else:
                flash('Invalid email or password.', 'danger')
        return render_template('auth/login.html', form=form)
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}", exc_info=True)
        flash('An error occurred during login. Please try again.', 'danger')
        return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_home'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered. Please login or use a different email.', 'danger')
            return redirect(url_for('auth.login'))

        user = User(email=form.email.data, is_verified=False)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # Send verification email
        send_verification_email(user)

        flash('Registration successful!', 'success')
        flash(f'A verification link has been sent to {user.email}. Please check your inbox and spam folder.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        flash('Invalid verification link.', 'danger')
        return redirect(url_for('auth.login'))
        
    if user.token_expiration < datetime.utcnow():
        flash('This verification link has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.login'))
        
    user.is_verified = True
    user.verification_token = None
    user.token_expiration = None
    db.session.commit()
    
    flash('Email verified successfully! You can now login.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/resend-verification')
def resend_verification():
    email = session.get('unverified_email')
    if not email:
        flash('Email address is required.', 'danger')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('If an account exists with that email, a verification link will be sent.', 'info')
        return redirect(url_for('auth.login'))
        
    if user.is_verified:
        flash('Your email is already verified. Please login.', 'info')
        return redirect(url_for('auth.login'))
        
    send_verification_email(user)
    flash('A new verification email has been sent. Please check your inbox.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        session.pop('user_id', None)
        session.clear()  # Clear all session data
        flash('Logged out successfully.', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.error(f"Error in logout route: {str(e)}", exc_info=True)
        flash('An error occurred during logout. Please try again.', 'danger')
        return redirect(url_for('auth.login'))



@auth_bp.route('/test-email')
def test_email():
    try:
        msg = Message('Test Email',
                    sender=current_app.config['MAIL_USERNAME'],
                    recipients=[current_app.config['MAIL_USERNAME']])  # sending to yourself
        msg.body = 'This is a test email to verify SMTP settings.'
        mail.send(msg)
        return 'Email sent successfully!'
    except Exception as e:
        print(f"Full error details: {str(e)}")  # This will show in your terminal
        return f'Error sending email: {str(e)}'

@auth_bp.route('/test-config')
def test_config():
    return {
        'MAIL_SERVER': current_app.config.get('MAIL_SERVER'),
        'MAIL_PORT': current_app.config.get('MAIL_PORT'),
        'MAIL_USE_TLS': current_app.config.get('MAIL_USE_TLS'),
        'MAIL_USERNAME': current_app.config.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': 'Present' if current_app.config.get('MAIL_PASSWORD') else 'Missing'
    }

def send_password_reset_email(user):
    token = user.get_reset_token()
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    msg = Message('Password Reset Request',
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[user.email])
    
    msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, simply ignore this email and no changes will be made.

This link will expire in 1 hour.
'''
    
    mail.send(msg)

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def request_reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_home'))
        
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('If an account exists with that email, you will receive instructions to reset your password.', 'info')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/request_reset_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_home'))
        
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired reset token', 'warning')
        return redirect(url_for('auth.request_reset_password'))
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', form=form)