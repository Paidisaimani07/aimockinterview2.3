import requests
import base64
from config import Config
from prompt import FACE_DETECTION_FALLBACK_PROMPT

def call_grok(prompt):
    """
    Fallback function to call Grok API when Groq reaches rate limits
    """
    if not Config.GROK_API_KEY:
        print("DEBUG: Grok API key not configured")
        return None
    
    url = "https://api.x.ai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {Config.GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Add randomness to prompt for variety
    import random
    random_seed = random.randint(1, 999999)
    
    body = {
        "model": "grok-2-mini",  # Correct Grok model name
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random_seed,
        "top_p": 0.95
    }
    
    try:
        print("DEBUG: Trying Grok as fallback...")
        response = requests.post(url, headers=headers, json=body, timeout=60)
        
        if not response.ok:
            try:
                err_data = response.json()
                err = err_data.get("error", {}) if isinstance(err_data, dict) else {}
                err_msg = err.get("message", str(err_data)) if isinstance(err, dict) else str(err_data)
                print("DEBUG: Grok error:", response.status_code, err_msg)
            except:
                print("DEBUG: Grok error:", response.status_code, response.text[:200])
            return None
            
        try:
            data = response.json()
        except:
            print("DEBUG: Grok non-JSON response:", response.text[:200])
            return None
            
        choices = data.get("choices")
        if not choices:
            print("DEBUG: Grok response missing choices:", data)
            return None
            
        msg = choices[0].get("message", {})
        content = msg.get("content")
        print("DEBUG: Grok fallback successful!")
        return content
        
    except Exception as e:
        print("DEBUG: Grok request error:", e)
        return None

def call_llm(prompt):
    """
    Main LLM function with Groq primary and Grok fallback
    """
    # Try Groq first
    groq_result = call_groq_llm(prompt)
    
    # If Groq hits rate limit, try Grok
    if groq_result == "RATE_LIMIT_ERROR":
        print("DEBUG: Groq rate limit hit, switching to Grok...")
        grok_result = call_grok(prompt)
        
        if grok_result:
            return grok_result
        else:
            print("DEBUG: Both Groq and Grok failed")
            return "RATE_LIMIT_ERROR"
    
    return groq_result

def call_groq_llm(prompt):
    """
    Original Groq LLM function (renamed)
    """
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
        # "model": "groq/compound-mini",
        
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
            print("RATE LIMIT REACHED - Switching to Grok fallback")
            print("Visit: https://console.groq.com/settings/billing to upgrade")
            # Return a helpful message when rate limited
            return "RATE_LIMIT_ERROR"
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
    fallback_prompt = FACE_DETECTION_FALLBACK_PROMPT.format(
        prompt=prompt
    )
    
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