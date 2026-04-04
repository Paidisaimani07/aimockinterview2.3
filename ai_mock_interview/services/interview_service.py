from services.llm_service import call_llm
from prompt import (
    GENERATE_FIRST_QUESTION_PROMPT,
    GENERATE_FIRST_QUESTION_JSON_PROMPT,
    GENERATE_NEXT_QUESTION_JSON_PROMPT,
    GENERATE_NEXT_QUESTION_PROMPT,
    EXPERT_INTERVIEWER_SYSTEM_MESSAGE
)


# -----------------------------------
# INITIAL QUESTION (FIRST QUESTION)
# -----------------------------------

def generate_first_question(name, jd, resume):
    prompt = GENERATE_FIRST_QUESTION_PROMPT.format(
        name=name
    )

    return call_llm(prompt)


# ------------------------------------------------------------
# STRICT JSON QUESTION GENERATION (REQUIRED CONTRACT)
# ------------------------------------------------------------
#
# Your system requirements require the LLM to output ONLY JSON:
# { "question": "...", "technology": "...", "difficulty": "EASY|MODERATE|HARD" }
#
# We keep the legacy string-based functions above for now, and add contract-based
# functions that backend code can call going forward.


def _extract_json_object(content: str) -> dict:
    if not content:
        return {}
    import re
    import json

    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except Exception:
        return {}


def generate_first_question_json(name: str, technology: str, difficulty: str = "EASY") -> dict:
    """
    First question with strict JSON-only LLM contract with enhanced randomness.
    """
    safe_name = name.strip() if isinstance(name, str) and name.strip() else "Candidate"
    import random
    
    # Add random context to encourage variety
    random_context = random.choice([
        "Start with a technical concept",
        "Begin with a practical scenario", 
        "Ask about fundamental principles",
        "Focus on real-world application",
        "Include a problem-solving element"
    ])
    
    prompt = GENERATE_FIRST_QUESTION_JSON_PROMPT.format(
        safe_name=safe_name,
        technology=technology,
        difficulty=difficulty,
        random_context=random_context
    )
    content = call_llm(prompt)
    
    # Check for rate limit error
    if content == "RATE_LIMIT_ERROR":
        print("DEBUG: Rate limit hit for first question, using fallback")
        return _get_fallback_first_question(name, technology, difficulty)
    
    data = _extract_json_object(content)
    if data.get("question"):
        return {
            "question": data.get("question"),
            "technology": data.get("technology", technology),
            "difficulty": data.get("difficulty", difficulty),
        }
    
    # If LLM fails, return empty dict - no fallback questions
    print("DEBUG: LLM failed to generate first question, no fallback available")
    return {}


def generate_next_question_json(
    name: str,
    previous_question: str,
    previous_answer: str,
    technology: str,
    difficulty: str,
    asked_questions: list,
) -> dict:
    """
    Next question with strict JSON-only LLM contract with enhanced randomness and adaptive logic.
    """
    safe_name = name.strip() if isinstance(name, str) and name.strip() else "Candidate"
    asked_questions_text = "\n".join(asked_questions[-10:]) if asked_questions else ""
    import random
    
    # Add random elements to encourage variety
    random_approach = random.choice([
        "Build on previous answer",
        "Explore different aspect", 
        "Challenge with new scenario",
        "Focus on practical implementation",
        "Include system design element"
    ])
    
    # Get available technologies from session (simulate this for now)
    available_technologies = ["Java", "Object-Oriented Programming", "Data Structures", "Algorithms", "Software Development"]
    
    prompt = GENERATE_NEXT_QUESTION_JSON_PROMPT.format(
        previous_question=previous_question,
        previous_answer=previous_answer,
        technology=technology,
        difficulty=difficulty,
        available_technologies_list=', '.join(available_technologies),
        asked_questions_text=asked_questions_text,
        safe_name=safe_name,
        random_approach=random_approach
    )
    content = call_llm(prompt)
    
    # Check for rate limit error
    if content == "RATE_LIMIT_ERROR":
        print("DEBUG: Rate limit hit for next question, using fallback")
        return _get_fallback_next_question(technology, difficulty, previous_question, previous_answer)
    
    data = _extract_json_object(content)
    
    # Check if LLM decided to end the interview
    if data.get("end_interview"):
        return {
            "end_interview": True,
            "reason": data.get("reason", "Interview ended due to consecutive low scores")
        }
    
    # Return normal question if interview continues
    if data.get("question"):
        return {
            "question": data.get("question"),
            "technology": data.get("technology", technology),
            "difficulty": data.get("difficulty", difficulty),
        }
    
    # If LLM fails, return empty dict - no fallback questions
    print("DEBUG: LLM failed to generate next question, no fallback available")
    return {}


