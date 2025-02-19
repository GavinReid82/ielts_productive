from flask_login import current_user
from app.models import db, Transcript, Task, UserTask
from flask import Blueprint, render_template, request, url_for, redirect, flash, session
from app.blueprints.writing.utils import extract_writing_response, generate_writing_task1_letter_feedback, save_writing_transcript
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
    return render_template('writing/writing_general_task_1_letter.html')

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
    feedback = generate_writing_task1_letter_feedback(response)

    # ✅ Save the transcript to the database
    save_writing_transcript(current_user.id, response, feedback)

    # ✅ Store feedback in session
    session['feedback'] = {
        'response': response,
        'general_comment': feedback.get('general_comment', ''),
        'did_well': feedback.get('did_well', []),
        'could_improve': feedback.get('could_improve', []),
        'ielts_band_score': feedback.get('ielts_band_score', 0.0)
    }

    return redirect(url_for('writing.writing_task_1_feedback'))  # ✅ Redirect instead of rendering directly


@writing_bp.route('/writing_task_1_feedback', methods=['GET'])
def writing_task_1_feedback():
    """Retrieve stored feedback from session and display it."""
    feedback = session.get('feedback', {})

    return render_template(
        'writing/writing_task_1_feedback.html',
        response=feedback.get('response', 'No response available.'),
        # general_comment=feedback.get('general_comment', 'No general comment provided.'),
        did_well=feedback.get('did_well', []),
        could_improve=feedback.get('could_improve', []),
        ielts_band_score=feedback.get('ielts_band_score', 0.0)
    )