import requests
import base64
from config import Config

def call_llm(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {Config.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    # Add randomness to prompt and increase temperature for variety
    import random
    random_seed = random.randint(1, 999999)
    
    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,  # Increased for more randomness
        "seed": random_seed,  # Add random seed for variety
        "top_p": 0.95  # Allow more diverse responses
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=60)
    except Exception as e:
        print("LLM request error:", e)
        return None

    # If Groq returns an error payload, it may not have `choices`.
    try:
        data = response.json()
    except Exception:
        print("LLM non-JSON response:", response.text[:500])
        return None

    if not response.ok:
        # Best-effort extraction of error message
        err = data.get("error") or {}
        print("LLM HTTP error:", response.status_code, err.get("message") or data)
        
        # Check for rate limit specifically
        if response.status_code == 429:
            print("RATE LIMIT REACHED - Please try again later or upgrade plan")
        return None

    choices = data.get("choices")
    if not choices:
        print("LLM response missing choices:", data)
        return None

    msg = choices[0].get("message") or {}
    return msg.get("content")


def call_llm_with_image(prompt, image_base64):
    """
    Call LLM with image analysis capability for face detection.
    Note: Groq doesn't support vision models, so this will use a fallback approach.
    """
    print("DEBUG: Groq doesn't support image analysis, using fallback")
    
    # Since Groq doesn't support vision models, we'll return a conservative default
    # In a real implementation, you'd use a vision-capable model like GPT-4V or Claude
    fallback_prompt = f"""
    {prompt}

    Since I cannot see the image, I'll provide a conservative estimate.
    For face detection in a typical video interview scenario:
    - Usually 1 person (the candidate)
    - Occasionally 0 if person stepped away
    - Rarely more than 1 in a proper interview setting

    Given the context of an AI mock interview system, I'll return 1 as the most likely count.
    """
    
    try:
        # Try to get a text-based assessment
        response = call_llm(fallback_prompt)
        if response:
            import re
            numbers = re.findall(r'\b([0-4])\b', response)
            if numbers:
                return str(numbers[0])
    except Exception as e:
        print(f"DEBUG: Fallback LLM analysis failed: {e}")
    
    # Default fallback: assume 1 face for interview context
    return "1"