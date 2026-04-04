import json
import re

from services.llm_service import call_llm
from prompt import (
    IS_RESUME_PROMPT,
    EXTRACT_CANDIDATE_NAME_PROMPT,
    EXTRACT_RESUME_ENTITIES_PROMPT,
    MATCH_SCORE_PROMPT
)


def is_resume(text: str) -> bool:
    """
    Determine whether text is a resume using LLM with strict validation and regex fallback.
    """
    t = text or ""
    print(f"DEBUG: Using LLM for resume validation")
    
    # If text is very short, it's probably not a resume
    if len(t.strip()) < 100:
        print("DEBUG: Text too short, automatically not a resume")
        return False
    
    # Quick regex check for obvious non-resume content
    non_resume_patterns = [
        r'government of india', r'ministry of communications', r'department of posts',
        r'gds online engagement', r'shortlisted candidates', r'divisional office',
        r'list \d+', r'circle.*list', r'engagement schedule', r'postal.*service',
        r'official.*document', r'administrative', r'office.*memorandum'
    ]
    
    text_lower = t.lower()
    for pattern in non_resume_patterns:
        if re.search(pattern, text_lower):
            print(f"DEBUG: Found non-resume pattern: {pattern}")
            return False
    
    # Use LLM for resume validation
    snippet = t[:3000]
    prompt = safe_format_prompt(IS_RESUME_PROMPT, snippet=snippet)
    
    try:
        from services.llm_service import call_llm
        resp = call_llm(prompt) or ""
        resp = resp.strip().upper()
        is_resume_result = resp.startswith("YES")
        print(f"DEBUG: LLM resume validation result: {resp} -> {is_resume_result}")
        
        # If LLM fails or returns uncertain, use regex fallback
        if not resp or resp not in ["YES", "NO"]:
            print("DEBUG: Uncertain LLM response, using regex fallback")
            return _is_resume_regex_fallback(t)
            
        return is_resume_result
        
    except Exception as e:
        print(f"DEBUG: LLM resume validation error: {e}")
        # Use regex fallback
        return _is_resume_regex_fallback(t)


def _is_resume_regex_fallback(text: str) -> bool:
    """
    Fallback resume validation using regex patterns.
    """
    text_lower = text.lower()
    
    # Strong indicators of resume
    resume_indicators = [
        r'career objective', r'professional summary', r'work experience',
        r'education.*details?', r'technical skills', r'projects?[^a-z]',
        r'certifications?', r'contact.*me', r'email.*me', r'phone.*me',
        r'linkedin\.com', r'github\.com', r'portfolio', r'resume', r'curriculum vitae'
    ]
    
    # Strong indicators of non-resume
    non_resume_indicators = [
        r'government of', r'ministry of', r'department of', r'official',
        r'circular', r'notification', r'memorandum', r'list.*candidates',
        r'shortlisted', r'engagement.*schedule', r'divisional office',
        r'postal.*circle', r'administrative', r'office.*order'
    ]
    
    # Count matches
    resume_matches = sum(1 for pattern in resume_indicators if re.search(pattern, text_lower))
    non_resume_matches = sum(1 for pattern in non_resume_indicators if re.search(pattern, text_lower))
    
    print(f"DEBUG: Resume indicators: {resume_matches}, Non-resume indicators: {non_resume_matches}")
    
    # If we have strong non-resume indicators, reject
    if non_resume_matches >= 2:
        print("DEBUG: Strong non-resume indicators found, rejecting")
        return False
    
    # If we have good resume indicators and no strong non-resume indicators, accept
    if resume_matches >= 2 and non_resume_matches == 0:
        print("DEBUG: Good resume indicators found, accepting")
        return True
    
    # Default to rejection if unclear
    print("DEBUG: Unclear document type, defaulting to rejection")
    return False


