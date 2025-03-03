from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.models import Task
from app.blueprints.writing.utils import generate_writing_task_1_letter_feedback
import logging
from flask_login import current_user

logger = logging.getLogger(__name__)

landing_bp = Blueprint('landing', __name__, template_folder='templates')

@landing_bp.route('/try-it-out/submit', methods=['POST'])
def try_it_out_submit():
    """Handle the free trial submission"""
    logger.info("Demo submission received")
    response = request.form.get('writingTask1')
    task_id = request.form.get('task_id')
    
    if not response:
        flash("Please provide a response", "warning")
        return redirect(url_for('root'))  # Change this to your root route
    
    try:
        # Generate feedback using Task 1 Letter function
        feedback = generate_writing_task_1_letter_feedback(response, task_id)
        
        # Store feedback in session
        session['feedback'] = {
            'response': response,
            'task_achievement': feedback.get('task_achievement', ''),
            'coherence_cohesion': feedback.get('coherence_cohesion', ''),
            'lexical_resource': feedback.get('lexical_resource', ''),
            'grammatical_range_accuracy': feedback.get('grammatical_range_accuracy', ''),
            'how_to_improve': feedback.get('how_to_improve', {
                'examples': [],
                'general_suggestions': []
            }),
            'band_scores': feedback.get('band_scores', {}),
            'improved_response': feedback.get('improved_response', '')
        }
        
        logger.info("Demo feedback generated successfully")
        return redirect(url_for('landing.try_it_out_feedback'))
        
    except Exception as e:
        logger.error(f"Error generating demo feedback: {str(e)}")
        flash("There was an error generating feedback. Please try again.", "error")
        return redirect(url_for('root'))

@landing_bp.route('/try-it-out/feedback')
def try_it_out_feedback():
    """Show feedback for the free trial submission"""
    if 'feedback' not in session:
        return redirect(url_for('root'))

    feedback = session['feedback']
    task = Task.query.get(31)  # Get the demo task

    return render_template(
        'writing/task_1_feedback.html',
        response=feedback.get('response', ''),
        task_achievement=feedback.get('task_achievement', ''),
        coherence_cohesion=feedback.get('coherence_cohesion', ''),
        lexical_resource=feedback.get('lexical_resource', ''),
        grammatical_range_accuracy=feedback.get('grammatical_range_accuracy', ''),
        how_to_improve=feedback.get('how_to_improve', {
            'examples': [],
            'general_suggestions': []
        }),
        band_scores=feedback.get('band_scores', {}),
        improved_response=feedback.get('improved_response', ''),
        task=task,  # Pass the task object
        is_demo=True
    ) 