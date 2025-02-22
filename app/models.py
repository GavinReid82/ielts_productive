from app.extensions import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# User model
class User(db.Model, UserMixin):
    __tablename__ = 'users'  # Explicitly defining the table name

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Establish relationships
    payments = db.relationship('Payment', back_populates='user')

    def set_password(self, password):
        """Hashes the password and stores it securely."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies a password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"

# Task model
class Task(db.Model):
    __tablename__ = 'tasks'  # Explicitly defining the table name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    type = db.Column(db.String(50))
    is_free = db.Column(db.Boolean, default=False)
    price = db.Column(db.Integer, nullable=True)
    main_prompt = db.Column(db.String(500))
    bullet_points = db.Column(db.String(500), nullable=True)
    image_path = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)

    # Establish relationships
    payments = db.relationship('Payment', back_populates='task')

    def __repr__(self):
        return f'<Task {self.name}>'


# Payment model
class Payment(db.Model):
    __tablename__ = 'payments'  # Explicitly defining the table name

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    amount_paid = db.Column(db.Integer, nullable=False)
    payment_status = db.Column(db.String(50), nullable=False)

    # Establish relationships
    user = db.relationship('User', back_populates='payments')
    task = db.relationship('Task', back_populates='payments')

    def __repr__(self):
        return f"<Payment {self.id}, Task {self.task_id}, User {self.user_id}>"

# Transcript model
class Transcript(db.Model):
    __tablename__ = 'transcripts'  # Explicitly defining the table name

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    transcription = db.Column(db.Text, nullable=False)
    feedback = db.Column(db.JSON, nullable=True)  # AI-generated feedback stored as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Transcript User {self.user_id}, Task {self.task_id}>"
