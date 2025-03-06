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
        "Error processing feedback",
        "Error generating feedback"
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
            
        # Check for error in feedback
        if t.feedback.get('error'):
            print(f"- Skipping: contains error message")
            continue
            
        # Check for required fields in new format
        required_fields = ['how_to_improve_language', 'how_to_improve_answer', 'improved_response']
        has_all_fields = True
        for field in required_fields:
            if not t.feedback.get(field):
                print(f"- Skipping: missing {field}")
                has_all_fields = False
                break
                
        if not has_all_fields:
            continue
            
        # Check if any error messages in the improved response
        if any(error in t.feedback['improved_response'] for error in error_messages):
            print(f"- Skipping: improved_response contains error message")
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