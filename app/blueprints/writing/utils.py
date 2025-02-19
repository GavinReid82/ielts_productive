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

def generate_writing_task1_letter_feedback(response):
    """Generates AI feedback for the IELTS Writing Task 1."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are an IELTS Writing (General) Task 1 examiner. Your job is to give feedback "
                "to candidates based on their performance. Provide structured feedback:\n"
                "1. General Comment\n2. What You Did Well (bullet points)\n3. What You Could Improve (bullet points)\n3. Estimated IELTS Band Score (usually +/-0.5)\n\n"
                "Ensure feedback is clear, concise, and simple to understand. Address the candidate directly (e.g. 'You did well' or 'You could improve') or use imperative verbs. Return a JSON response with:\n"
                "{\n"
                '"general_comment": "string",\n'
                '"did_well": ["string", "string"],\n'
                '"could_improve": ["string", "string"],\n'
                '"ielts_band_score": "float"\n'
                "}\n"
                "Task Criteria:\n"
                "- Task Achievement: Did they address all points?\n"
                "- Coherence & Cohesion: Is it logically structured?\n"
                "- Lexical Resource: Is vocabulary varied?\n"
                "- Grammatical Range & Accuracy: Are there errors? Provide examples and corrections.\n\n"
                "Task Prompt:\n"
                "A friend has agreed to look after your house and pet while you are on holiday. "
                "Write a letter to your friend.\n"
                "In your letter:\n"
                "- Give contact details for when you are away\n"
                "- Give instructions about how to care for your pet\n"
                "- Describe other household duties you would like your friend to undertake.\n\n"
            )
        },
        {"role": "user", "content": f"Candidate's response:\n\n{response}"}
    ]

    try:
        openai_response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=400
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
