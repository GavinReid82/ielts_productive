from flask import Blueprint, render_template, redirect, url_for, flash, session,request
from flask_login import login_user, logout_user, login_required
from app.models import db, User
from app.blueprints.auth.forms import LoginForm, RegistrationForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            session['user_id'] = user.id  # ✅ Store user_id in session
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard.dashboard_home'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        login_user(user)  # ✅ Automatically log in the user
        session['user_id'] = user.id  # ✅ Store user_id in session after registration

        flash('Account created! You are now logged in.', 'success')
        return redirect(url_for('dashboard.dashboard_home'))  # ✅ Redirect to dashboard

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))