# -----------------------------------
# NEXT QUESTION (ADAPTIVE)
# -----------------------------------

def generate_next_question(previous_q, answer, score, skills, name):
    prompt = GENERATE_NEXT_QUESTION_PROMPT.format(
        name=name,
        skills=skills,
        previous_q=previous_q,
        answer=answer,
        score=score
    )

    return call_llm(prompt)


def _get_fallback_next_question(technology, difficulty, previous_question, previous_answer):
    """Fallback next question generation when LLM fails"""
    fallback_questions = {
        "Java": [
            "Can you explain the difference between ArrayList and LinkedList in Java?",
            "What is polymorphism in Java and can you provide an example?",
            "How does garbage collection work in Java?"
        ],
        "Object-Oriented Programming": [
            "What are the four principles of object-oriented programming?",
            "Explain encapsulation with a real-world example.",
            "What is the difference between abstraction and encapsulation?"
        ],
        "Data Structures": [
            "What is the difference between a stack and a queue?",
            "Explain how a hash map works.",
            "What is time complexity and why is it important?"
        ],
        "Algorithms": [
            "Can you explain binary search and its time complexity?",
            "What is the difference between DFS and BFS?",
            "How would you reverse a linked list?"
        ],
        "Software Development": [
            "What version control systems have you used?",
            "How do you approach debugging a complex issue?",
            "What is your experience with agile methodologies?"
        ]
    }
    
    questions = fallback_questions.get(technology, fallback_questions["Software Development"])
    import random
    return {
        "question": random.choice(questions),
        "technology": technology,
        "difficulty": difficulty
    }


def _get_fallback_first_question(name, technology, difficulty):
    """Fallback first question generation when LLM fails"""
    fallback_questions = {
        "Java": [
            f"Hello, let's start with Java! Can you explain the main features of Java and why it's platform-independent?",
            f"Welcome! Let's discuss Java. What is the difference between JDK, JRE, and JVM?",
            f"Hi! Let's begin with Java. Can you explain what object-oriented programming means?"
        ],
        "Object-Oriented Programming": [
            f"Hello, let's talk about OOP! Can you explain the four principles of object-oriented programming?",
            f"Welcome! Let's discuss object-oriented concepts. What is encapsulation and why is it important?",
            f"Hi! Let's start with OOP fundamentals. Can you give an example of inheritance in programming?"
        ],
        "Data Structures": [
            f"Hello, let's explore data structures! What is a data structure and why do we need them?",
            f"Welcome! Let's discuss data structures. Can you explain the difference between an array and a linked list?",
            f"Hi! Let's start with data structures. What is time complexity and how do we analyze it?"
        ],
        "Algorithms": [
            f"Hello, let's dive into algorithms! What is an algorithm and can you give a simple example?",
            f"Welcome! Let's discuss algorithms. Can you explain what binary search is and when you'd use it?",
            f"Hi! Let's start with algorithms. What's the difference between linear and binary search?"
        ],
        "Software Development": [
            f"Hello, let's talk about software development! What programming languages are you comfortable with?",
            f"Welcome! Let's discuss your development experience. Can you tell me about a project you've worked on?",
            f"Hi! Let's start with your background. What inspired you to pursue software development?"
        ]
    }
    
    questions = fallback_questions.get(technology, fallback_questions["Software Development"])
    import random
    return {
        "question": random.choice(questions),
        "technology": technology,
        "difficulty": difficulty
    }

