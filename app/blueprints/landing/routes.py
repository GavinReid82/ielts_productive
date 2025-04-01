from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.models import Task
from app.blueprints.writing.utils import generate_writing_task_1_letter_feedback, generate_writing_task_1_report_feedback, generate_writing_task_2_feedback
import logging
from flask_login import current_user

logger = logging.getLogger(__name__)

landing_bp = Blueprint('landing', __name__)

@landing_bp.route('/')
def home():
    """Landing page route"""
    try:
        logger.info("Accessing landing page route")
        logger.info(f"User authenticated: {current_user.is_authenticated}")
        if current_user.is_authenticated:
            logger.info("User is authenticated, redirecting to writing home")
            return redirect(url_for('writing.writing_home'))
        
        # Get task #31 for the demo
        demo_task = Task.query.get(31)
        if not demo_task:
            logger.error("Demo task not found")
            return render_template('landing/home.html')
        
        logger.info("User is not authenticated, showing demo task")
        return render_template(
            'writing/task_1_report_lessons.html',
            task=demo_task,
            is_demo=True
        )
    except Exception as e:
        logger.error(f"Error in landing page route: {str(e)}", exc_info=True)
        raise

@landing_bp.route('/try-it-out/submit', methods=['POST'])
def try_it_out_submit():
    task_id = request.form.get('task_id')
    response = request.form.get('writingTask1')  # or writingTask2 depending on the task
    
    print(f"Task ID: {task_id}")  # Debug log
    print(f"Response: {response}")  # Debug log
    
    try:
        # Generate feedback using the appropriate function based on task type
        task = Task.query.get(task_id)
        if not task:
            raise ValueError("Task not found")

        if task.type == 'writing_task_1_report':
            feedback = generate_writing_task_1_report_feedback(response, task_id)
        elif task.type == 'writing_task_1_letter':
            feedback = generate_writing_task_1_letter_feedback(response, task_id)
        else:
            feedback = generate_writing_task_2_feedback(response, task_id)
        
        print(f"Generated feedback: {feedback}")  # Debug log
        
        # Store feedback in session
        session['feedback'] = {
            'response': response,
            'task': {
                'id': task.id,
                'type': task.type,
                'description': task.description,
                'main_prompt': task.main_prompt,
                'bullet_points': task.bullet_points
            },  # Convert task object to dict to avoid serialization issues
            'how_to_improve_language': feedback.get('how_to_improve_language', {
                'examples': [],
            }),
            'how_to_improve_answer': feedback.get('how_to_improve_answer', {
                'examples': [],
            }),
            'improved_response': feedback.get('improved_response', '')
        }
        
        print(f"Session feedback: {session['feedback']}")  # Debug log
        
    except Exception as e:
        logger.error(f"Error generating feedback: {str(e)}")
        session['feedback'] = {
            'response': response,
            'task': task,
            'error': str(e),
            'how_to_improve_language': {'examples': []},
            'how_to_improve_answer': {'examples': []},
            'improved_response': 'Error generating feedback.'
        }
    
    return redirect(url_for('landing.try_it_out_feedback'))

@landing_bp.route('/try-it-out/feedback')
def try_it_out_feedback():
    feedback = session.get('feedback', {})
    print(f"Feedback in feedback route: {feedback}")  # Debug log
    
    # Convert task dict back to Task object if needed
    task_data = feedback.get('task', {})
    if isinstance(task_data, dict):
        task = Task(
            id=task_data.get('id'),
            type=task_data.get('type'),
            description=task_data.get('description'),
            main_prompt=task_data.get('main_prompt'),
            bullet_points=task_data.get('bullet_points')
        )
    else:
        task = task_data

    return render_template('writing/task_1_feedback.html',
                         task=task,
                         response=feedback.get('response', ''),
                         how_to_improve_language=feedback.get('how_to_improve_language', {}),
                         how_to_improve_answer=feedback.get('how_to_improve_answer', {}),
                         improved_response=feedback.get('improved_response', ''),
                         is_demo=True)