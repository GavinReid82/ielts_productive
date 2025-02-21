from app.extensions import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    tasks_completed = db.relationship('UserTask', back_populates='user')  # ✅ Relationship with UserTask

    def set_password(self, password):
        """Hashes the password and stores it securely."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies a password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'speaking' or 'writing'
    is_free = db.Column(db.Boolean, default=False)  # ✅ NEW: Tracks if a task is free
    price = db.Column(db.Integer, nullable=True)  # ✅ NEW: Paid tasks have a price

    users_completed = db.relationship('UserTask', back_populates='task')

    def __repr__(self):
        return f"<Task {self.name} (Free: {self.is_free})>"


# ✅ Tracks which users completed which tasks
class UserTask(db.Model):
    __tablename__ = 'user_tasks'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), primary_key=True)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='tasks_completed')
    task = db.relationship('Task', back_populates='users_completed')

    def __repr__(self):
        return f"<UserTask User {self.user_id}, Task {self.task_id}>"


class Transcript(db.Model):
    __tablename__ = 'transcripts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    transcription = db.Column(db.Text, nullable=False)
    feedback = db.Column(db.JSON, nullable=True)  # AI-generated feedback stored as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Transcript User {self.user_id}, Task {self.task_id}>"
