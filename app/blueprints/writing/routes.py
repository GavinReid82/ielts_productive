from flask_login import current_user
from app.models import db, Transcript, Task, UserTask
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

@writing_bp.route('/writing_tips')
def writing_tips():
    return render_template('writing/writing_tips.html')

@writing_bp.route('/writing_general_task_1_letter')
def writing_general_task_1_letter():
    """Show the Writing Task 1 page with free and paid activities."""
    all_tasks = Task.query.filter_by(type='writing_general_task_1_letter').all()
    purchased_tasks = UserTask.query.filter_by(user_id=current_user.id).all()
    purchased_task_ids = [p.task_id for p in purchased_tasks]  # Get IDs of purchased tasks

    free_tasks = [task for task in all_tasks if task.is_free]
    paid_tasks = [task for task in all_tasks if not task.is_free]

    return render_template(
        'writing/writing_general_task_1_letter.html',
        free_tasks=free_tasks,
        paid_tasks=paid_tasks,
        purchased_task_ids=purchased_task_ids
    )


@writing_bp.route('/task_1_letter_1')
def task_1_letter_1():
    return render_template('writing/general_task_1/task_1_letter_1.html')

@writing_bp.route('/task_1_letter_2')
def task_1_letter_2():
    """Show paid activity 2 if user has purchased it."""
    task = Task.query.filter_by(name="Describe a time when you were really close to a wild animal.").first()
    if not task or task.id not in [p.task_id for p in UserTask.query.filter_by(user_id=current_user.id).all()]:
        return redirect(url_for('writing_general_task_1_letter'))

    return render_template('writing/general_task_1/task_1_letter_2.html')

@writing_bp.route('/task_1_letter_3')
def task_1_letter_3():
    """Show paid activity 3 if user has purchased it."""
    task = Task.query.filter_by(name="Describe a difficult task that you completed at work/study that you felt proud of.").first()
    if not task or task.id not in [p.task_id for p in UserTask.query.filter_by(user_id=current_user.id).all()]:
        return redirect(url_for('writing_general_task_1_letter'))

    return render_template('writing/general_task_1/task_1_letter_3.html')

@writing_bp.route('/task_1_letter_4')
def task_1_letter_4():
    """Show paid activity 4 if user has purchased it."""
    task = Task.query.filter_by(name="Describe a time when you were really close to a wild animal.").first()
    if not task or task.id not in [p.task_id for p in UserTask.query.filter_by(user_id=current_user.id).all()]:
        return redirect(url_for('writing_general_task_1_letter'))

    return render_template('writing/general_task_1/task_1_letter_4.html')

@writing_bp.route('/task_1_letter_5')
def task_1_letter_5():
    """Show paid activity 5 if user has purchased it."""
    task = Task.query.filter_by(name="Describe a difficult task that you completed at work/study that you felt proud of.").first()
    if not task or task.id not in [p.task_id for p in UserTask.query.filter_by(user_id=current_user.id).all()]:
        return redirect(url_for('writing_general_task_1_letter'))

    return render_template('writing/general_task_1/task_1_letter_5.html')

@writing_bp.route('/task_1_letter_6')
def task_1_letter_6():
    """Show paid activity 6 if user has purchased it."""
    task = Task.query.filter_by(name="Describe a difficult task that you completed at work/study that you felt proud of.").first()
    if not task or task.id not in [p.task_id for p in UserTask.query.filter_by(user_id=current_user.id).all()]:
        return redirect(url_for('writing_general_task_1_letter'))

    return render_template('writing/general_task_1/task_1_letter_6.html')

@writing_bp.route('/task_1_letter_7')
def task_1_letter_7():
    """Show paid activity 7 if user has purchased it."""
    task = Task.query.filter_by(name="Describe a difficult task that you completed at work/study that you felt proud of.").first()
    if not task or task.id not in [p.task_id for p in UserTask.query.filter_by(user_id=current_user.id).all()]:
        return redirect(url_for('writing_general_task_1_letter'))

    return render_template('writing/general_task_1/task_1_letter_7.html')

@writing_bp.route('/task_1_letter_8')
def task_1_letter_8():
    """Show paid activity 8 if user has purchased it."""
    task = Task.query.filter_by(name="Describe a difficult task that you completed at work/study that you felt proud of.").first()
    if not task or task.id not in [p.task_id for p in UserTask.query.filter_by(user_id=current_user.id).all()]:
        return redirect(url_for('writing_general_task_1_letter'))

    return render_template('writing/general_task_1/task_1_letter_8.html')

@writing_bp.route('/task_1_letter_9')
def task_1_letter_9():
    """Show paid activity 9 if user has purchased it."""
    task = Task.query.filter_by(name="Describe a difficult task that you completed at work/study that you felt proud of.").first()
    if not task or task.id not in [p.task_id for p in UserTask.query.filter_by(user_id=current_user.id).all()]:
        return redirect(url_for('writing_general_task_1_letter'))

    return render_template('writing/general_task_1/task_1_letter_9.html')   

@writing_bp.route('/task_1_letter_10')
def task_1_letter_10():
    """Show paid activity 10 if user has purchased it."""
    task = Task.query.filter_by(name="Describe a difficult task that you completed at work/study that you felt proud of.").first()
    if not task or task.id not in [p.task_id for p in UserTask.query.filter_by(user_id=current_user.id).all()]:
        return redirect(url_for('writing_general_task_1_letter'))

    return render_template('writing/general_task_1/task_1_letter_10.html')





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