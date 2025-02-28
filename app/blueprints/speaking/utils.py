import os
import json
import re
from flask import current_app, session
from werkzeug.utils import secure_filename
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def save_audio_file(request):
    """Handles file upload and saves it to the uploads folder."""
    if 'audio_file' not in request.files:
        return None, "No file uploaded."
    
    user_id = session.get("user_id", "unknown_user")
    filename = secure_filename(f"candidate_{user_id}_speaking_task.webm")
    
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    audio_file_path = os.path.join(upload_folder, filename)

    try:
        request.files['audio_file'].save(audio_file_path)
        return audio_file_path, None
    except Exception as e:
        return None, f"Error saving file: {e}"

def transcribe_audio(audio_path):
    """Transcribes an audio file using OpenAI Whisper."""
    try:
        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, response_format="text"
            )
        return response.strip(), None
    except Exception as e:
        return None, f"Error in transcription: {e}"

def generate_feedback(transcription):
    """Generates feedback based on IELTS Speaking Part 2 criteria."""
    messages = [
        {"role": "system", "content": (
            "You are an IELTS Speaking Part 2 examiner. Your job is to evaluate candidates' spoken responses "
            "using the official IELTS band descriptors: fluency & coherence, lexical resource, grammatical range & accuracy, "
            "and pronunciation. If relevant, give examples of grammar/vocabulary errors and how to correct them. "
            "If the candidate should expand on their response, give them a suggestion.\n\n"
            "Provide feedback in four sections:\n"
            "1. General Comment\n"
            "2. What You Did Well (bullet points)\n"
            "3. What You Could Improve (bullet points)\n"
            "4. Estimated IELTS Band Score\n\n"
            "Return ONLY a JSON object in this format:\n"
            "{\n"
            '"general_comment": "string",\n'
            '"did_well": ["string", "string"],\n'
            '"could_improve": ["string", "string"],\n'
            '"ielts_band_score": "float"\n'
            "}"
        )},
        {"role": "user", "content": f"Candidate's response:\n\n{transcription}"}
    ]

    try:
        chat_response = client.chat.completions.create(
            model="gpt-4", messages=messages, temperature=0.7, max_tokens=500
        )
        return json.loads(chat_response.choices[0].message.content.strip()), None
    except Exception as e:
        return {
            "general_comment": "Feedback not available.",
            "did_well": [],
            "could_improve": [],
            "ielts_band_score": 0.0
        }, f"Error generating feedback: {e}"
