from flask import render_template, Blueprint
from flask_login import login_required, current_user
from app.models import Transcript
from app.blueprints.dashboard import dashboard_bp

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required  # ✅ Only logged-in users can access
def dashboard_home():
    return render_template('dashboard/home.html')

@dashboard_bp.route('/my-tasks')
@login_required
def my_tasks():
    error_messages = [
        "Please try again later",
        "System is experiencing high load",
        "Service temporarily unavailable",
        "We apologize for the inconvenience",
        "Feedback service temporarily unavailable",
        "Error processing feedback"
    ]
    
    # Get all transcripts that have an associated feedback
    transcripts = Transcript.query.filter(
        Transcript.user_id == current_user.id,
        Transcript.feedback != None
    ).order_by(Transcript.created_at.desc()).all()
    
    # Filter for valid feedback
    valid_transcripts = []
    for t in transcripts:
        print(f"\nChecking transcript {t.id}:")
        print(f"Task type: {t.task.type}")
        print(f"Feedback type: {type(t.feedback)}")
        
        if not isinstance(t.feedback, dict):
            print(f"- Skipping: feedback is not a dict")
            continue
            
        # For Writing Task 2, check task_response
        if t.task.type == 'writing_task_2':
            print(f"- Has task_response: {bool(t.feedback.get('task_response'))}")
            if not t.feedback.get('task_response'):
                print(f"- Skipping: missing task_response")
                continue
            if any(error in t.feedback['task_response'] for error in error_messages):
                print(f"- Skipping: task_response contains error message")
                continue
        # For other tasks, check task_achievement
        else:
            print(f"- Has task_achievement: {bool(t.feedback.get('task_achievement'))}")
            if not t.feedback.get('task_achievement'):
                print(f"- Skipping: missing task_achievement")
                continue
            if any(error in t.feedback['task_achievement'] for error in error_messages):
                print(f"- Skipping: task_achievement contains error message")
                continue
                
        # Check other required fields
        required_fields = ['coherence_cohesion', 'lexical_resource', 'grammatical_range_accuracy']
        for field in required_fields:
            print(f"- Has {field}: {bool(t.feedback.get(field))}")
            if not t.feedback.get(field):
                print(f"- Skipping: missing {field}")
                continue
            if any(error in t.feedback[field] for error in error_messages):
                print(f"- Skipping: {field} contains error message")
                continue
            
        print(f"- Adding transcript {t.id} to valid list")
        valid_transcripts.append(t)
    
    print(f"\nFound {len(valid_transcripts)} valid transcripts out of {len(transcripts)} total")
    return render_template('dashboard/my_tasks.html', transcripts=valid_transcripts)

@dashboard_bp.route('/reading')
@login_required
def reading():
    return render_template('reading/home.html')

@dashboard_bp.route('/writing')
@login_required
def writing():
    return render_template('writing/home.html')

@dashboard_bp.route('/speaking')
@login_required
def speaking():
    return render_template('speaking/home.html')

@dashboard_bp.route('/listening')
@login_required
def listening():
    return render_template('listening/home.html')