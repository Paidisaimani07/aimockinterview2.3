import pdfplumber
import docx
from prompt import MATCH_RESUME_WITH_JD_PROMPT

def extract_text(file_path):
    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            return "\n".join([p.extract_text() or "" for p in pdf.pages])

    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

    return ""

def extract_skills_from_text(text):
    """
    Extract skills using regex patterns (no LLM)
    """
    skills = set()
    
    # Common technical skills patterns
    tech_patterns = [
        r'\b(Python|Java|JavaScript|React|Node\.js|Angular|Vue\.js|HTML|CSS|TypeScript)\b',
        r'\b(SQL|MySQL|PostgreSQL|MongoDB|Oracle|SQLite|Redis|Elasticsearch)\b',
        r'\b(AWS|Azure|GCP|Docker|Kubernetes|Terraform|Ansible)\b',
        r'\b(Git|GitHub|GitLab|Bitbucket|Jenkins|CI\/CD|DevOps)\b',
        r'\b(REST|GraphQL|API|Microservices|Serverless|Lambda)\b',
        r'\b(Mongo|Express|Django|Flask|Spring|\.NET|Laravel|Rails)\b',
        r'\b(Linux|Unix|Windows|macOS|Ubuntu|CentOS|Debian)\b',
        r'\b(Agile|Scrum|Kanban|Waterfall|DevOps|CI\/CD|TDD)\b'
    ]
    
    text_lower = text.lower()
    for pattern in tech_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                skills.add(match[0].title())
            else:
                skills.add(match.title())
    
    return list(skills)

def extract_certifications_from_text(text):
    """
    Extract certifications using regex patterns (no LLM)
    """
    certifications = []
    
    # Common certification patterns
    cert_patterns = [
        r'(AWS|Azure|GCP)\s+(Certified|Solutions|Architect|Professional|Developer)',
        r'(PMP|PRINCE2|Scrum|Agile)\s+(Certified|Master|Professional)',
        r'(Oracle|Microsoft|Cisco|CompTIA)\s+(Certified|Professional|Associate)',
        r'(Google|Facebook|Meta)\s+(Cloud|AI|ML|Data)\s+(Certified|Professional)',
        r'(ISTQB|CSTE|PMP)\s*(Certified|Foundation|Professional)',
        r'(Docker|Kubernetes|Jenkins|Git)\s+(Certified|Associate|Professional)'
    ]
    
    text_lower = text.lower()
    for pattern in cert_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                cert = ' '.join(match).title()
            else:
                cert = match.title()
            if cert not in certifications:
                certifications.append(cert)
    
    return certifications

def extract_projects_from_text(text):
    """
    Extract projects using regex patterns (no LLM)
    """
    projects = []
    
    # Project patterns
    project_patterns = [
        r'(Project|Application|System|Platform|Website|Portal|Dashboard):\s*([A-Za-z0-9\s]+)',
        r'Developed|Designed|Built|Created|Implemented|Architected\s+([A-Za-z0-9\s]+)',
        r'(E-commerce|Social|Banking|Education|Healthcare|Finance)\s+(Platform|System|App|Website)',
        r'(Full[- ]?stack|Front[- ]?end|Back[- ]?end)\s+(Project|Application|System)'
    ]
    
    text_lower = text.lower()
    for pattern in project_patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                project = f"{match[0]}: {match[1]}"
            else:
                project = match.title()
            if project not in projects:
                projects.append(project)
    
    return projects

def extract_resume_data(file_path):
    """
    Extract resume data using pdfplumber only (no LLM)
    """
    resume_text = extract_text(file_path)
    
    if not resume_text:
        return {
            "resume_text": "",
            "entities": {"skills": [], "projects": [], "certifications": []}
        }
    
    # Extract entities using regex (no LLM)
    skills = extract_skills_from_text(resume_text)
    projects = extract_projects_from_text(resume_text)
    certifications = extract_certifications_from_text(resume_text)
    
    return {
        "resume_text": resume_text,
        "entities": {
            "skills": skills[:15],  # Limit to 15
            "projects": projects[:5],    # Limit to 5
            "certifications": certifications[:8]  # Limit to 8
        }
    }

def match_resume_with_jd(resume_data, job_description):
    """
    Match resume against job description using LLM analysis
    """
    if not resume_data or not job_description:
        return {
            "match_score": 0,
            "analysis": "Missing resume or job description",
            "matched_skills": [],
            "missing_skills": []
        }
    
    resume_text = resume_data.get("resume_text", "")
    entities = resume_data.get("entities", {})
    resume_skills = entities.get("skills", [])
    
    try:
        # Use LLM for intelligent matching
        from services.llm_service import call_llm
        
        llm_prompt = MATCH_RESUME_WITH_JD_PROMPT.format(
            job_description=job_description,
            resume_skills_list=', '.join(resume_skills),
            resume_text_truncated=resume_text[:2000]
        )
        
        response = call_llm(llm_prompt)
        
        if response == "RATE_LIMIT_ERROR":
            # Fallback to simple keyword matching
            jd_lower = job_description.lower()
            matched_skills = [skill for skill in resume_skills if skill.lower() in jd_lower]
            missing_skills = [skill for skill in resume_skills if skill.lower() not in jd_lower]
            match_score = int((len(matched_skills) / max(1, len(resume_skills))) * 100) if resume_skills else 0
            
            return {
                "match_score": match_score,
                "analysis": f"Resume matches job description with {match_score}% compatibility (fallback analysis)",
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "all_skills": resume_skills
            }
        
        # Parse JSON response
        import json
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                match_score = min(100, max(0, int(result.get("match_score", 50))))
                
                return {
                    "match_score": match_score,
                    "analysis": result.get("analysis", f"Resume matches job description with {match_score}% compatibility"),
                    "matched_skills": result.get("matched_skills", []),
                    "missing_skills": result.get("missing_skills", []),
                    "all_skills": resume_skills
                }
            except (json.JSONDecodeError, ValueError):
                pass
    
    except Exception as e:
        print(f"DEBUG: LLM matching error: {e}")
    
    # Final fallback to simple keyword matching
    jd_lower = job_description.lower()
    matched_skills = [skill for skill in resume_skills if skill.lower() in jd_lower]
    missing_skills = [skill for skill in resume_skills if skill.lower() not in jd_lower]
    match_score = int((len(matched_skills) / max(1, len(resume_skills))) * 100) if resume_skills else 0
    
    return {
        "match_score": match_score,
        "analysis": f"Resume matches job description with {match_score}% compatibility",
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "all_skills": resume_skills
    }