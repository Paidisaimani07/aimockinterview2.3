import requests
import re
import json
from config import Config
from prompt import (
    ANSWER_FEEDBACK_PROMPT,
    EVALUATE_ANSWER_PROMPT,
    FALLBACK_EVALUATION_PROMPT,
    GENERATE_FEEDBACK_PROMPT,
    EXPERT_INTERVIEW_EVALUATOR_SYSTEM_MESSAGE
)

# -------------------------------
# LLM CALL (Reusable)
# -------------------------------

def call_llm(prompt, temperature=0):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {Config.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "llama-3.3-70b-versatile",
        # "model": "groq/compound-mini",
        "messages": [
            {"role": "system", "content": EXPERT_INTERVIEW_EVALUATOR_SYSTEM_MESSAGE},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        data = response.json()
        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("LLM Error:", e)
        return None


# -------------------------------
def generate_answer_feedback(question, answer, score):
    """Generate specific feedback for a single answer"""
    prompt = ANSWER_FEEDBACK_PROMPT.format(
        question=question,
        answer=answer,
        score=score.get('total_score', 0)
    )
    
    try:
        content = call_llm(prompt, temperature=0.7)
        if content and content.strip():
            # Clean up the response
            feedback = content.strip().replace('"', '').replace("'", "")
            return feedback[:300]  # Limit length
    except Exception as e:
        print(f"Error generating answer feedback: {e}")
    
    # Fallback feedback based on score
    score_val = score.get('total_score', 0)
    if score_val >= 4:
        return "Excellent answer! You demonstrated strong understanding and clear communication."
    elif score_val >= 3:
        return "Good answer with solid understanding. Consider adding more specific examples next time."
    elif score_val >= 2:
        return "Decent attempt. Try to provide more detailed technical explanations and examples."
    else:
        return "Keep practicing! Focus on understanding the core concepts and structuring your answers more clearly."

# ANSWER EVALUATION
# -------------------------------

def evaluate_answer(question, answer):
    prompt = EVALUATE_ANSWER_PROMPT.format(
        question=question,
        answer=answer
    )

    content = call_llm(prompt)

    if not content:
        print("DEBUG: LLM returned None, trying LLM fallback evaluation")
        return llm_fallback_evaluation(question, answer)

    print(f"DEBUG: LLM evaluation response: {content}")

    try:
        match = re.search(r"\{.*\}", content, re.DOTALL)

        if match:
            scores = json.loads(match.group())
            print(f"DEBUG: Parsed scores: {scores}")

            # Update safety checks for new criteria
            for key in ["relevance", "technical", "understanding", "communication"]:
                scores[key] = float(scores.get(key, 0))

            # Calculate total score as average of all criteria
            scores["total_score"] = round(
                (
                    scores["relevance"]
                    + scores["technical"]
                    + scores["understanding"]
                    + scores["communication"]
                ) / 4,
                2
            )

            print(f"DEBUG: Final scores: {scores}")
            return scores

    except Exception as e:
        print("Evaluation parsing error:", e)
        return default_score()

    print("DEBUG: No JSON match found in LLM response")
    return default_score()


def llm_fallback_evaluation(question, answer):
    """
    LLM-based fallback evaluation when primary LLM fails
    """
    # Try a different LLM service or simpler prompt
    try:
        fallback_prompt = FALLBACK_EVALUATION_PROMPT.format(
            question=question,
            answer=answer
        )
        content = call_llm(fallback_prompt)
        
        if content:
            print(f"DEBUG: Fallback LLM response: {content}")
            match = re.search(r"\{.*\}", content, re.DOTALL)
            
            if match:
                scores = json.loads(match.group())
                # Ensure all keys exist
                for key in ["relevance", "technical", "understanding", "communication"]:
                    scores[key] = float(scores.get(key, 0))
                
                scores["total_score"] = round(
                    (scores["relevance"] + scores["technical"] + scores["understanding"] + scores["communication"]) / 4,
                    2
                )
                
                print(f"DEBUG: Fallback evaluation scores: {scores}")
                return scores
                
    except Exception as e:
        print(f"Fallback LLM evaluation failed: {e}")
    
    # If all LLM attempts fail, return a neutral score for good answers
    if answer and len(answer.split()) > 10:
        print("DEBUG: All LLM failed, giving neutral score for substantial answer")
        return {
            "relevance": 3,
            "technical": 3,
            "understanding": 3,
            "communication": 3,
            "total_score": 3.0
        }
    
    return default_score()


def default_score():
    return {
        "relevance": 0,
        "technical": 0,
        "understanding": 0,
        "communication": 0,
        "total_score": 0
    }


# -------------------------------
# FINAL INTERVIEW FEEDBACK
# -------------------------------

def generate_feedback(average_score, questions, answers):
    qa_text = ""

    for i in range(len(answers)):
        q = questions[i]["question"]
        a = answers[i]["answer"]
        score = answers[i]["score"]["total_score"]
        relevance = answers[i]["score"].get("relevance", 0)
        clarity = answers[i]["score"].get("clarity", 0)
        confidence = answers[i]["score"].get("confidence", 0)

        qa_text += f"""
Question: {q}
Answer: {a}
Score: {score}/5
Relevance: {relevance}/5, Clarity: {clarity}/5, Confidence: {confidence}/5
"""

    prompt = GENERATE_FEEDBACK_PROMPT.format(
        average_score=average_score,
        average_percentage=(average_score/5)*100,
        qa_text=qa_text
    )

    content = call_llm(prompt, temperature=0.3)

    if not content:
        return default_feedback()

    try:
        match = re.search(r"\{.*\}", content, re.DOTALL)

        if match:
            return json.loads(match.group())

    except Exception as e:
        print("Feedback parsing error:", e)

    return default_feedback()


def default_feedback():
    return {
        "overall_feedback": "Unable to generate detailed feedback",
        "strengths": ["Unable to analyze strengths"],
        "weaknesses": ["Unable to analyze weaknesses"],
        "where_to_improve": ["Unable to generate improvement suggestions"],
        "suggestions": ["Unable to provide specific suggestions"],
        "final_recommendation": "Unknown"
    }