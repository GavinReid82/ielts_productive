import os
import json
from flask import current_app
from app.extensions import db
from app.models import Transcript, Task
from openai import OpenAI, OpenAIError, RateLimitError
import logging
import time
import re

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
        task = Task.query.get(task_id)
        if not task:
            raise ValueError("Task not found")

        word_count = len(response.split())
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an IELTS Writing Task 1 (letter) examiner.\n"
                    "Your task is to assess and provide structured feedback for a candidate's letter.\n"
                    "Use the task prompt and bullet points to give relevant feedback.\n"
                    "Respond in British English and address the candidate as 'you'.\n\n"
                    
                    "Follow these instructions exactly:\n\n"
                    
                    "=== STEP 1: CHECK LENGTH ===\n"
                    "If response is under 150 words, your FIRST feedback must address this:\n"
                    "- Original: [full response]\n"
                    "- Improved: [\n"
                    "    'Your response is only [X] words. You MUST write at least 150 words.',\n"
                    "    'Missing required elements: proper letter format, addressing all bullet points, and conclusion',\n"
                    "    'See below for how to develop your answer properly'\n"
                    "  ]\n\n"

                    "=== STEP 2: LANGUAGE FEEDBACK ===\n"
                    "Identify **2-5 key grammar and vocabulary issues**.\n"
                    "In 'how_to_improve_language', provide:\n"
                    "1. The original issue from the candidate's response\n"
                    "2. A corrected version\n"
                    "3. An alternative way to express it\n\n"
                    
                    "=== STEP 3: TASK ACHIEVEMENT FEEDBACK ===\n"
                    "Identify **2-3 key Task Achievement issues**.\n"
                    "In 'how_to_improve_answer', address:\n"
                    "1. Response below 150 words\n"
                    "2. Missing bullet points\n"
                    "3. Inappropriate tone\n"
                    "4. Letter format issues\n"
                    "5. Paragraph organisation\n\n"
                    
                    "=== STEP 4: GENERATE IMPROVED RESPONSE ===\n"
                    "Generate an improved letter that:\n"
                    "- Meets the word count requirement\n"
                    "- Maintains the user's original ideas where relevant\n"
                    "- Addresses all bullet points\n"
                    "- Uses appropriate tone and format\n"
                    "- Includes proper letter components\n"
                    "- Uses varied vocabulary and grammar\n\n"

                    "=== OUTPUT FORMAT (STRICT JSON) ===\n"
                    "{\n"
                    '"how_to_improve_language": {\n'
                    '  "examples": [{\n'
                    '    "original": "text",\n'
                    '    "improved": ["correction", "alternative"]\n'
                    '  }]\n'
                    '},\n'
                    '"how_to_improve_answer": {\n'
                    '  "examples": [{\n'
                    '    "issue": "text",\n'
                    '    "improved": "text"\n'
                    '  }]\n'
                    '},\n'
                    '"improved_response": "complete rewritten letter"\n'
                    "}\n\n"

                    "=== IMPORTANT ===\n"
                    "- Always check word count first\n"
                    "- Ensure all bullet points are addressed\n"
                    "- Check tone matches the letter type\n"
                    "- Return ONLY valid JSON\n"
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
                                "You are an IELTS Writing Task 1 (letter) examiner. Provide feedback in exactly this JSON format:\n"
                                "{\n"
                                '"how_to_improve_language": {\n'
                                '  "examples": [\n'
                                '    {\n'
                                '      "original": "text",\n'
                                '      "improved": ["correction", "alternative"]\n'
                                '    }\n'
                                '  ]\n'
                                '},\n'
                                '"how_to_improve_answer": {\n'
                                '  "examples": [\n'
                                '    {\n'
                                '      "issue": "text",\n'
                                '      "improved": "text"\n'
                                '    }\n'
                                '  ]\n'
                                '},\n'
                                '"improved_response": "text"\n'
                                "}\n"
                                "\nEnsure 'improved' in how_to_improve_answer is a single string, not an array."
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

        # Calculate word count
        word_count = len(response.split())
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an IELTS Academic Writing Task 1 (report) examiner.\n"
                    "Your task is to assess and provide structured feedback for a candidate's response.\n"
                    "Use the task prompt and graph description (given in content) to give relevant feedback to the candidate's response.\n"
                    "Respond in British English and address the candidate as 'you'.\n\n"
                    
                    "Follow these instructions exactly:\n\n"
                    
                    "=== STEP 1: CHECK LENGTH ===\n"
                    "If response is under 150 words, your FIRST feedback for 'how_to_improve_answer' must address this:\n"
                    "- Original: [full response]\n"
                    "- Improved: [\n"
                    "    'Your response is only [X] words. You MUST write at least 150 words.',\n"
                    "    'Missing required elements: introduction (overview), body paragraphs (data analysis, comparisons) and conclusion',\n"
                    "    'See below for how to develop your answer properly'\n"
                    "  ]\n\n"

                    "=== STEP 2: LANGUAGE FEEDBACK ===\n"
                    "Identify **2-5 key grammar and vocabulary issues**.\n"
                    "In 'how_to_improve_language', provide:\n"
                    "1. The original issue as provided in the candidate's response\n"
                    "2. A corrected version of the original issue\n"
                    "3. An alternative way to express the original issue (e.g. using passive voice)\n\n"
                    
                    "Example format:\n"
                    "Original: 'the graph show people watch more tv in the night'\n"
                    "Improved: [\n"
                    "  'The graph shows that people watched more television at night',\n"
                    "  'According to the data, television viewership was seen to be highest at night...',\n"
                    "]\n\n"

                    "=== STEP 3: TASK ACHIEVEMENT FEEDBACK ===\n"
                    "Identify **2-3 key Task Achievement issues**.\n"
                    "In 'how_to_improve_answer', address:\n"
                    "1. Response below 150 words\n"
                    "2. Missing overview\n"
                    "3. Missing data/percentages\n"
                    "4. Missing comparisons\n"
                    "5. Paragraph organisation\n\n"
                    
                    "Example format:\n"
                    "Issue: 'Missing comparisons'\n"
                    "Improved: [\n"
                    "  'You have identified differences in the data, but not given any similarities. For example, 'Television and radio shared similar audience numbers between 12pm and 1pm',\n"
                    "]\n\n"

                    "=== STEP 4: GENERATE IMPROVED RESPONSE ===\n"
                    "Generate an 'Improved Response' based on the specific task and where:\n"
                    "- Meets the word count requirement\n"
                    "- The user's original ideas are maintained where relevant to the task.\n"
                    "- **Task Achievement** is optimized by ensuring full coverage of required points.\n"
                    "- **Coherence & Cohesion** is improved by better structuring paragraphs and transitions.\n"
                    "- **Lexical Resource** is enhanced by using more precise and varied vocabulary.\n"
                    "- **Grammar** and sentence structure are refined, eliminating errors and improving complexity.\n"
                    "- Format the improved response with proper line breaks between paragraphs and essay components (introduction, body paragraphs, conclusion).\n\n"

                    "=== OUTPUT FORMAT (STRICT JSON) ===\n"
                    "{\n"
                    '"how_to_improve_language": {\n'
                    '  "examples": [{\n'
                    '    "original": "text",\n'
                    '    "improved": ["correction", "alternative"]\n'
                    '  }]\n'
                    '},\n'
                    '"how_to_improve_answer": {\n'
                    '  "examples": [{\n'
                    '    "issue": "text",\n'
                    '    "improved": "text"\n'
                    '  }]\n'
                    '},\n'
                    '"improved_response": "complete rewritten response"\n'
                    "}\n\n"

                    "=== IMPORTANT ===\n"
                    "- Always check word count first\n"
                    "- Include specific data/percentages in improvements\n"
                    "- Refer to the task prompt and graph description to give relevant feedback\n"
                    "- Return ONLY valid JSON\n"
                )
            },
            {
                "role": "user",
                "content": f"Evaluate this report:\n\n{response}\n\nTask Prompt:\n{task.main_prompt}\nGraph Description:\n{task.description}"
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
            
            # First try to parse the raw JSON
            try:
                feedback = json.loads(raw_feedback)
                return feedback
            except json.JSONDecodeError:
                # If that fails, try cleaning the response
                try:
                    # Replace newlines in the improved_response section
                    cleaned_feedback = re.sub(
                        r'("improved_response":\s*")(.*?)(")',
                        lambda m: m.group(1) + m.group(2).replace('\n', '\\n') + m.group(3),
                        raw_feedback,
                        flags=re.DOTALL
                    )
                    
                    feedback = json.loads(cleaned_feedback)
                    
                    # Convert escaped newlines back to real newlines in improved_response
                    if 'improved_response' in feedback:
                        feedback['improved_response'] = feedback['improved_response'].replace('\\n', '\n')
                    
                    return feedback
                    
                except (json.JSONDecodeError, Exception) as e:
                    logger.error(f"JSON error after cleaning: {e}")
                    return {
                        "error": "Error parsing feedback",
                        "how_to_improve_language": {"examples": []},
                        "how_to_improve_answer": {"examples": []},
                        "improved_response": "Error generating feedback."
                    }

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {
                "error": f"Error calling OpenAI API: {str(e)}",
                "how_to_improve_language": {"examples": []},
                "how_to_improve_answer": {"examples": []},
                "improved_response": "Error generating feedback."
            }

    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return {
            "error": f"Error generating feedback: {str(e)}",
            "how_to_improve_language": {"examples": []},
            "how_to_improve_answer": {"examples": []},
            "improved_response": "Error generating feedback."
        }


def generate_writing_task_2_feedback(response, task_id):
    """Generates AI feedback for IELTS Writing Task 2 (Essay)."""
    try:
        task = Task.query.get(task_id)
        if not task:
            raise ValueError("Task not found")

        word_count = len(response.split())
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an IELTS Writing Task 2 examiner.\n"
                    "Your task is to assess and provide structured feedback for a candidate's essay.\n"
                    "Use the essay question to give relevant feedback.\n"
                    "Respond in British English and address the candidate as 'you'.\n\n"
                    
                    "Follow these instructions exactly:\n\n"
                    
                    "=== STEP 1: CHECK LENGTH ===\n"
                    "If response is under 250 words, your FIRST feedback must address this:\n"
                    "- Original: [full response]\n"
                    "- Improved: [\n"
                    "    'Your response is only [X] words. You MUST write at least 250 words.',\n"
                    "    'Missing required elements: introduction, body paragraphs, and conclusion',\n"
                    "    'See below for how to develop your answer properly'\n"
                    "  ]\n\n"

                    "=== STEP 2: LANGUAGE FEEDBACK ===\n"
                    "Identify **2-5 key grammar and vocabulary issues**.\n"
                    "In 'how_to_improve_language', provide:\n"
                    "1. The original issue from the candidate's response\n"
                    "2. A corrected version\n"
                    "3. An alternative way to express it\n\n"
                    
                    "=== STEP 3: TASK ACHIEVEMENT FEEDBACK ===\n"
                    "Identify **2-3 key Task Achievement issues**.\n"
                    "In 'how_to_improve_answer', provide:\n"
                    "1. Response below 250 words\n"
                    "2. Missing thesis statement\n"
                    "3. Underdeveloped arguments\n"
                    "4. Missing examples\n"
                    "5. Paragraph organisation\n\n"
                    
                    "Example format:\n"
                    "{\n"
                    '  "issue": "Your essay lacks a clear thesis statement",\n'
                    '  "improved": "Start your introduction with a clear position. For example: While museums provide valuable cultural education, charging entrance fees can be necessary for their sustainability and development."\n'
                    "}\n\n"

                    "=== STEP 4: GENERATE IMPROVED RESPONSE ===\n"
                    "Generate an improved essay that:\n"
                    "- Meets the word count requirement\n"
                    "- Maintains the user's original ideas where relevant\n"
                    "- Uses the essay description as an example\n"
                    "- Has clear thesis and topic sentences\n"
                    "- Develops arguments with examples\n"
                    "- Uses academic vocabulary and complex grammar\n"
                    "- Has proper essay structure\n\n"

                    "=== OUTPUT FORMAT (STRICT JSON) ===\n"
                    "{\n"
                    '"how_to_improve_language": {\n'
                    '  "examples": [{\n'
                    '    "original": "text",\n'
                    '    "improved": ["correction", "alternative"]\n'
                    '  }]\n'
                    '},\n'
                    '"how_to_improve_answer": {\n'
                    '  "examples": [{\n'
                    '    "issue": "text",\n'
                    '    "improved": "text"\n'
                    '  }]\n'
                    '},\n'
                    '"improved_response": "complete rewritten essay"\n'
                    "}\n\n"

                    "=== IMPORTANT ===\n"
                    "- Always check word count first\n"
                    "- Ensure clear position on the topic\n"
                    "- Check argument development\n"
                    "- Return ONLY valid JSON\n"
                )
            },
            {
                "role": "user",
                "content": f"Evaluate this essay:\n\n{response}\n\nEssay Question:\n{task.main_prompt}\n\nEssay Description:\n{task.description}"
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
                                '      "original": "text",\n'
                                '      "improved": ["correction", "alternative"]\n'
                                '    }\n'
                                '  ]\n'
                                '},\n'
                                '"how_to_improve_answer": {\n'
                                '  "examples": [\n'
                                '    {\n'
                                '      "issue": "text",\n'
                                '      "improved": "text"\n'
                                '    }\n'
                                '  ]\n'
                                '},\n'
                                '"improved_response": "text"\n'
                                "}\n"
                                "\nEnsure 'improved' in how_to_improve_answer is a single string, not an array."
                            )
                        },
                        {
                            "role": "user",
                            "content": f"Evaluate this Writing Task 2 essay:\n\n{response}\n\nEssay Question:\n{task.main_prompt}"
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
