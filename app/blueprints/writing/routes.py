from flask_login import current_user
from app.models import db, Transcript, Task, Payment
from flask import Blueprint, render_template, request, url_for, redirect, flash, session
from app.blueprints.writing.utils import extract_writing_response, generate_writing_task_1_letter_feedback, save_writing_transcript
from openai import OpenAI
import json
import os
from app.blueprints.writing import writing_bp

writing_bp = Blueprint('writing', __name__, template_folder='templates')

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@writing_bp.route('/')
def writing_home():
    return render_template('writing/home.html')

@writing_bp.route('/view_task/<int:task_id>')
def view_task(task_id):
    """View a task that the user has paid for (if paid)"""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    # Check if the task is free or if the user has paid for it
    if task.is_free or Task.query.join(Payment).filter(Payment.user_id == current_user.id, Payment.task_id == task.id).first():
        # The user has paid or the task is free, allow access
        return render_template('view_task.html', task=task)
    else:
        # If the task is not free and the user has not paid
        return redirect(url_for('payments.checkout', task_id=task.id))


@writing_bp.route('/writing_tips')
def writing_tips():
    return render_template('writing/writing_tips.html')


@writing_bp.route('/writing_general_task_1_letter')
def writing_general_task_1_letter():
    """Show the Writing Task 1 page with all tasks available to the user."""
    all_tasks = Task.query.filter_by(type='writing_general_task_1_letter').all()

    # Fetch the user_id of the logged-in user
    user_id = current_user.id

    # Query the Payment table to find all the tasks purchased by the user
    purchased_tasks = Payment.query.filter_by(user_id=user_id).all()

    # Get task IDs from purchased tasks
    purchased_task_ids = [p.task_id for p in purchased_tasks]

    # Combine free tasks and purchased tasks into one list
    tasks_for_user = []
    for task in all_tasks:
        task_info = {
            'task': task,
            'is_purchased': task.id in purchased_task_ids or task.is_free,  # Check if task is free or purchased
            'is_free': task.is_free
        }
        tasks_for_user.append(task_info)

    return render_template(
        'writing/general_task_1.html',
        tasks_for_user=tasks_for_user
    )


@writing_bp.route('/writing_task_1_letter/<int:task_id>', methods=['GET'])
def writing_task_1_letter(task_id):
    task = Task.query.get_or_404(task_id)
    bullet_points = task.bullet_points.split(',')  # Assuming bullet points are stored as a comma-separated string
    return render_template('writing/writing_task_1_letter_template.html', task=task, bullet_points=bullet_points)




@writing_bp.route('/writing_task_2_essay')
def writing_task_2_essay():
    return render_template('writing/writing_task_2_essay.html')

@writing_bp.route('/writing_task_2_report')
def writing_task_2_report():
    return render_template('writing/writing_task_2_report.html')

@writing_bp.route('/writing_task_1_letter_submit', methods=['POST'])
def writing_task_1_letter_submit():
    user_id = session.get('user_id')
    if not user_id:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for('auth.login'))
    
     # ✅ Extract the writing response
    response = extract_writing_response(request)

    # ✅ Generate AI feedback
    feedback = generate_writing_task_1_letter_feedback(response)

    # ✅ Save the transcript to the database
    save_writing_transcript(current_user.id, response, feedback)

    # ✅ Store feedback in session
    session['feedback'] = {
    'response': response,
    'task_achievement': feedback.get('task_achievement', ''),
    'coherence_cohesion': feedback.get('coherence_cohesion', ''),
    'lexical_resource': feedback.get('lexical_resource', ''),
    'grammatical_range_accuracy': feedback.get('grammatical_range_accuracy', ''),
    'band_scores': feedback.get('band_scores', {
        'task_achievement': 0, 
        'coherence_cohesion': 0, 
        'lexical_resource': 0, 
        'grammatical_range_accuracy': 0, 
        'overall_band': 0
    }),
    'improved_response': feedback.get('improved_response', 'No improved response generated.')
    }

    return redirect(url_for('writing.writing_task_1_feedback'))  # ✅ Redirect instead of rendering directly


@writing_bp.route('/writing_task_1_feedback', methods=['GET'])
def writing_task_1_feedback():
    """Retrieve stored feedback from session and display it."""
    feedback = session.get('feedback', {})

    return render_template(
        'writing/writing_task_1_feedback.html',
        response=feedback.get('response', 'No response available.'),
        task_achievement=feedback.get('task_achievement', 'No feedback available.'),
        coherence_cohesion=feedback.get('coherence_cohesion', 'No feedback available.'),
        lexical_resource=feedback.get('lexical_resource', 'No feedback available.'),
        grammatical_range_accuracy=feedback.get('grammatical_range_accuracy', 'No feedback available.'),
        band_scores=feedback.get('band_scores', {'task_achievement': 0, 'coherence_cohesion': 0, 'lexical_resource': 0, 'grammatical_range_accuracy': 0, 'overall_band': 0}),
        improved_response=feedback.get('improved_response', 'No improved response generated.')
    )