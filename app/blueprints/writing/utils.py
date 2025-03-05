import os
import json
from flask import current_app
from app.models import db, Transcript, Task
from openai import OpenAI, OpenAIError, RateLimitError
import logging
import time

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger(__name__)

def extract_writing_response(request):
    """Extract and validate the writing response from the request."""
    response = request.form.get('writingTask1') or request.form.get('writingTask2')  # Check both form fields
    if not response:
        raise ValueError("No writing response provided")
    return response.replace("\r\n", "\n")  # Keep the line ending normalization

def generate_writing_task_1_letter_feedback(response, task_id):
    """Generates AI feedback for IELTS Writing Task 1 (Letter)."""
    try:
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
                    "You are an IELTS Writing Task 1 (Letter) examiner. Evaluate the candidate's letter based on the "
                    "official IELTS Writing Task 1 band descriptors and key assessment criteria. For each example in the feedback, "
                    "provide 2-3 alternative ways to express the same idea, showing different grammatical structures or vocabulary "
                    "choices. Address the candidate as 'you' and use British English.\n\n"
                    
                    "For each identified area of improvement:\n"
                    "1. Show the original text\n"
                    "2. Provide 2-3 improved versions that:\n"
                    "   - Use appropriate tone (formal/semi-formal/informal) for the letter type\n"
                    "   - Show natural letter-writing expressions and phrases\n"
                    "   - Employ varied vocabulary suitable for letter writing\n"
                    "   - Demonstrate clear organization with proper opening/closing\n"
                    
                    "For example, if the original is:\n"
                    "'I want to tell you about a problem with my neighbor.'\n"
                    "Provide multiple alternatives like:\n"
                    "1. 'I am writing to inform you about an ongoing issue with my neighbor.'\n"
                    "2. 'I would like to bring to your attention a situation concerning my neighbor.'\n"
                    "3. 'I need to discuss a problem I've been having with my neighbor.'\n\n"
                    
                    "1. **Task Achievement (TA):** Assess how well the letter:\n"
                    "   - Addresses the purpose of the letter (complaint, request, information, etc.)\n"
                    "   - Covers all bullet points from the task\n"
                    "   - Uses appropriate tone and style for the recipient\n"
                    "   - Includes proper letter format (opening, paragraphing, closing)\n"
                    "   - Meets the minimum word count (150 words)\n"
                    
                    "2. **Coherence & Cohesion (CC):** Evaluate:\n"
                    "   - Clear organization of ideas in logical paragraphs\n"
                    "   - Natural flow between paragraphs using appropriate linking phrases\n"
                    "   - Proper use of letter-writing conventions\n"
                    "   - Clear progression from opening to closing\n"
                    
                    "3. **Lexical Resource (LR):** Assess:\n"
                    "   - Range and accuracy of vocabulary for letter writing\n"
                    "   - Appropriate tone and register (formal/semi-formal/informal)\n"
                    "   - Natural expressions and collocations used in letters\n"
                    "   - Avoidance of overly informal or formal language where inappropriate\n"
                    
                    "4. **Grammatical Range & Accuracy (GRA):** Analyze:\n"
                    "   - Accuracy of basic and complex sentence structures\n"
                    "   - Variety of sentence forms appropriate for letters\n"
                    "   - Correct use of tenses and modal verbs\n"
                    "   - Proper punctuation in letter format\n\n"
                    
                    "The task details are provided below.\n\n"
                    f"Task Prompt:\n{task_prompt}\n\n"
                    f"Required Points:\n{bullet_points}\n\n"

                    "Provide structured feedback addressing the candidate as 'you' as a JSON object with the following format:\n"
                    "{\n"
                    '"how_to_improve_language": {\n'
                    '  "examples": [\n'
                    '    {\n'
                    '      "original": "string",\n'
                    '      "improved": ["string", "string", "string"]\n'
                    '    }\n'
                    '  ]\n'
                    '},\n'
                    '"how_to_improve_answer": {\n'
                    '  "examples": [\n'
                    '    {\n'
                    '      "original": "string",\n'
                    '      "improved": ["string", "string", "string"]\n'
                    '    }\n'
                    '  ]\n'
                    '},\n'
                    '"band_scores": {\n'
                    '  "task_achievement": float,\n'
                    '  "coherence_cohesion": float,\n'
                    '  "lexical_resource": float,\n'
                    '  "grammatical_range_accuracy": float,\n'
                    '  "overall_band": float\n'
                    '},\n'
                    '"improved_response": "string"\n'
                    "}\n\n"
                    
                    "For the 'how_to_improve_language' section:\n"
                    "- Identify 2-3 specific examples from the response that could be improved\n"
                    "- For each example, show the original text, an improved version, and explain the improvement\n"
                    "- Focus on grammar, vocabulary, and expression improvements\n"
                    "- Add 2-3 general suggestions for overall improvement\n"
                    "- Be constructive and encouraging in your feedback\n\n"

                    "For the 'how_to_improve_answer' section:\n"
                    "- Identify 2-3 specific examples from the response that could be improved\n"
                    "- For each example, show a section of the original text, a section of the improved version\n"
                    "- Focus on task achievement and coherence & cohesion improvements\n"
                    "- Add 2-3 general suggestions for overall improvement\n"
                    "- Be constructive and encouraging in your feedback\n\n"
                    
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
                    "- **Grammar** and sentence structure are refined, eliminating errors and improving complexity.\n"
                    "- Format the improved response with proper line breaks between paragraphs and letter components (greeting, body paragraphs, closing).\n\n"
                    "Now, evaluate the following candidate's response and generate feedback accordingly."
                )
            },
            {
                "role": "user",
                "content": f"Evaluate this letter:\n\n{response}\n\nTask Prompt:\n{task.main_prompt}\nRequired Points:\n{task.bullet_points}"
            }
        ]

        try:
            openai_response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                timeout=30
            )
            raw_feedback = openai_response.choices[0].message.content.strip()
            logger.info(f"Raw GPT response:\n{raw_feedback}")
            cleaned_feedback = raw_feedback.strip().replace('\n', '\\n').replace('\t', '\\t')
            logger.info(f"Cleaned response:\n{cleaned_feedback}")
            try:
                feedback = json.loads(cleaned_feedback)
                return feedback
            except json.JSONDecodeError as e:
                logger.error(f"JSON error after cleaning: {e}")
                logger.error(f"Error position: {e.pos}")
                logger.error(f"Line: {e.lineno}, Column: {e.colno}")
                # First retry with the same prompt
                logger.warning(f"First attempt failed with JSON error: {e}. Retrying...")
                try:
                    openai_response = client.chat.completions.create(
                        model="gpt-4",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000,
                        timeout=30
                    )
                    raw_feedback = openai_response.choices[0].message.content.strip()
                    cleaned_feedback = raw_feedback.strip().replace('\n', '\\n').replace('\t', '\\t')
                    feedback = json.loads(cleaned_feedback)
                    return feedback
                except (json.JSONDecodeError, Exception) as e:
                    # If retry fails, try with a simplified prompt
                    logger.warning(f"Retry failed: {e}. Attempting with simplified prompt...")
                    simplified_messages = [
                        {
                            "role": "system",
                            "content": (
                                "You are an IELTS Writing Task 1 examiner. Provide feedback in exactly this JSON format:\n"
                                "{\n"
                                '"how_to_improve_language": {\n'
                                '  "examples": [\n'
                                '    {\n'
                                '      "original": "string",\n'
                                '      "improved": ["string", "string", "string"]\n'
                                '    }\n'
                                '  ]\n'
                                '},\n'
                                '"how_to_improve_answer": {\n'
                                '  "examples": [\n'
                                '    {\n'
                                '      "original": "string",\n'
                                '      "improved": ["string", "string", "string"]\n'
                                '    }\n'
                                '  ]\n'
                                '},\n'
                                '"band_scores": {\n'
                                '  "task_achievement": float,\n'
                                '  "coherence_cohesion": float,\n'
                                '  "lexical_resource": float,\n'
                                '  "grammatical_range_accuracy": float,\n'
                                '  "overall_band": float\n'
                                '},\n'
                                '"improved_response": "string"\n'
                                "}"
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Evaluate this Writing Task 1 letter:\n\n{response}\n\nTask Prompt:\n{task.main_prompt}\nRequired Points:\n{task.bullet_points}"
                        }
                    ]
                    try:
                        openai_response = client.chat.completions.create(
                            model="gpt-4",
                            messages=simplified_messages,
                            temperature=0.7,
                            max_tokens=2000,
                            timeout=30
                        )
                        raw_feedback = openai_response.choices[0].message.content.strip()
                        feedback = json.loads(raw_feedback)
                        return feedback
                    except Exception as e:
                        logger.error(f"Simplified prompt attempt failed: {e}")
                        return {
                            "error": "Error processing feedback format",
                            "how_to_improve_language": {"examples": []},
                            "how_to_improve_answer": {"examples": []},
                            "band_scores": {
                                "task_achievement": 0,
                                "coherence_cohesion": 0,
                                "lexical_resource": 0,
                                "grammatical_range_accuracy": 0,
                                "overall_band": 0
                            },
                            "improved_response": "Your improved response will be available shortly."
                        }

        except RateLimitError as e:
            logger.error(f"OpenAI Rate Limit error: {str(e)}")
            time.sleep(5)
            try:
                openai_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000,
                    timeout=30
                )
                raw_feedback = openai_response.choices[0].message.content.strip()
                logger.info(f"Raw GPT response:\n{raw_feedback}")
                cleaned_feedback = raw_feedback.strip().replace('\n', '\\n').replace('\t', '\\t')
                logger.info(f"Cleaned response:\n{cleaned_feedback}")
                try:
                    feedback = json.loads(cleaned_feedback)
                    return feedback
                except json.JSONDecodeError as e:
                    logger.error(f"JSON error after cleaning: {e}")
                    logger.error(f"Error position: {e.pos}")
                    logger.error(f"Line: {e.lineno}, Column: {e.colno}")
                    return {
                        "error": "Service temporarily at capacity",
                        "how_to_improve_language": {
                            "examples": [],
                            "general_suggestions": ["Your feedback is being processed. Please check back soon."]
                        },
                        "how_to_improve_answer": {
                            "examples": [],
                            "general_suggestions": ["Your feedback is being processed. Please check back soon."]
                        },
                        "improved_response": "Your improved response will be available shortly."
                    }
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                return {
                    "error": "Error calling OpenAI API",
                    "how_to_improve_language": {"examples": []},
                    "how_to_improve_answer": {"examples": []},
                    "improved_response": "Your improved response will be available shortly."
                }

    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return {
            "error": f"Error generating feedback: {str(e)}",
            "how_to_improve_language": {
                "examples": [],
            },
            "how_to_improve_answer": {
                "examples": [],
            },  
            "improved_response": "Your improved response will be available shortly."
        }


