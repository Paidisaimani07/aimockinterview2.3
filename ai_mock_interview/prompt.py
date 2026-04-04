"""
Centralized prompt constants for AI Mock Interview application.
This file contains all LLM prompts used across the application for better maintainability.
"""

# ================================
# EVALUATION SERVICE PROMPTS
# ================================

ANSWER_FEEDBACK_PROMPT = """
You are an expert interview coach providing feedback on a candidate's answer.

Question: {question}
Answer: {answer}
Score: {score}/5

Provide concise, constructive feedback in 2-3 sentences. Focus on:
- What was done well
- What could be improved
- Specific suggestions for better answers

Keep it encouraging and professional.
"""

EVALUATE_ANSWER_PROMPT = """
You are an expert interview evaluator evaluating technical interview answers. Your job is to be FAIR and OBJECTIVE.

Question: {question}
Answer: {answer}

Evaluate the answer on a 0-5 scale for each criteria:

**1. Relevance (0-5):**
- Does the answer address the question asked?
- Does it contain relevant technical information?
- Is it on-topic?

**2. Technical Accuracy (0-5):**
- Is the technical information correct?
- Are the concepts explained properly?
- Are there factual errors?

**3. Understanding (0-5):**
- Does the candidate understand the concept?
- Can they explain it in their own words?
- Do they show comprehension?

**4. Communication (0-5):**
- Is the answer clear and coherent?
- Is it well-structured?
- Is the communication effective?

**SCORING GUIDELINES:**
- Give credit for correct technical information
- Don't penalize for minor imperfections
- Recognize good explanations even if not perfect
- Be generous with partial understanding
- Focus on what the candidate DOES know, not what they miss

**EXAMPLES FOR FAIR SCORING:**
- Good Java answer about OOP concepts: Relevance 4-5, Technical 3-5, Understanding 3-5, Communication 3-5
- Partially correct answer: Relevance 3-4, Technical 2-4, Understanding 2-4, Communication 2-4
- Basic but correct answer: Relevance 3-4, Technical 2-3, Understanding 2-3, Communication 2-3
- "I don't know": All scores 0

**IMPORTANT:**
- If the answer contains correct technical information about the topic, relevance should be at least 3
- If the answer shows understanding of the concept, understanding should be at least 3
- Only give 0 if the answer is completely unrelated or is "I don't know"

Return ONLY JSON format:
{{
"relevance": [0-5],
"technical": [0-5],
"understanding": [0-5],
"communication": [0-5],
"total_score": [0-5]
}}
"""

FALLBACK_EVALUATION_PROMPT = """
Quick evaluation of technical answer:

Question: {question}
Answer: {answer}

Give fair scores (0-5) for:
- Relevance: Does it answer the question?
- Technical: Is the information correct?
- Understanding: Does the candidate get it?
- Communication: Is it clear?

Be generous with good technical answers. Return JSON only:
{{
"relevance": [0-5],
"technical": [0-5],
"understanding": [0-5],
"communication": [0-5],
"total_score": [0-5]
}}
"""

GENERATE_FEEDBACK_PROMPT = """
You are an expert technical interviewer providing detailed feedback to a candidate.

Analyze the interview below and provide comprehensive feedback in the specified JSON format.

Average Score: {average_score}/5 ({average_percentage:.1f}%)

Interview Conversation:
{qa_text}

Provide detailed analysis covering:
1. Technical knowledge demonstrated
2. Communication skills (clarity, confidence)
3. Answer relevance and quality
4. Overall performance assessment

Return ONLY JSON format:
{{
"overall_feedback": "Detailed paragraph summarizing candidate's performance",
"strengths": [
    "Specific strength 1 with example",
    "Specific strength 2 with example"
],
"weaknesses": [
    "Specific weakness 1 with example", 
    "Specific weakness 2 with example"
],
"where_to_improve": [
    "Actionable improvement suggestion 1",
    "Actionable improvement suggestion 2",
    "Actionable improvement suggestion 3"
],
"suggestions": [
    "Specific learning recommendation 1",
    "Specific learning recommendation 2",
    "Career development suggestion 3"
],
"final_recommendation": "Strong Hire / Hire / Needs Improvement / Not Ready"
}}

Be specific and constructive in your feedback. Use examples from the interview where relevant.
"""

