from app import create_app
from app.models import db, User, Task, UserTask

app = create_app()
with app.app_context():
    user = User.query.filter_by(email="test@example.com").first()
    task = Task.query.filter_by(name="Speaking Task 1").first()

    if user and task:
        completion = UserTask(user_id=user.id, task_id=task.id)
        db.session.add(completion)
        db.session.commit()
        print(f"✅ Task '{task.name}' marked as completed for {user.email}")


if __name__ == "__main__":
    app.run(debug=True)
