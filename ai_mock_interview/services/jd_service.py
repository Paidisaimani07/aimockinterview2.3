import json
import re

from services.llm_service import call_llm


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
    prompt = (
        "You are an expert document classifier. Determine if the following text is a RESUME/CV.\n\n"
        "Resume characteristics:\n"
        "- Contains sections like Skills, Experience, Education, Projects, Certifications\n"
        "- Includes contact information (email, phone, LinkedIn)\n"
        "- Describes work experience, education background, technical skills\n"
        "- Written in first person perspective\n"
        "- Professional format with clear sections\n"
        "- Lists job responsibilities, achievements, qualifications\n"
        "- Typically 1-3 pages long\n\n"
        "Non-resume documents might be:\n"
        "- Government documents (lists, schedules, notifications)\n"
        "- Job descriptions (usually written in third person, lists requirements)\n"
        "- Official letters or memos\n"
        "- Academic papers (abstracts, citations, references)\n"
        "- News articles (journalistic style, bylines)\n"
        "- Administrative documents (lists, schedules, circulars)\n\n"
        "IMPORTANT: Be very strict. If the document looks like a government list, official notification, or any non-resume document, return NO.\n\n"
        f"TEXT TO ANALYZE:\n{snippet}\n\n"
        "Answer with exactly YES if it's clearly a resume, or NO if it's not a resume."
    )
    
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
    prompt = (
        "You are an expert resume parser. Extract the candidate's full name from this resume.\n\n"
        "Guidelines:\n"
        "- Look for the person's actual name (like 'John Smith', 'Jane Doe', 'ASIFA Khan')\n"
        "- Names are typically at the top of the resume and may be in ALL CAPS\n"
        "- Do NOT extract job titles, company names, or section headers\n"
        "- Return only the person's name, nothing else\n"
        "- If you cannot find a clear name, return 'Unknown'\n\n"
        "RESUME TEXT:\n"
        f"{snippet}\n\n"
        "Return ONLY the name string (no quotes, no additional text)."
    )
    
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


def _extract_resume_entities(resume_text: str) -> dict:
    """
    Extract skills, projects, certifications from resume using only LLM.
    Returns a dict with keys: skills, projects, certifications.
    """
    text = resume_text or ""
    
    print(f"DEBUG: Using LLM for resume entity extraction")
    
    # Use LLM for all extraction
    snippet = text[:8000]
    prompt = (
        "You are an expert resume parser. Extract the following information from the resume:\n"
        "- skills: Technical skills, programming languages, tools, frameworks (max 15 items)\n"
        "- projects: Project names and brief descriptions (max 5 items)\n"
        "- certifications: Professional certifications, certificates, licenses (max 8 items)\n\n"
        "Guidelines:\n"
        "- Extract only relevant, professional items\n"
        "- Keep items concise and specific\n"
        "- Avoid generic soft skills unless specifically mentioned as technical\n"
        "- Include programming languages, frameworks, databases, tools\n"
        "- For projects, include both name and brief description if available\n\n"
        "Return ONLY valid JSON with this exact format:\n"
        "{\n"
        '  "skills": ["skill1", "skill2", ...],\n'
        '  "projects": ["project1", "project2", ...],\n'
        '  "certifications": ["cert1", "cert2", ...]\n'
        "}\n\n"
        f"RESUME TEXT:\n{snippet}"
    )
    
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
    Compute match percentage (0-100) using rule-based scoring with LLM skill extraction.
    """
    print("="*50)
    print("DEBUG: RULE-BASED MATCHING SYSTEM ACTIVATED")
    print("="*50)
    
    jd_text = jd or ""
    resume_text = resume or ""
    
    print(f"DEBUG: Using rule-based JD-Resume matching")
    print(f"DEBUG: JD text length: {len(jd_text)}")
    print(f"DEBUG: Resume text length: {len(resume_text)}")

    # Extract skills using LLM (this works well)
    if not entities:
        entities = extract_resume_entities(resume_text)
    
    resume_skills = [skill.lower().strip() for skill in entities.get("skills", [])]
    print(f"DEBUG: Resume skills extracted: {resume_skills}")
    
    # Extract JD skills using simple keyword matching
    jd_skills = []
    common_tech_skills = [
        "react", "javascript", "html", "css", "typescript", "nodejs", "angular", "vue",
        "python", "java", "c++", "c#", "sql", "mongodb", "postgresql", "mysql",
        "aws", "azure", "docker", "kubernetes", "git", "github", "gitlab",
        "frontend", "backend", "full stack", "ui", "ux", "api", "rest", "graphql"
    ]
    
    jd_lower = jd_text.lower()
    for skill in common_tech_skills:
        if skill in jd_lower:
            jd_skills.append(skill)
    
    print(f"DEBUG: JD skills extracted: {jd_skills}")
    
    # Calculate matches
    direct_matches = 0
    related_matches = 0
    
    for jd_skill in jd_skills:
        if jd_skill in resume_skills:
            direct_matches += 1
            print(f"DEBUG: Direct match found: {jd_skill}")
        else:
            # Check for related skills
            related_map = {
                "javascript": ["nodejs", "typescript", "react", "angular", "vue"],
                "react": ["javascript", "typescript", "frontend"],
                "python": ["django", "flask", "fastapi"],
                "java": ["spring", "hibernate", "maven"],
                "sql": ["postgresql", "mysql", "mongodb", "database"],
                "frontend": ["html", "css", "javascript", "react", "vue", "angular"],
                "backend": ["nodejs", "python", "java", "sql", "api"],
                "full stack": ["frontend", "backend", "react", "nodejs", "sql"]
            }
            
            for related_skill in related_map.get(jd_skill, []):
                if related_skill in resume_skills:
                    related_matches += 1
                    print(f"DEBUG: Related match found: {jd_skill} -> {related_skill}")
                    break
    
    # Calculate score using the point system
    base_score = (direct_matches * 15) + (related_matches * 8)
    
    # Experience bonus (check for experience keywords)
    experience_keywords = ["years", "experience", "worked", "developed", "built", "created"]
    experience_bonus = min(25, sum(5 for keyword in experience_keywords if keyword in resume_text.lower()))
    
    # Project bonus (check for project keywords)
    project_keywords = ["project", "application", "system", "platform", "website", "app"]
    project_bonus = min(20, sum(4 for keyword in project_keywords if keyword in resume_text.lower()))
    
    final_score = base_score + experience_bonus + project_bonus
    final_score = min(100, max(0, final_score))
    
    print(f"DEBUG: Direct matches: {direct_matches} (×15 = {direct_matches * 15})")
    print(f"DEBUG: Related matches: {related_matches} (×8 = {related_matches * 8})")
    print(f"DEBUG: Experience bonus: {experience_bonus}")
    print(f"DEBUG: Project bonus: {project_bonus}")
    print(f"DEBUG: Final calculated score: {final_score}%")
    
    return final_score

