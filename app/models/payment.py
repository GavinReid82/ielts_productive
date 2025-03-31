from app.extensions import db

class Payment(db.Model):
    __tablename__ = 'payments'

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