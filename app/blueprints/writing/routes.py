from flask_login import current_user, login_required
from app.models import db, Transcript, Task, Payment
from flask import Blueprint, render_template, request, url_for, redirect, flash, session, jsonify
from app.blueprints.writing.utils import extract_writing_response, generate_writing_task_1_letter_feedback, generate_writing_task_1_report_feedback, generate_writing_task_2_feedback, save_writing_transcript
from openai import OpenAI
import json
import os
from app.blueprints.writing import writing_bp

writing_bp = Blueprint('writing', __name__, template_folder='templates')

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ------------------------------------------------------------
# Home
# ------------------------------------------------------------


@writing_bp.route('/')
def writing_home():
    """Landing page with regular writing home"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return render_template('writing/home.html')

# ------------------------------------------------------------
# Tips
# ------------------------------------------------------------


@writing_bp.route('/writing_tips')
@login_required
def writing_tips():
    return render_template('writing/writing_tips.html')


# ------------------------------------------------------------
# Task 1
# ------------------------------------------------------------
@writing_bp.route('/task-1-lesson/<int:lesson_id>')
def task_1_lesson(lesson_id):
    """Display the Task 1 lesson page"""
    # Get the corresponding task for this lesson
    task = Task.query.get_or_404(lesson_id)
    
    # Get the task type from the task object
    task_type = task.type
    
    # Render the generic lesson template
    return render_template('writing/task_1_report_lessons.html', 
                         task=task,
                         task_type=task_type)


@writing_bp.route('/view_task/<int:task_id>')
def view_task(task_id):
    """View a task that the user has paid for (if paid) or is being viewed as demo"""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    # Allow access if:
    # 1. It's a demo view
    # 2. The task is free
    # 3. The user is logged in and has paid
    is_demo = request.args.get('is_demo', False)
    if (is_demo or 
        task.is_free or 
        (current_user.is_authenticated and 
         Task.query.join(Payment).filter(Payment.user_id == current_user.id, Payment.task_id == task.id).first())):
        return render_template('writing/task_1_template.html', task=task, is_demo=is_demo)
    else:
        # If the task is not free and the user has not paid
        return redirect(url_for('auth.login'))


@writing_bp.route('/writing_task_1/<task_type>')
@login_required
def writing_task_1(task_type):
    """Show the Writing Task 1 page with tasks available to the user."""
    if task_type not in ['writing_task_1_letter', 'writing_task_1_report']:
        # Handle invalid task type (e.g., redirect or show an error)
        flash("Invalid task type", "danger")
        return redirect(url_for('writing.writing_task_1', task_type='writing_task_1_letter'))

    # Fetch tasks based on the task_type (either 'writing_task_1_letter' or 'writing_task_1_report')
    all_tasks = Task.query.filter_by(type=task_type).all()

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

    # Render the appropriate template (writing_task_1_letter_template or writing_task_1_report_template)
    return render_template(
        'writing/task_1_menu.html',
        tasks_for_user=tasks_for_user,
        task_type=task_type
    )


@writing_bp.route('/writing_task_1_submit', methods=['POST'])
@login_required
def writing_task_1_submit():
    user_id = session.get('user_id')
    if not user_id:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for('auth.login'))
    
    try:
        task_id = int(request.form.get('task_id'))
    except (TypeError, ValueError):
        flash("Invalid task ID.", "danger")
        return redirect(url_for('writing.writing_task_1', task_type='writing_task_1_letter'))
    
    if not task_id:
        flash("No task selected.", "danger")
        return redirect(url_for('writing.writing_task_1', task_type='writing_task_1_letter'))
    
    # Extract the writing response
    response = extract_writing_response(request)

    # Get the task details
    task = Task.query.get(task_id)
    if not task:
        flash("Task not found.", "danger")
        return redirect(url_for('writing.writing_task_1', task_type='writing_task_1_letter'))

    # Generate AI feedback
    # Choose the correct feedback function based on the task type
    if task.type.lower() == "writing_task_1_letter":
        feedback = generate_writing_task_1_letter_feedback(response, task_id)
    elif task.type.lower() == "writing_task_1_report":
        feedback = generate_writing_task_1_report_feedback(response, task_id)
    else:
        flash("Unknown task type.", "danger")
        return redirect(url_for('writing.writing_task_1', task_type='writing_task_1_letter'))
    
    # Save the transcript to the database
    save_writing_transcript(current_user.id, task_id, response, feedback)

    # Store feedback in session
    session['feedback'] = {
        'response': response,
        'task_id': task_id,
        'how_to_improve_language': feedback.get('how_to_improve_language', {
            'examples': [],
            'general_suggestions': []
        }),
        'how_to_improve_answer': feedback.get('how_to_improve_answer', {
            'examples': [],
            'general_suggestions': []
        }),
        'band_scores': feedback.get('band_scores', {
            'task_achievement': 0,
            'coherence_cohesion': 0,
            'lexical_resource': 0,
            'grammatical_range_accuracy': 0,
            'overall_band': 0
        }),
        'improved_response': feedback.get('improved_response', 'No improved response generated.')
    }

    return redirect(url_for('writing.writing_task_1_feedback'))


@writing_bp.route('/writing_task_1_feedback', methods=['GET'])
@login_required
def writing_task_1_feedback():
    """Retrieve stored feedback from session and display it."""
    feedback = session.get('feedback', {})
    task_id = feedback.get('task_id', 'No task ID available.')
    
    # Get the task type
    task = Task.query.get(task_id)
    task_type = task.type if task else None

    return render_template(
        'writing/task_1_feedback.html',
        task=task,
        task_id=task_id,
        type=task_type,
        response=feedback.get('response', 'No response available.'),
        how_to_improve_language=feedback.get('how_to_improve_language', {
            'examples': [],
            'general_suggestions': []
        }),
        how_to_improve_answer=feedback.get('how_to_improve_answer', {
            'examples': [],
            'general_suggestions': []
        }),
        band_scores=feedback.get('band_scores', {
            'task_achievement': 0,
            'coherence_cohesion': 0,
            'lexical_resource': 0,
            'grammatical_range_accuracy': 0,
            'overall_band': 0
        }),
        improved_response=feedback.get('improved_response', 'No improved response generated.')
    )


# ------------------------------------------------------------
# Task 2
# ------------------------------------------------------------

@writing_bp.route('/task-2-lesson/<int:lesson_id>')
def task_2_lesson(lesson_id):
    """Display the Task 2 lesson page"""
    task = Task.query.get_or_404(lesson_id)
    return render_template('writing/task_2_lessons.html', 
                         task=task,
                         task_type='writing_task_2')

@writing_bp.route('/view_task_2/<int:task_id>')
@login_required
def view_task_2(task_id):
    """View a task that the user has paid for (if paid)"""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    # Check if the task is free or if the user has paid for it
    if task.is_free or Task.query.join(Payment).filter(Payment.user_id == current_user.id, Payment.task_id == task.id).first():
        return render_template('writing/task_2_lessons.html', task=task)
    else:
        # If the task is not free and the user has not paid
        return redirect(url_for('payments.checkout', task_id=task.id))


@writing_bp.route('/writing_task_2')
@login_required
def writing_task_2():
    """Show the Writing Task 2 page with essay tasks available to the user."""
    all_tasks = Task.query.filter_by(type='writing_task_2').all()

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
        'writing/task_2_menu.html',
        tasks_for_user=tasks_for_user
    )


@writing_bp.route('/writing_task_2_submit', methods=['POST'])
@login_required
def writing_task_2_submit():
    """Submit the essay and generate feedback."""
    user_id = session.get('user_id')
    if not user_id:
        flash("Session expired. Please log in again.", "warning")
        return redirect(url_for('auth.login'))
    
    try:
        task_id = int(request.form.get('task_id'))
    except (TypeError, ValueError):
        flash("Invalid task ID.", "danger")
        return redirect(url_for('writing.writing_task_2'))
    
    if not task_id:
        flash("No task selected.", "danger")
        return redirect(url_for('writing.writing_task_2'))
    
    # Extract the essay response
    response = request.form.get('writingTask2')

    # Generate feedback using your AI model
    feedback = generate_writing_task_2_feedback(response, task_id)

    # Save the transcript to the database
    save_writing_transcript(user_id, task_id, response, feedback)

    # Store feedback in session
    session['feedback'] = {
        'response': response,
        
        'how_to_improve_language': feedback.get('how_to_improve_language', {
            'examples': [],
            'general_suggestions': []
        }),
        'how_to_improve_answer': feedback.get('how_to_improve_answer', {
            'examples': [],
            'general_suggestions': []
        }),
        'band_scores': feedback.get('band_scores', {
            'task_response': 0,
            'coherence_cohesion': 0,
            'lexical_resource': 0,
            'grammatical_range_accuracy': 0,
            'overall_band': 0
        }),
        'improved_response': feedback.get('improved_response', 'No improved response generated.')
    }

    return redirect(url_for('writing.writing_task_2_feedback'))


@writing_bp.route('/writing_task_2_feedback', methods=['GET'])
@login_required
def writing_task_2_feedback():
    """Retrieve stored feedback for Writing Task 2 and display it."""
    feedback = session.get('feedback', {})

    return render_template(
        'writing/task_2_feedback.html',
        response=feedback.get('response', 'No response available.'),
        how_to_improve_language=feedback.get('how_to_improve_language', {
            'examples': [],
            'general_suggestions': []
        }),
        how_to_improve_answer=feedback.get('how_to_improve_answer', {
            'examples': [],
            'general_suggestions': []
        }),
        band_scores=feedback.get('band_scores', {
            'task_response': feedback.get('band_scores', {}).get('task_response', 0),
            'coherence_cohesion': feedback.get('band_scores', {}).get('coherence_cohesion', 0),
            'lexical_resource': feedback.get('band_scores', {}).get('lexical_resource', 0),
            'grammatical_range_accuracy': feedback.get('band_scores', {}).get('grammatical_range_accuracy', 0),
            'overall_band': feedback.get('band_scores', {}).get('overall_band', 0)
        }),
        improved_response=feedback.get('improved_response', 'No improved response generated.')
    )