def generate_writing_task_1_report_feedback(response, task_id):
    """Generates AI feedback for IELTS Writing Task 1 (Report)."""
    try:
        # Get the task first
        task = Task.query.get(task_id)
        if not task:
            raise ValueError("Task not found")

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an IELTS Writing Task 1 examiner. Your task is to assess and provide structured feedback for a candidate’s response.\n\n"
                    
                    "## **📌 EVALUATION CRITERIA**\n"
                    "**1️⃣ How to Improve Language (LR & GRA)**\n"
                    "- Identify **2-6 key grammar and vocabulary issues**.\n"
                    "- Provide **corrections** and **two alternative ways** to express each phrase.\n\n"

                    "**2️⃣ How to Improve Answer (TA & CC)**\n"
                    "- Explain **why the response does not fully meet the task requirements**.\n"
                    "- Identify **missing key trends, missing data points, or incorrect focus**.\n"
                    "- Suggest **how to improve coherence and cohesion**.\n\n"
                    
                    "**3️⃣ Band Scores (1-9)**\n"
                    "- Rate **Task Achievement (TA)**, **Coherence & Cohesion (CC)**, **Lexical Resource (LR)**, **Grammatical Range & Accuracy (GRA)**.\n"
                    "- Provide an **overall band score**.\n\n"
                    
                    "**4️⃣ Improved Response**\n"
                    "- Rewrite the response with **corrected grammar, vocabulary, and structure**.\n"
                    "- Maintain the **original ideas**, but improve clarity and academic tone.\n\n"
                    
                    "## **📌 OUTPUT FORMAT (MUST BE VALID JSON)**\n"
                    "Return feedback ONLY in this JSON format:\n"
                    
                    "{\n"
                    '"how_to_improve_language": {\n'
                    '  "examples": [\n'
                    '    {\n'
                    '      "original": "string",\n'
                    '      "improved": ["string", "string", "string"]\n'
                    '    }\n'
                    '  ]\n'
                    '},\n'
                    '"how_to_improve_answer": {\n'
                    '  "examples": [\n'
                    '    {\n'
                    '      "original": "string",\n'
                    '      "issues": ["Explain what is missing or incorrect in TA & CC."],\n'
                    '      "improved": ["string"]\n'
                    '    }\n'
                    '  ]\n'
                    '},\n'
                    '"band_scores": {\n'
                    '  "task_achievement": float,\n'
                    '  "coherence_cohesion": float,\n'
                    '  "lexical_resource": float,\n'
                    '  "grammatical_range_accuracy": float,\n'
                    '  "overall_band": float\n'
                    '},\n'
                    '"improved_response": "string"\n'
                    "}\n\n"
                    
                    "⚠️ **DO NOT return any explanation or formatting outside the JSON structure.**\n"
                    "Now, evaluate the following candidate's response."
                )
            },
            {
                "role": "user",
                "content": f"Evaluate this report:\n\n{response}\n\nTask Prompt:\n{task.main_prompt}\nGraph Description:\n{task.description}"
            }
        ]

        # Make the API call
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
        )

        # Extract the feedback
        feedback_text = completion.choices[0].message.content
        print(f"Raw OpenAI response: {feedback_text}")  # Debug log
        
        try:
            feedback = json.loads(feedback_text)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")  # Debug log
            print(f"Failed to parse: {feedback_text}")  # Debug log
            return {
                'error': 'Error parsing feedback',
                'how_to_improve_language': {'examples': []},
                'how_to_improve_answer': {'examples': []},
                'improved_response': 'Error generating feedback.'
            }

        return feedback

    except Exception as e:
        logger.error(f"Error generating feedback: {str(e)}")
        return {
            'error': f"Error generating feedback: {str(e)}",
            'how_to_improve_language': {'examples': []},
            'how_to_improve_answer': {'examples': []},
            'improved_response': 'Your improved response will be available shortly.'
        }


