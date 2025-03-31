from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, current_app
from app.blueprints.speaking.utils import save_audio_file, transcribe_audio, generate_feedback
from app.extensions import db
from app.models import Transcript, Task
from openai import OpenAI
import json
import os
import re
from werkzeug.utils import secure_filename
from app.blueprints.speaking import speaking_bp


speaking_bp = Blueprint('speaking', __name__, template_folder='templates')
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@speaking_bp.route('/')
def speaking_home():
    return render_template('speaking/home.html')

@speaking_bp.route('/speaking_tips')
def speaking_tips():
    return render_template('speaking/speaking_tips.html')

@speaking_bp.route('/speaking_task_1')
def speaking_task_1():
    return render_template('speaking/speaking_task_1.html')

@speaking_bp.route('/speaking_task_3')
def speaking_task_3():
    return render_template('speaking/speaking_task_3.html')

@speaking_bp.route('/speaking_task_4')
def speaking_task_4():
    return render_template('speaking/speaking_task_4.html')

@speaking_bp.route('/speaking_task_2')
def speaking_task_2():
    """Render the IELTS Speaking Part 2 task."""
    return render_template('speaking/speaking_task_2.html', 
                           question="Describe something you own which is very important to you. You should say: "
                                    "where you got it from, how long you have had it, what you use it for, and "
                                    "explain why it is important to you.", 
                           question_number=1)


# ------------------------------------------------------------------------------------------------
# Task 2
# ------------------------------------------------------------------------------------------------


@speaking_bp.route('/speaking_task_2_submit', methods=['POST'])
def speaking_task_2_submit():
    """Handle audio file upload, transcription, and feedback generation."""

    # ✅ Step 1: Ensure user is logged in before processing
    user_id = session.get("user_id")
    print(f"🛠️ DEBUG: Session Data - {session}")  # ✅ Log session data for debugging

    if not user_id:
        print("❌ ERROR: User ID not found in session!")
        return render_template('speaking/speaking_task_2_feedback.html',
                            question="Describe something you own which is very important to you.",
                            transcription="No transcription available.",
                            general_comment="User is not logged in or session expired.",
                            did_well=[],
                            could_improve=[])

    # ✅ Step 2: Process audio file
    audio_file_path, error = save_audio_file(request)
    if error:
        print(f"❌ ERROR: Audio file not saved! {error}")
        return render_template('speaking/speaking_task_2_feedback.html',
                               question="Describe something you own which is very important to you.",
                               transcription="No transcription available.",
                               general_comment=error,
                               did_well=[],
                               could_improve=[])

    print(f"✅ Audio file saved: {audio_file_path}")

    # ✅ Step 3: Transcribe audio
    transcription, error = transcribe_audio(audio_file_path)
    if error:
        print(f"❌ ERROR: Transcription failed! {error}")
        return render_template('speaking/speaking_task_2_feedback.html',
                               question="Describe something you own which is very important to you.",
                               transcription="No transcription available.",
                               general_comment=error,
                               did_well=[],
                               could_improve=[])

    print(f"✅ Transcription: {transcription}")

    # ✅ Step 4: Generate feedback
    feedback, error = generate_feedback(transcription)
    print(f"✅ Feedback Generated: {feedback}")

    # ✅ Step 5: Store transcript in database
    task = Task.query.filter_by(name="IELTS Speaking Task 2").first()
    if not task:
        task = Task(name="IELTS Speaking Task 2", type="speaking")
        db.session.add(task)
        db.session.commit()

    # ✅ Step 6: Save transcript to database
    transcript = Transcript(user_id=user_id, task_id=task.id,
                            transcription=transcription, feedback=feedback)
    db.session.add(transcript)
    db.session.commit()

    # ✅ Store feedback in session before redirecting
    session['feedback'] = {
        'question': "Describe something you own which is very important to you.",
        'transcription': transcription,
        'general_comment': feedback.get('general_comment', ''),
        'did_well': feedback.get('did_well', []),
        'could_improve': feedback.get('could_improve', []),
        'ielts_band_score': feedback.get('ielts_band_score', 0.0)
    }

    return redirect(url_for('speaking.speaking_task_2_feedback'))


@speaking_bp.route('/speaking_task_2_feedback', methods=['GET'])
def speaking_task_2_feedback():
    feedback = session.get('feedback', {})
    
    return render_template(
        'speaking/speaking_task_2_feedback.html',
        question=feedback.get('question', 'Unknown question'),
        transcription=feedback.get('transcription', 'No transcription available.'),
        general_comment=feedback.get('general_comment', 'No general comment provided.'),
        did_well=feedback.get('did_well', []),
        could_improve=feedback.get('could_improve', []),
        ielts_band_score=feedback.get('ielts_band_score', 0.0)
    )