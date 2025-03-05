from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.models import Task
from app.blueprints.writing.utils import generate_writing_task_1_letter_feedback, generate_writing_task_1_report_feedback, generate_writing_task_2_feedback
import logging
from flask_login import current_user

logger = logging.getLogger(__name__)

landing_bp = Blueprint('landing', __name__, template_folder='templates')

@landing_bp.route('/try-it-out/submit', methods=['POST'])
def try_it_out_submit():
    task_id = request.form.get('task_id')
    response = request.form.get('writingTask1')  # or writingTask2 depending on the task
    
    # Generate feedback using the appropriate function based on task type
    task = Task.query.get(task_id)
    if task.type == 'writing_task_1_report':
        feedback = generate_writing_task_1_report_feedback(response, task_id)
    elif task.type == 'writing_task_1_letter':
        feedback = generate_writing_task_1_letter_feedback(response, task_id)
    else:
        feedback = generate_writing_task_2_feedback(response, task_id)
    
    # Store feedback in session
    session['feedback'] = {
        'response': response,
        'task': task,
        'how_to_improve_language': feedback.get('how_to_improve_language', {
            'examples': [],
        }),
        'how_to_improve_answer': feedback.get('how_to_improve_answer', {
            'examples': [],
        }),
        'improved_response': feedback.get('improved_response', '')
    }
    
    return redirect(url_for('landing.try_it_out_feedback'))

@landing_bp.route('/try-it-out/feedback')
def try_it_out_feedback():
    feedback = session.get('feedback', {})
    return render_template('writing/task_1_feedback.html',
                         task=feedback.get('task'),
                         response=feedback.get('response', ''),
                         how_to_improve_language=feedback.get('how_to_improve_language', {}),
                         how_to_improve_answer=feedback.get('how_to_improve_answer', {}),
                         improved_response=feedback.get('improved_response', ''),
                         is_demo=True)