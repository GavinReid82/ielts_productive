import os
import json
from flask import current_app
from app.models import db, Transcript, Task
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_writing_response(request):
    """Extract and validate the writing response from the request."""
    response = request.form.get('writingTask1')  # Changed from 'writingResponse' to match the form
    if not response:
        raise ValueError("No writing response provided")
    return response.replace("\r\n", "\n")  # Keep the line ending normalization

def generate_writing_task_1_letter_feedback(response, task_id):
    """Generates AI feedback for IELTS Writing Task 1 based on official assessment criteria and provides an improved version of the response."""
    
    # Validate task_id is an integer
    try:
        task_id = int(task_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid task ID provided")

    # Get the task
    task = Task.query.get(task_id)
    if not task:
        raise ValueError("Task not found")

    task_prompt = task.main_prompt if task and task.main_prompt else "No prompt provided."
    bullet_points = task.bullet_points if task and task.bullet_points else "No bullet points provided."

    messages = [
    {
        "role": "system",
        "content": (
            "You are an IELTS Writing Task 1 examiner providing feedback in British English. Use direct, simple language "
            "and address the candidate as 'you'. The task details are provided below.\n\n"
            f"Task Prompt:\n{task_prompt}\n\n"
            f"Required Points:\n{bullet_points}\n\n"
            "You are an IELTS Writing Task 1 examiner. Your task is to evaluate candidates' responses based on the "
            "official IELTS Writing Task 1 band descriptors and key assessment criteria. Your feedback must be "
            "consistent, accurate, and strictly follow these guidelines:\n\n"
            
            "1. **Task Achievement (TA):** Assess how fully the candidate addresses the prompt, if the key features are "
            "accurately summarized, and if any relevant comparisons are made. A score of 9 means all key features are fully covered, "
            "with clear, accurate comparisons. Lower scores reflect incomplete coverage or inaccurate information.\n"
            
            "2. **Coherence & Cohesion (CC):** Evaluate the organization of ideas, paragraphing, and the use of cohesive devices. "
            "A score of 9 reflects clear, logical structure with effective transitions between ideas. Scores lower than 9 reflect "
            "problems in paragraphing, weak transitions, or illogical ordering of ideas.\n"
            
            "3. **Lexical Resource (LR):** Assess the range, accuracy, and appropriacy of vocabulary. A score of 9 requires precise, "
            "varied vocabulary used accurately. A score of 5-6 means the vocabulary is limited, repetitive, or used inaccurately.\n"
            
            "4. **Grammatical Range & Accuracy (GRA):** Analyze sentence structures, punctuation, and grammar. A score of 9 means "
            "accurate grammar and varied sentence structures, while lower scores indicate frequent errors or simpler sentence structures.\n\n"
            
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
            "- **9** = Excellent (Almost no errors, highly fluent, well-developed ideas)\n"
            "- **7-8** = Very good (Few minor errors, strong structure, well-extended ideas)\n"
            "- **5-6** = Moderate (Some errors, limited development, minor issues in organization or vocabulary)\n"
            "- **3-4** = Weak (Frequent errors, lack of clarity, poor structure)\n\n"
            
            "After assessing the response, generate an 'Improved Response' based on the specific task and where:\n"
            "- The user's original ideas are maintained where relevant to the task.\n"
            "- **Task Achievement** is optimized by ensuring full coverage of required points.\n"
            "- **Coherence & Cohesion** is improved by better structuring paragraphs and transitions.\n"
            "- **Lexical Resource** is enhanced by using more precise and varied vocabulary.\n"
            "- **Grammar** and sentence structure are refined, eliminating errors and improving complexity.\n\n"
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


def generate_writing_task_1_report_feedback(response, task_id):
    """Generates AI feedback for IELTS Writing Task 1 based on official assessment criteria and provides an improved version of the response."""
    
    # Validate task_id is an integer
    try:
        task_id = int(task_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid task ID provided")

    # Get the task
    task = Task.query.get(task_id)
    if not task:
        raise ValueError("Task not found")

    if task and task.description:
        graph_description = task.description
    else:
        graph_description = "No graph description provided."

    messages = [
    {
        "role": "system",
        "content": (
            "You are an IELTS Academic Writing Task 1 (Report) examiner. Your task is to evaluate candidates' responses based on the "
            "official IELTS Writing Task 1 band descriptors and key assessment criteria. Candidates' responses are based on a graph, "
            "which is provided below with the user's response. Your feedback must be consistent, accurate, and strictly follow these guidelines:\n\n"
            
            "1. **Task Achievement (TA):** Assess how fully the candidate addresses the prompt, if the key features are "
            "accurately summarized, and if any relevant comparisons are made. A score of 9 means all key features are fully covered, "
            "with clear, accurate comparisons. Lower scores reflect incomplete coverage or inaccurate information.\n"
            
            "2. **Coherence & Cohesion (CC):** Evaluate the organization of ideas, paragraphing, and the use of cohesive devices. "
            "A score of 9 reflects clear, logical structure with effective transitions between ideas. Scores lower than 9 reflect "
            "problems in paragraphing, weak transitions, or illogical ordering of ideas.\n"
            
            "3. **Lexical Resource (LR):** Assess the range, accuracy, and appropriacy of vocabulary. A score of 9 requires precise, "
            "varied vocabulary used accurately. A score of 5-6 means the vocabulary is limited, repetitive, or used inaccurately.\n"
            
            "4. **Grammatical Range & Accuracy (GRA):** Analyze sentence structures, punctuation, and grammar. A score of 9 means "
            "accurate grammar and varied sentence structures, while lower scores indicate frequent errors or simpler sentence structures.\n\n"
            
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
            "- **9** = Excellent (Almost no errors, highly fluent, well-developed ideas)\n"
            "- **7-8** = Very good (Few minor errors, strong structure, well-extended ideas)\n"
            "- **5-6** = Moderate (Some errors, limited development, minor issues in organization or vocabulary)\n"
            "- **3-4** = Weak (Frequent errors, lack of clarity, poor structure)\n\n"
            
            "After assessing the response, generate an 'Improved Response' based on the specific task and where:\n"
            "- The user's original ideas are maintained where relevant to the task.\n"
            "- **Task Achievement** is optimized by ensuring full coverage of required points.\n"
            "- **Coherence & Cohesion** is improved by better structuring paragraphs and transitions.\n"
            "- **Lexical Resource** is enhanced by using more precise and varied vocabulary.\n"
            "- **Grammar** and sentence structure are refined, eliminating errors and improving complexity.\n\n"
            "Now, evaluate the following candidate's response and generate feedback accordingly."
        )
    },
    {"role": "user", "content": f"Graph details:\n\n{graph_description}"},
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
    

def generate_writing_task_2_feedback(response, task_id):
    """Generates AI feedback for IELTS Writing Task 2 based on official assessment criteria and provides an improved version of the response."""
    
    # Validate task_id is an integer
    try:
        task_id = int(task_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid task ID provided")

    # Get the task
    task = Task.query.get(task_id)
    if not task:
        raise ValueError("Task not found")

    task_prompt = task.main_prompt if task and task.main_prompt else "No prompt provided."

    messages = [
    {
        "role": "system",
        "content": (
            "You are an IELTS Writing Task 2 examiner providing feedback in British English. Use direct, simple language "
            "and address the candidate as 'you'. The essay question is provided below.\n\n"
            f"Essay Question:\n{task_prompt}\n\n"
            "You are an IELTS Writing Task 2 examiner. Your task is to evaluate candidates' responses based on the "
            "official IELTS Writing Task 2 band descriptors and key assessment criteria. Your feedback must be "
            "consistent and rigorous, and adhere strictly to the following rules:\n\n"
            
            "1. **Task Response (TR):** Assess how fully the candidate responds to the task, whether the position is clear, "
            "and how well the main ideas are supported. A score of 9 indicates full coverage with detailed examples, while "
            "lower scores reflect gaps or unclear arguments.\n"
            
            "2. **Coherence & Cohesion (CC):** Evaluate the logical structure, paragraphing, and use of cohesive devices. "
            "A score of 9 means highly organized ideas with effective transitions, while lower scores reflect issues with paragraphing "
            "or weak logical flow.\n"
            
            "3. **Lexical Resource (LR):** Assess the range, accuracy, and appropriacy of vocabulary. A score of 9 reflects "
            "wide-ranging, precise vocabulary used appropriately. Scores of 5-6 indicate repetitive vocabulary, while 3-4 reflects "
            "incorrect or limited word choice.\n"
            
            "4. **Grammatical Range & Accuracy (GRA):** Analyze sentence structures, grammar, punctuation, and errors. "
            "A score of 9 means highly accurate grammar and varied sentence structures, while lower scores reflect frequent errors "
            "and simpler structures.\n\n"
            
            "Provide structured feedback as a JSON object with the following format:\n"
            "{\n"
            '"task_response": "string",\n'
            '"coherence_cohesion": "string",\n'
            '"lexical_resource": "string",\n'
            '"grammatical_range_accuracy": "string",\n'
            '"band_scores": {\n'
            '  "task_response": float,\n'
            '  "coherence_cohesion": float,\n'
            '  "lexical_resource": float,\n'
            '  "grammatical_range_accuracy": float,\n'
            '  "overall_band": float\n'
            "},\n"
            '"improved_response": "string"\n'
            "}\n\n"
            
            "Each score should be based on the official IELTS Writing Task 2 band descriptors, considering:\n"
            "- **9** = Excellent (Almost no errors, highly fluent, well-developed ideas)\n"
            "- **7-8** = Very good (Few minor errors, strong structure, well-extended ideas)\n"
            "- **5-6** = Moderate (Some errors, limited development, minor issues in organization or vocabulary)\n"
            "- **3-4** = Weak (Frequent errors, lack of clarity, poor structure)\n\n"
            
            "After assessing the response, generate an 'Improved Response' based on the specific task and where:\n"
            "- The user's original ideas are maintained where relevant to the task.\n"
            "- **Task Response** is optimized by ensuring full coverage of required points.\n"
            "- **Coherence & Cohesion** is improved by better structuring paragraphs and transitions.\n"
            "- **Lexical Resource** is enhanced by using more precise and varied vocabulary.\n"
            "- **Grammar** and sentence structure are refined, eliminating errors and improving complexity.\n\n"
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


def save_writing_transcript(user_id, task_id, response, feedback):
    """Saves the writing task response and feedback to the database."""
    task = Task.query.filter_by(id=task_id).first()  # Use task_id here to fetch the task
    if not task:
        task = Task(id=task_id, name="IELTS Writing Task 1 - Letter", type="writing")  # Ensure correct task is added
        db.session.add(task)
        db.session.commit()

    transcript = Transcript(user_id=user_id, task_id=task.id, transcription=response, feedback=feedback)
    db.session.add(transcript)
    db.session.commit()
