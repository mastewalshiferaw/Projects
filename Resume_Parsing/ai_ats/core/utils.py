# core/utils.py
import os
import json
from openai import OpenAI
from pdfminer.high_level import extract_text
from django.conf import settings

def extract_text_from_pdf(pdf_path):
    try:
        raw_text = extract_text(pdf_path)
        return raw_text.strip() if raw_text else None
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def parse_resume_with_ai(raw_text, job_description):
    """
    Enterprise matching engine. Extracts data and calculates a weighted score
    using Dynamic Model Discovery to prevent deprecation crashes.
    """
    api_key = os.getenv('GROQ_API_KEY') or getattr(settings, 'GROQ_API_KEY', None)
    if not api_key:
        print("Error: GROQ_API_KEY is not set.")
        return None

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key
    )

    system_prompt = """You are an uncompromising, strict Applicant Tracking System (ATS) evaluator. Your task is to evaluate a candidate's resume against a job description with zero tolerance for hallucination.

### STRICT EVALUATION RULES:
1. ZERO HALLUCINATION POLICY:
   - A skill, tool, or qualification ONLY exists if explicitly stated in the resume text. 
   - Never assume or infer skills based on job titles (e.g., do NOT assume a "Frontend Developer" knows React unless "React" is explicitly written).

2. YEARS OF EXPERIENCE CALCULATION:
   - Calculate total years of experience ONLY using explicit start and end dates (e.g., "Jan 2020 - Dec 2022" = 3 years).
   - If dates are missing, overlapping, or vague (e.g., just "2020"), calculate only what is clearly proven.
   - If NO dates are provided at all, you MUST output 0 for `years_of_experience` and set `experience_dates_verified` to false. DO NOT GUESS.

3. STRICT MATCH SCORE CALCULATION (0 - 100):
   Evaluate four categories:
   - Required Skills Match (Max 40 pts): (Number of required skills found / Total required skills) * 40
   - Experience Match (Max 25 pts): Full points if candidate's verified years >= required years; scale down proportionally if less.
   - Education Match (Max 15 pts): Full points if required degree/level met; 0 if missing.
   - Preferred Skills / Certifications (Max 20 pts): (Preferred qualifications met / Total preferred) * 20
   
   *CRITICAL PENALTY:* If any MANDATORY requirement (minimum years of experience or a mandatory skill) is not explicitly proven, the total match score CANNOT exceed 49.

### OUTPUT FORMAT:
You MUST respond ONLY with a single valid JSON object following this schema:
{
  "applicant_name": "string or null",
  "email": "string or null",
  "phone": "string or null",
  "location": "string or null",
  "years_of_experience": 0,
  "experience_dates_verified": true,
  "skills": ["string"],
  "match_score": 0,
  "match_breakdown": {
    "strong_matches": ["Explicitly verified requirements found in resume"],
    "partial_matches": ["Requirements partially met or unclear"],
    "missing_requirements": ["Mandatory or preferred requirements not found in resume"]
  },
  "ai_explanation": "A concise, 1-paragraph summary detailing why the candidate received this exact score, citing explicit missing or matched items."
}"""

    user_content = f"""JOB DESCRIPTION:
\"\"\"{job_description}\"\"\"

CANDIDATE RESUME:
\"\"\"{raw_text}\"\"\""""

    # --- DYNAMIC MODEL DISCOVERY ---
    try:
        print("[AI] Fetching list of active models from Groq...")
        available_models = client.models.list().data
        # Filter for text-generation models (Llama, Mixtral, Gemma)
        models_to_try = [m.id for m in available_models if any(keyword in m.id.lower() for keyword in ["llama", "mixtral", "gemma"])]
        print(f"[AI] Found {len(models_to_try)} active models to use!")
    except Exception as e:
        print(f"[AI] Failed to fetch models from Groq. Error: {e}")
        # Failsafe fallback just in case the discovery API is down
        models_to_try = ["llama3-8b-8192", "llama-3.3-70b-versatile", "gemma2-9b-it"]

    # Try the available models one by one
    for model_name in models_to_try:
        try:
            print(f"[AI] Attempting extraction with model: {model_name}...")
            response = client.chat.completions.create(
                model=model_name,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.0,  # 0.0 gives the most deterministic and strict scoring
            )
            print(f"[AI] SUCCESS! Data extracted using {model_name}.")
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"[AI] Model {model_name} failed. Error: {e}")

    print("[AI] CRITICAL: All dynamically fetched AI models failed.")
    return None