def extract_candidate_name(resume_text: str) -> str:
    """
    Extract candidate name from resume using LLM with regex fallback.
    """
    t = resume_text or ""
    print(f"DEBUG: Using LLM for name extraction")
    
    # Use LLM for name extraction
    snippet = t[:4000]
    prompt = safe_format_prompt(EXTRACT_CANDIDATE_NAME_PROMPT, snippet=snippet)
    
    try:
        from services.llm_service import call_llm
        resp = call_llm(prompt) or ""
        resp = resp.strip().splitlines()[0].strip()
        print(f"DEBUG: LLM response for name: '{resp}'")
        
        # Basic cleanup
        resp = re.sub(r"[^A-Za-z.\' -]", "", resp).strip()
        result = resp[:60] if resp else ""
        print(f"DEBUG: Final extracted name: '{result}'")
        
        # If LLM couldn't find a name or returned something generic, use fallback
        if not result or result.lower() in ['unknown', 'name', 'candidate', 'not found']:
            print("DEBUG: LLM could not find name, using regex fallback")
            return _extract_name_with_regex(t)
            
        return result
        
    except Exception as e:
        print(f"DEBUG: LLM name extraction error: {e}")
        # Use regex fallback
        return _extract_name_with_regex(t)


def _extract_name_with_regex(text: str) -> str:
    """
    Fallback name extraction using regex patterns.
    """
    lines = text.splitlines()[:10]  # Check first 10 lines
    text_upper = text.upper()
    
    # Common name patterns
    name_patterns = [
        r'^([A-Z][a-z]+ [A-Z][a-z]+)',  # First Last
        r'^([A-Z]+ [A-Z]+)',             # ALL CAPS names
        r'^([A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+)',  # First Middle Last
        r'^([A-Z]\. [A-Z][a-z]+)',       # Initial Last
        r'^([A-Z][a-z]+ [A-Z]\.)',       # First Initial
    ]
    
    # Look for names in first few lines
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Skip lines that are clearly not names
        skip_patterns = [
            r'RESUME', r'CURRICULUM', r'VITAE', r'OBJECTIVE', r'EXPERIENCE',
            r'EDUCATION', r'SKILLS', r'CONTACT', r'EMAIL', r'PHONE', r'@',
            r'\d', r'http', r'www', r'.com', r'.net', r'.org'
        ]
        
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
            continue
            
        # Try each name pattern
        for pattern in name_patterns:
            match = re.search(pattern, line)
            if match:
                name = match.group(1).strip()
                # Validate name (2-3 words, letters only, reasonable length)
                if 2 <= len(name.split()) <= 3 and len(name) >= 3 and len(name) <= 50:
                    if re.fullmatch(r"[A-Za-z\. '\-]+", name):
                        print(f"DEBUG: Regex fallback found name: '{name}'")
                        return name
    
    print("DEBUG: Regex fallback could not find name")
    return ""


def safe_format_prompt(template, **kwargs):
    """Safely format a prompt template without interpreting JSON structures"""
    result = template
    for key, value in kwargs.items():
        result = result.replace(f'{{{key}}}', str(value))
    return result


def _extract_resume_entities(resume_text: str) -> dict:
    """
    Extract skills, projects, certifications from resume using only LLM.
    Returns a dict with keys: skills, projects, certifications.
    """
    text = resume_text or ""
    
    print(f"DEBUG: Using LLM for resume entity extraction")
    
    # Use LLM for all extraction
    snippet = text[:8000]
    prompt = EXTRACT_RESUME_ENTITIES_PROMPT.replace('{snippet}', snippet)
    
    try:
        from services.llm_service import call_llm
        content = call_llm(prompt) or ""
        print(f"DEBUG: LLM response for entities: {content[:200]}...")
        
        # Extract JSON from response
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if not match:
            print("DEBUG: No JSON found in LLM response, using empty arrays")
            return {"skills": [], "projects": [], "certifications": []}

        try:
            data = json.loads(match.group())
            result = {
                "skills": data.get("skills", [])[:15],  # Limit to 15
                "projects": data.get("projects", [])[:5],  # Limit to 5
                "certifications": data.get("certifications", [])[:8]  # Limit to 8
            }
            
            # Validate and clean data
            for key in result:
                result[key] = [item.strip() for item in result[key] if isinstance(item, str) and item.strip() and len(item.strip()) > 1]
            
            print(f"DEBUG: Extracted {len(result['skills'])} skills, {len(result['projects'])} projects, {len(result['certifications'])} certifications")
            return result
            
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON parsing error: {e}")
            return {"skills": [], "projects": [], "certifications": []}
            
    except Exception as e:
        print(f"DEBUG: LLM entity extraction error: {e}")
        return {"skills": [], "projects": [], "certifications": []}