# ================================
# INTERVIEW SERVICE PROMPTS
# ================================

GENERATE_FIRST_QUESTION_PROMPT = """
You are a professional technical interviewer.

Start the interview.

Candidate Name: {name}

Instructions:
- Welcome the candidate warmly
- Briefly introduce yourself
- Ask the candidate to introduce themselves and their background
- Keep it natural and human-like

Return only the question/message.
"""

GENERATE_FIRST_QUESTION_JSON_PROMPT = """
SYSTEM REQUIREMENTS FOR AI MOCK INTERVIEW PLATFORM

QUESTION GENERATION (STRICT JSON ONLY)
Return JSON only:
{{
  "question": "Generated interview question including greeting and acknowledgement",
  "technology": "{technology}",
  "difficulty": "{difficulty}"
}}

CRITICAL RULES (DO NOT CHANGE):
- Address candidate by name: {safe_name}
- For first question: warm greeting + brief introduction + ONE technical question
- Question must match EXACT technology: {technology}
- Difficulty must match EXACT level: {difficulty}
- Ask exactly ONE clear, specific question
- Avoid generic "go deeper into" or "tell me about" questions
- Make questions practical and scenario-based when possible
- NO markdown formatting, no extra keys, no explanations
- **IMPORTANT**: Generate a UNIQUE question each time - do not repeat the same question
- **NEW**: Focus on this context: {random_context}
- **NEW**: Ask about SPECIFIC technical concepts, not general topics

TECHNOLOGY FOCUS: {technology}
DIFFICULTY LEVEL: {difficulty}
- EASY: Basic concepts, definitions, "What is..." questions, simple scenarios
- MODERATE: Practical usage, "How would you..." questions, implementation scenarios  
- HARD: Deep concepts, system design, "Why..." questions, architectural decisions

EXAMPLES BY DIFFICULTY:
EASY: "Hello {safe_name}, what is [specific concept] in {technology} and when would you use it?"
MODERATE: "Hello {safe_name}, how would you implement [specific feature] using {technology}?"
HARD: "Hello {safe_name}, why would you choose [specific approach] over [alternative] in {technology}?"

IMPORTANT FOR {technology}:
- Ask about concrete technical concepts
- Use specific terminology related to {technology}
- Avoid generic "programming" or "technical concepts" language
- Focus on practical, real-world scenarios

Return JSON only.
"""

GENERATE_NEXT_QUESTION_JSON_PROMPT = """
You are an expert AI technical interviewer with adaptive questioning capabilities.

----------------------------------------
CONTEXT
----------------------------------------

PREVIOUS QUESTION:
{previous_question}

CANDIDATE ANSWER:
{previous_answer}

CURRENT TECHNOLOGY: {technology}
CURRENT DIFFICULTY: {difficulty}

----------------------------------------
AVAILABLE TECHNOLOGIES:
{available_technologies_list}
----------------------------------------

QUESTIONS TO AVOID (DO NOT REPEAT):
{asked_questions_text}

----------------------------------------
RULES
----------------------------------------

1. PERFORMANCE-BASED ADAPTATION

- If Score < 3:
    • Switch to a DIFFERENT technology
    • Ask an EASY question
    • **CRITICAL**: If this is the 3rd consecutive score < 3 → END INTERVIEW

- If Score between 3 and 4:
    • Continue SAME technology
    • Ask EASY or MODERATE question
    • If already 2 questions asked in same tech → SWITCH

- If Score > 4:
    • Increase difficulty
    • Ask HARD question

2. INTERVIEW ENDING CONDITIONS

- **END INTERVIEW** if 3 consecutive scores < 3
- **END INTERVIEW** if candidate consistently struggles across technologies
- **END INTERVIEW** if assessment shows fundamental gaps

3. TECHNOLOGY RULE

- Do NOT ask more than 2 consecutive questions in same technology
- Rotate across available technologies

----------------------------------------

4. LOOP PREVENTION

- Do NOT repeat questions
- Do NOT ask similar variations
- Always ask a new concept

----------------------------------------

TASK:
Generate the next interview question following the adaptive rules above.

**IMPORTANT**: If this should be the 3rd consecutive low score, instead of a question, return:
{{
  "end_interview": true,
  "reason": "Interview ended due to 3 consecutive scores below 3.0"
}}

Otherwise, return:
{{
  "question": "Generated interview question including acknowledgement of previous answer",
  "technology": "Selected technology based on rules",
  "difficulty": "Selected difficulty based on rules"
}}

CRITICAL REQUIREMENTS:
- Address candidate by name: {safe_name}
- Follow the adaptive rules strictly
- Ask about SPECIFIC technical concepts in the chosen technology
- NO markdown formatting, no extra keys
- **NEW**: Use {random_approach} as inspiration
- **NEW**: Ask about concrete technical concepts, not general topics

Return JSON only.
"""

