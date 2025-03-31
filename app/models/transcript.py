from app.extensions import db
from datetime import datetime

class Transcript(db.Model):
    __tablename__ = 'transcripts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    transcription = db.Column(db.Text, nullable=False)
    feedback = db.Column(db.JSON, nullable=True)  # AI-generated feedback stored as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Add this line to establish the relationship with Task
    task = db.relationship('Task', backref='transcripts')

    def __repr__(self):
        return f"<Transcript User {self.user_id}, Task {self.task_id}>" 