def generate_writing_task_2_feedback(response, task_id):
    """Generates AI feedback for IELTS Writing Task 2."""
    try:
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
                    "You are an IELTS Writing Task 2 examiner. Address the candidate as 'you' and use British English at all times. Evaluate the candidate's essay based on the "
                    "official IELTS Writing Task 2 band descriptors and key assessment criteria (see below). For each example in the feedback, "
                    "correct any grammar, vocabulary and expression errors first, then provide 1-2 alternative ways to express the same idea, "
                    "showing different grammatical structures or vocabulary choices.\n\n"
                    
                    "For each identified area of improvement:\n"
                    "1. Show the original text\n"
                    "2. Provide 2-3 improved versions.\n"
                    "   The first version should correct the grammar, vocabulary and expression errors. The other versions should:\n"
                    "   - Use different grammatical structures\n"
                    "   - Employ varied academic vocabulary\n"
                    "   - Show different ways to present arguments\n"
                    "   - Demonstrate advanced cohesive devices\n"
                    
                    "For example, if the original is:\n"
                    "'Many people think education important.'\n"
                    "Provide multiple alternatives like:\n"
                    "1. 'Many people think education is important.'\n"
                    "2. 'It is widely acknowledged that education plays a crucial role in society.'\n"
                    "3. 'The significance of education in modern society cannot be overstated.'\n\n"
                    
                    "1. **Task Response (TR):** Assess how fully the candidate (addressed as 'you') responds to the task, whether the position is clear, "
                    "and how well the main ideas are supported. The candidate (addressed as 'you') should write at least 250 words. A score of 9 indicates full coverage with detailed examples, while "
                    "lower scores reflect gaps or unclear arguments.\n"
                    
                    "2. **Coherence & Cohesion (CC):** Evaluate the logical structure (introduction, body paragraphs, conclusion), paragraphing, "
                    "and use of cohesive devices. A score of 9 means highly organized ideas with effective transitions, while lower scores reflect "
                    "issues with paragraphing or weak logical flow.\n"
                    
                    "3. **Lexical Resource (LR):** Assess the range, accuracy, and appropriacy of vocabulary for the topic and task. A score of 9 reflects "
                    "wide-ranging, precise vocabulary used appropriately. Scores of 5-6 indicate repetitive vocabulary, while 3-4 reflects "
                    "incorrect or limited word choice.\n"
                    
                    "4. **Grammatical Range & Accuracy (GRA):** Analyze sentence structures, grammar, punctuation, and errors. "
                    "A score of 9 means highly accurate grammar and varied sentence structures, while lower scores reflect frequent errors "
                    "and simpler structures.\n\n"
                    
                    "Provide structured feedback addressing the candidate as 'you' as a JSON object with the following format:\n"
                    "{\n"

                    '"how_to_improve_language": {\n'
                    '  "examples": [\n'
                    '    {\n'
                    '      "original": "string",\n'
                    '      "improved": ["string", "string", "string"]\n'
                    '    }\n'
                    '  ]\n'
                    '},\n'
                    '"how_to_improve_answer": {\n'
                    '  "examples": [\n'
                    '    {\n'
                    '      "original": "string",\n'
                    '      "improved": ["string", "string", "string"]\n'
                    '    }\n'
                    '  ]\n'
                    '},\n'
                    '"band_scores": {\n'
                    '  "task_response": float,\n'
                    '  "coherence_cohesion": float,\n'
                    '  "lexical_resource": float,\n'
                    '  "grammatical_range_accuracy": float,\n'
                    '  "overall_band": float\n'
                    '},\n'
                    '"improved_response": "string"\n'
                    "}\n\n"
                    
                    "For the 'how_to_improve_language' section:\n"
                    "- Identify between 2-6 specific examples of grammar, vocabulary, and expression from the response that could be improved\n"
                    "- For each example, show the original text and an improved version\n"
                    "- Correct any grammar, vocabulary and expression errors first\n"
                    "- Focus on grammar, vocabulary, and expression improvements\n"
                    "- Be constructive and encouraging in your feedback\n\n"

                    "For the 'how_to_improve_answer' section:\n"
                    "- Identify 2-3 specific examples of task response and coherence & cohesion from the response that could be improved\n"
                    "- For each example, show the relevant part of the original text and the improved version\n"
                    "- Focus on task response (especially the word count, which should be at least 250 words, and whether the argument is balanced and well-developed) and coherence & cohesion improvements\n"
                    "- Be constructive and encouraging in your feedback\n\n"
                    
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
                    "- **Grammar** and sentence structure are refined, eliminating errors and improving complexity.\n"
                    "- Format the improved response with proper line breaks between paragraphs and essay components (introduction, body paragraphs, conclusion).\n\n"
                    "Now, evaluate the following candidate's response and generate feedback accordingly."
                )
            },
            {
                "role": "user",
                "content": f"Evaluate this essay:\n\n{response}\n\nEssay Question:\n{task.main_prompt}"
            }
        ]

        try:
            openai_response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                timeout=30
            )
            raw_feedback = openai_response.choices[0].message.content.strip()
            logger.info(f"Raw GPT response:\n{raw_feedback}")
            cleaned_feedback = raw_feedback.strip().replace('\n', '\\n').replace('\t', '\\t')
            logger.info(f"Cleaned response:\n{cleaned_feedback}")
            
            try:
                feedback = json.loads(cleaned_feedback)
                return feedback
            except json.JSONDecodeError as e:
                logger.error(f"JSON error after cleaning: {e}")
                logger.error(f"Error position: {e.pos}")
                logger.error(f"Line: {e.lineno}, Column: {e.colno}")
                
                # First retry with the same prompt
                logger.warning(f"First attempt failed with JSON error: {e}. Retrying...")
                try:
                    openai_response = client.chat.completions.create(
                        model="gpt-4",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000,
                        timeout=30
                    )
                    raw_feedback = openai_response.choices[0].message.content.strip()
                    cleaned_feedback = raw_feedback.strip().replace('\n', '\\n').replace('\t', '\\t')
                    feedback = json.loads(cleaned_feedback)
                    return feedback
                except (json.JSONDecodeError, Exception) as e:
                    # If retry fails, try with a simplified prompt
                    logger.warning(f"Retry failed: {e}. Attempting with simplified prompt...")
                    simplified_messages = [
                        {
                            "role": "system",
                            "content": (
                                "You are an IELTS Writing Task 2 examiner. Provide feedback in exactly this JSON format:\n"
                                "{\n"
                                '"how_to_improve_language": {\n'
                                '  "examples": [\n'
                                '    {\n'
                                '      "original": "string",\n'
                                '      "improved": ["string", "string", "string"]\n'
                                '    }\n'
                                '  ]\n'
                                '},\n'
                                '"how_to_improve_answer": {\n'
                                '  "examples": [\n'
                                '    {\n'
                                '      "original": "string",\n'
                                '      "improved": ["string", "string", "string"]\n'
                                '    }\n'
                                '  ]\n'
                                '},\n'
                                '"band_scores": {\n'
                                '  "task_response": float,\n'
                                '  "coherence_cohesion": float,\n'
                                '  "lexical_resource": float,\n'
                                '  "grammatical_range_accuracy": float,\n'
                                '  "overall_band": float\n'
                                '},\n'
                                '"improved_response": "string"\n'
                                "}"
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Evaluate this Writing Task 2 essay:\n\n{response}\n\nEssay Question:\n{task_prompt}"
                        }
                    ]
                    try:
                        openai_response = client.chat.completions.create(
                            model="gpt-4",
                            messages=simplified_messages,
                            temperature=0.7,
                            max_tokens=2000,
                            timeout=30
                        )
                        raw_feedback = openai_response.choices[0].message.content.strip()
                        feedback = json.loads(raw_feedback)
                        return feedback
                    except Exception as e:
                        logger.error(f"All attempts failed: {e}")
                        return {
                            "error": "Error processing feedback format",
                            "how_to_improve_language": {"examples": []},
                            "how_to_improve_answer": {"examples": []},
                            "band_scores": {
                                "task_response": 0,
                                "coherence_cohesion": 0,
                                "lexical_resource": 0,
                                "grammatical_range_accuracy": 0,
                                "overall_band": 0
                            },
                            "improved_response": "Your improved response will be available shortly."
                        }

        except RateLimitError as e:
            logger.error(f"OpenAI Rate Limit error: {str(e)}")
            time.sleep(5)
            try:
                openai_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000,
                    timeout=30
                )
                raw_feedback = openai_response.choices[0].message.content.strip()
                cleaned_feedback = raw_feedback.strip().replace('\n', '\\n').replace('\t', '\\t')
                feedback = json.loads(cleaned_feedback)
                return feedback
            except Exception as e:
                logger.error(f"Retry after rate limit failed: {e}")
                return {
                    "error": "Service temporarily at capacity",
                    "how_to_improve_language": {"examples": []},
                    "how_to_improve_answer": {"examples": []},
                    "band_scores": {
                        "task_response": 0,
                        "coherence_cohesion": 0,
                        "lexical_resource": 0,
                        "grammatical_range_accuracy": 0,
                        "overall_band": 0
                    },
                    "improved_response": "Your improved response will be available shortly."
                }

    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return {
            "error": f"Error generating feedback: {str(e)}",
            "how_to_improve_language": {"examples": []},
            "how_to_improve_answer": {"examples": []},
            "band_scores": {
                "task_response": 0,
                "coherence_cohesion": 0,
                "lexical_resource": 0,
                "grammatical_range_accuracy": 0,
                "overall_band": 0
            },
            "improved_response": "Your improved response will be available shortly."
        }


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
