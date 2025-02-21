import os
import json
from flask import current_app
from app.models import db, Transcript, Task, UserTask
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_writing_response(request):
    """Extracts and formats the user's writing response."""
    response = request.form.get('writingTask1', '').replace("\r\n", "\n")
    return response

def generate_writing_task_1_letter_feedback(response):
    """Generates AI feedback for IELTS Writing Task 1 based on official assessment criteria and provides an improved version of the response."""
    
    messages = [
        {
            "role": "system",
            "content": (
                "You are an IELTS Writing Task 1 examiner. Your task is to evaluate candidates' responses based on the "
                "official IELTS Writing Task 1 band descriptors and key assessment criteria. Your feedback must include:\n"
                "1. Task Achievement (TA): Assess if the response fully addresses the prompt and extends the points appropriately.\n"
                "2. Coherence & Cohesion (CC): Evaluate logical structure, paragraphing, and use of cohesive devices.\n"
                "3. Lexical Resource (LR): Assess the range, accuracy, and appropriacy of vocabulary.\n"
                "4. Grammatical Range & Accuracy (GRA): Analyze sentence structures, grammar, punctuation, and errors.\n\n"
                "Provide structured feedback as a JSON object with the following format:\n"
                "{\n"
                '"task_achievement": "string",\n'
                '"coherence_cohesion": "string",\n'
                '"lexical_resource": "string",\n'
                '"grammatical_range_accuracy": "string",\n'
                '"band_scores": {\n'
                '  "task_achievement": float,\n'
                '  "coherence_cohesion": float,\n'
                '  "lexical_resource": float,\n'
                '  "grammatical_range_accuracy": float,\n'
                '  "overall_band": float\n'
                "},\n"
                '"improved_response": "string"\n'
                "}\n\n"
                "Each score should be based on the official IELTS Writing Task 1 band descriptors, considering:\n"
                "- 9 = Excellent (Almost no errors, highly fluent, well-developed ideas)\n"
                "- 7-8 = Very good (Few minor errors, strong structure, well-extended ideas)\n"
                "- 5-6 = Moderate (Some errors, limited development, minor issues in organization or vocabulary)\n"
                "- 3-4 = Weak (Frequent errors, lack of clarity, poor structure)\n\n"
                "After assessing the response, generate an 'Improved Response' where:\n"
                "- The original ideas are maintained.\n"
                "- Task Achievement is optimized by ensuring full coverage of required points.\n"
                "- Coherence & Cohesion is improved by better structuring paragraphs and transitions.\n"
                "- Lexical Resource is enhanced by using more precise and varied vocabulary.\n"
                "- Grammar and sentence structure are refined, eliminating errors and improving complexity.\n\n"
                "Now, evaluate the following candidate's response and generate feedback accordingly."
            )
        },
        {"role": "user", "content": f"Candidate's response:\n\n{response}"}
    ]

    try:
        openai_response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=700  
        )
        raw_feedback = openai_response.choices[0].message.content.strip()
        feedback = json.loads(raw_feedback)

        # ✅ Clean list formatting
        feedback["did_well"] = [point.lstrip("- ") for point in feedback.get("did_well", [])]
        feedback["could_improve"] = [point.lstrip("- ") for point in feedback.get("could_improve", [])]

        return feedback
    except json.JSONDecodeError:
        return {"general_comment": "Error processing feedback.", "did_well": [], "could_improve": []}

def save_writing_transcript(user_id, response, feedback):
    """Saves the writing task response and feedback to the database."""
    task = Task.query.filter_by(name="IELTS Writing Task 1 - Letter").first()
    if not task:
        task = Task(name="IELTS Writing Task 1 - Letter", type="writing")
        db.session.add(task)
        db.session.commit()

    transcript = Transcript(user_id=user_id, task_id=task.id, transcription=response, feedback=feedback)
    db.session.add(transcript)

    existing_completion = UserTask.query.filter_by(user_id=user_id, task_id=task.id).first()
    if not existing_completion:
        user_task = UserTask(user_id=user_id, task_id=task.id)
        db.session.add(user_task)

    db.session.commit()