def extract_resume_entities(resume_text: str) -> dict:
    return _extract_resume_entities(resume_text)


def match_score(jd: str, resume: str, entities: dict | None = None) -> int:
    """
    Compute match percentage (0-100) using LLM-based analysis.
    """
    print("="*50)
    print("DEBUG: LLM-BASED MATCHING SYSTEM ACTIVATED")
    print("="*50)
    
    jd_text = jd or ""
    resume_text = resume or ""
    
    print(f"DEBUG: Using LLM for JD-Resume matching")
    print(f"DEBUG: JD text length: {len(jd_text)}")
    print(f"DEBUG: Resume text length: {len(resume_text)}")

    # Extract skills using LLM if not provided
    if not entities:
        entities = extract_resume_entities(resume_text)
    
    resume_skills = entities.get("skills", [])
    resume_projects = entities.get("projects", [])
    resume_certifications = entities.get("certifications", [])
    
    print(f"DEBUG: Resume skills extracted: {resume_skills}")
    print(f"DEBUG: Resume projects extracted: {resume_projects}")
    print(f"DEBUG: Resume certifications extracted: {resume_certifications}")
    
    # Use LLM to analyze match and generate score
    jd_snippet = jd_text[:6000]
    resume_snippet = resume_text[:6000]
    
    prompt = safe_format_prompt(
        MATCH_SCORE_PROMPT,
        resume_skills=resume_skills,
        resume_projects=resume_projects,
        resume_certifications=resume_certifications,
        jd_snippet=jd_snippet,
        resume_snippet=resume_snippet
    )
    
    try:
        from services.llm_service import call_llm
        response = call_llm(prompt) or ""
        print(f"DEBUG: LLM response for matching: {response[:300]}...")
        
        # Check for rate limit error
        if response == "RATE_LIMIT_ERROR":
            print("DEBUG: Rate limit hit, using fallback scoring")
            return _fallback_score(jd_text, resume_text, entities)
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if not json_match:
            print("DEBUG: No JSON found in LLM response, using fallback scoring")
            return _fallback_score(jd_text, resume_text, entities)
        
        try:
            result = json.loads(json_match.group())
            score = int(result.get("score", 50))
            
            # Ensure score is within bounds
            score = min(100, max(0, score))
            
            print(f"DEBUG: LLM calculated score: {score}%")
            if "analysis" in result:
                print(f"DEBUG: Analysis: {result['analysis']}")
            if "strengths" in result:
                print(f"DEBUG: Strengths: {result['strengths']}")
            if "gaps" in result:
                print(f"DEBUG: Gaps: {result['gaps']}")
            
            return score
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"DEBUG: JSON parsing error: {e}")
            return _fallback_score(jd_text, resume_text, entities)
            
    except Exception as e:
        print(f"DEBUG: LLM matching error: {e}")
        return _fallback_score(jd_text, resume_text, entities)


def _fallback_score(jd: str, resume: str, entities: dict) -> int:
    """
    Fallback scoring method when LLM fails.
    """
    print("DEBUG: Using fallback scoring method")
    
    resume_skills = [skill.lower().strip() for skill in entities.get("skills", [])]
    
    # Basic keyword matching for fallback
    jd_lower = (jd or "").lower()
    common_skills = [
        "react", "javascript", "html", "css", "typescript", "nodejs", "angular", "vue",
        "python", "java", "c++", "c#", "sql", "mongodb", "postgresql", "mysql",
        "aws", "azure", "docker", "kubernetes", "git", "github", "gitlab",
        "frontend", "backend", "full stack", "ui", "ux", "api", "rest", "graphql"
    ]
    
    matches = sum(1 for skill in common_skills if skill in jd_lower and skill in resume_skills)
    base_score = min(60, matches * 10)
    
    # Add some bonus points for resume length and structure
    resume_text = resume or ""
    length_bonus = min(20, len(resume_text) // 100)
    structure_bonus = 20 if any(keyword in resume_text.lower() for keyword in ["experience", "projects", "skills"]) else 0
    
    final_score = base_score + length_bonus + structure_bonus
    final_score = min(100, max(0, final_score))
    
    print(f"DEBUG: Fallback score calculated: {final_score}%")
    return final_score