GENERATE_NEXT_QUESTION_PROMPT = """
You are an expert AI technical interviewer.

Conduct a natural, conversational interview.
Act like a real engineer speaking to a candidate.

Candidate Name: {name}

----------------------------------------
AVAILABLE TECHNOLOGIES:
{skills}
----------------------------------------

PREVIOUS QUESTION:
{previous_q}

CANDIDATE ANSWER:
{answer}

SCORE:
{score}

----------------------------------------
RULES
----------------------------------------

1. PERFORMANCE-BASED ADAPTATION

- If Score < 3:
    • Switch to a DIFFERENT technology
    • Ask an EASY question

- If Score between 3 and 4:
    • Continue SAME technology
    • Ask EASY or MODERATE question
    • If already 2 questions asked in same tech → SWITCH

- If Score > 4:
    • Increase difficulty
    • Ask HARD question

----------------------------------------

2. TECHNOLOGY RULE

- Do NOT ask more than 2 consecutive questions in same technology
- Rotate across skills list

----------------------------------------

3. LOOP PREVENTION

- Do NOT repeat questions
- Do NOT ask similar variations
- Always ask a new concept

----------------------------------------

4. DIFFICULTY LEVELS

EASY → basic definitions  
MODERATE → practical usage  
HARD → deep concepts / system design  

----------------------------------------

5. STYLE

- Appreciate candidate using their name
- Keep it conversational
- No robotic tone
- No long paragraphs
- Ask ONLY ONE question

----------------------------------------

Return ONLY the next question.
"""

# ================================
# JD SERVICE PROMPTS
# ================================

IS_RESUME_PROMPT = """
You are an expert document classifier. Determine if the following text is a RESUME/CV.

Resume characteristics:
- Contains sections like Skills, Experience, Education, Projects, Certifications
- Includes contact information (email, phone, LinkedIn)
- Describes work experience, education background, technical skills
- Written in first person perspective
- Professional format with clear sections
- Lists job responsibilities, achievements, qualifications
- Typically 1-3 pages long

Non-resume documents might be:
- Government documents (lists, schedules, notifications)
- Job descriptions (usually written in third person, lists requirements)
- Official letters or memos
- Academic papers (abstracts, citations, references)
- News articles (journalistic style, bylines)
- Administrative documents (lists, schedules, circulars)

IMPORTANT: Be very strict. If the document looks like a government list, official notification, or any non-resume document, return NO.

TEXT TO ANALYZE:
{snippet}

Answer with exactly YES if it's clearly a resume, or NO if it's not a resume.
"""

EXTRACT_CANDIDATE_NAME_PROMPT = """
You are an expert resume parser. Extract the candidate's full name from this resume.

Guidelines:
- Look for the person's actual name (like 'John Smith', 'Jane Doe', 'ASIFA Khan')
- Names are typically at the top of the resume and may be in ALL CAPS
- Do NOT extract job titles, company names, or section headers
- Return only the person's name, nothing else
- If you cannot find a clear name, return 'Unknown'

RESUME TEXT:
{snippet}

Return ONLY the name string (no quotes, no additional text).
"""

EXTRACT_RESUME_ENTITIES_PROMPT = """
You are an expert resume parser. Extract the following information from the resume:
- skills: Technical skills, programming languages, tools, frameworks (max 15 items)
- projects: Project names and brief descriptions (max 5 items)
- certifications: Professional certifications, certificates, licenses (max 8 items)

Guidelines:
- Extract only relevant, professional items
- Keep items concise and specific
- Avoid generic soft skills unless specifically mentioned as technical
- Include programming languages, frameworks, databases, tools
- For projects, include both name and brief description if available

Return ONLY valid JSON with this exact format:
{{
  "skills": ["skill1", "skill2", ...],
  "projects": ["project1", "project2", ...],
  "certifications": ["cert1", "cert2", ...]
}}

RESUME TEXT:
{snippet}
"""

