from app.extensions import db

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    is_available = db.Column(db.Boolean, default=False)
    type = db.Column(db.String(50))
    is_free = db.Column(db.Boolean, default=False)
    price = db.Column(db.Integer, nullable=True)
    main_prompt = db.Column(db.String(500))
    bullet_points = db.Column(db.String(500), nullable=True)
    image_path = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    language_inputs = db.Column(db.JSON, nullable=True)  # Store language examples
    practice_questions = db.Column(db.JSON, nullable=True)  # Store practice questions

    # Establish relationships
    payments = db.relationship('Payment', back_populates='task')

    def __repr__(self):
        return f'<Task {self.name}>' 