import os
import json
from openai import OpenAI
from pdfminer.high_level import extract_text
from django.conf import settings

def extract_text_from_pdf(pdf_path):
    try:
        raw_text = extract_text(pdf_path)
        return raw_text.strip()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def parse_resume_with_ai(raw_text, job_description):
    """
    Enterprise matching engine. Extracts data and calculates a weighted score.
    """
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv('GROQ_API_KEY')
    )

    system_prompt = f"""
    You are an expert, highly objective ATS (Applicant Tracking System).
    Compare the following Candidate Resume against the Job Description.

    Job Description:
    "{job_description}"

    RULES:
    1. Do not hallucinate. If a skill is not explicitly in the resume, it is MISSING.
    2. Calculate a strict match score (0-100) based on: 
       - Required Skills (40%)
       - Experience match (25%)
       - Education match (15%)
       - Preferred skills/certs (20%)
    3. If a MANDATORY requirement (like years of experience) is missing, the score MUST drop significantly.

    You MUST return ONLY a valid JSON object with EXACTLY these keys:
    {
      "applicant_name": "string or null",
      "email": "string or null",
      "phone": "string or null",
      "location": "string or null",
      "years_of_experience": "integer. Calculate total professional experience based on dates. If unclear, or if dates are missing, output EXACTLY 0. DO NOT GUESS.",
      "skills": ["skill1", "skill2"],
      "match_score": "integer between 0 and 100",
      "match_breakdown": {
          "strong_matches": ["list of job requirements the candidate perfectly meets"],
          "partial_matches": ["list of requirements they partially meet"],
          "missing_requirements": ["list of job requirements totally missing from resume"]
      }},
      "ai_explanation": "A concise, 2-paragraph explanation of why they received this score."
    
    """

    models_to_try = ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]

    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"CANDIDATE RESUME:\n{raw_text}"}
                ],
                temperature=0.1,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"[AI] Model {model_name} failed. Error: {e}")

    return None