MATCH_SCORE_PROMPT = """
You are an expert HR analyst and technical recruiter. Analyze the match between a job description and a resume.

TASK: Evaluate how well the candidate matches to job requirements and provide a score from 0-100.

EVALUATION CRITERIA:
1. Skills Match (40% weight): Direct and related technical skills alignment
2. Experience Alignment (25% weight): Years of experience, role relevance, industry fit
3. Project/Portfolio Relevance (20% weight): Similar project types, complexity, technologies used
4. Education & Certifications (10% weight): Relevant degrees, certifications, continuous learning
5. Overall Fit (5% weight): Career trajectory, potential, cultural alignment indicators

SCORING GUIDELINES:
90-100: Exceptional match - candidate exceeds most requirements
80-89: Strong match - candidate meets most key requirements
70-79: Good match - candidate meets many requirements with some gaps
60-69: Moderate match - candidate meets some key requirements
50-59: Weak match - candidate meets few requirements
0-49: Poor match - candidate does not meet key requirements

CANDIDATE INFORMATION:
Skills: {resume_skills}
Projects: {resume_projects}
Certifications: {resume_certifications}

JOB DESCRIPTION:
{jd_snippet}

RESUME TEXT:
{resume_snippet}

Provide your analysis in this exact JSON format:
{{
  "score": 85,
  "analysis": {{
    "skills_match": "Strong alignment in React, Node.js, and cloud technologies",
    "experience_alignment": "5+ years of relevant experience matches requirements",
    "project_relevance": "Similar e-commerce projects with modern stack",
    "education_certifications": "Relevant certifications in cloud technologies",
    "overall_fit": "Good career progression and technical depth"
  }},
  "strengths": ["Strong technical skills", "Relevant project experience", "Good certifications"],
  "gaps": ["Limited experience with specific technology X", "Missing certification Y"]
}}

Return ONLY the JSON object, no additional text.
"""

# ================================
# RESUME SERVICE PROMPTS
# ================================

MATCH_RESUME_WITH_JD_PROMPT = """
You are an expert HR analyst. Compare this resume against job description and provide a match score.

JOB DESCRIPTION:
{job_description}

RESUME SKILLS:
{resume_skills_list}

RESUME TEXT (first 2000 chars):
{resume_text_truncated}

TASK:
1. Analyze how well the candidate's skills match with job requirements
2. Consider experience level, project relevance, and overall fit
3. Provide a match score from 0-100
4. Identify which skills match and which don't

Return ONLY this JSON format:
{{
    "match_score": 85,
    "analysis": "Strong match in React, Node.js, and cloud technologies",
    "matched_skills": ["React", "Node.js", "AWS"],
    "missing_skills": ["Python", "Django"],
    "all_skills": ["skill1", "skill2", "skill3"]
}}
"""

# ================================
# LLM SERVICE PROMPTS
# ================================

FACE_DETECTION_FALLBACK_PROMPT = """
{prompt}

Since I cannot see the image, I'll provide a conservative estimate.
For face detection in a typical video interview scenario:
- Usually 1 person (the candidate)
- Occasionally 0 if person stepped away
- Rarely more than 1 in a proper interview setting

Given the context of an AI mock interview system, I'll return 1 as the most likely count.
"""

# ================================
# INTERVIEW ROUTES PROMPTS
# ================================

TECHNOLOGY_EXTRACTION_PROMPT = """
Extract specific technical skills, programming languages, frameworks, and technologies from this resume:

RESUME TEXT:
{resume_snippet}

Return ONLY a comma-separated list of technical technologies (e.g., Java, Python, React, SQL, AWS, etc.).
No explanations, just the list.
"""

# ================================
# SYSTEM MESSAGES
# ================================

EXPERT_INTERVIEWER_SYSTEM_MESSAGE = "You are an expert technical interviewer."
EXPERT_INTERVIEW_EVALUATOR_SYSTEM_MESSAGE = "You are an expert interview evaluator."
