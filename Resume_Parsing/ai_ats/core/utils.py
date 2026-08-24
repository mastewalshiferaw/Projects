import json
import os
import re

from django.conf import settings
from openai import OpenAI
from pdfminer.high_level import extract_text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def extract_text_from_pdf(pdf_path):
    """Extract and sanitize raw text from PDF."""
    try:
        raw_text = extract_text(pdf_path)
        if not raw_text:
            return ""
   
        cleaned = re.sub(r"\s+", " ", raw_text)
        return cleaned.strip()
    except Exception as e:
        print(f"[PDF ERROR] {e}")
        return ""


def smart_local_matcher(raw_text, job_description):
    """Clean fallback if the Groq AI API fails or is offline."""
    print("[SYSTEM] AI Failed. Using clean local fallback.")
    return {
        "applicant_name": "Applicant (AI Offline)",
        "email": "N/A",
        "phone": "N/A",
        "location": "N/A",
        "years_of_experience": 0,
        "skills": ["Error: AI API Offline"],
        "match_score": 0,
        "match_breakdown": {
            "strong_matches": ["Could not generate: Please check your GROQ_API_KEY or internet connection."],
            "partial_matches": [],
            "missing_requirements": []
        },
        "ai_explanation": "The Groq AI API could not be reached. Please check Terminal 2 (Celery) to see why the API connection was refused."
    }
def parse_resume_with_ai(raw_text, job_description, is_student_mode=False):
    """Parses resume against a job description using Groq LLMs."""
    api_key = os.getenv("GROQ_API_KEY") or getattr(
        settings, "GROQ_API_KEY", None
    )
    if not api_key:
        return smart_local_matcher(raw_text, job_description)

    
    clean_resume = raw_text[:12000]
    clean_job = job_description[:8000]

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
        timeout=20.0,  
    )

    system_prompt = """You are an elite Applicant Tracking System (ATS) and Career Reviewer.
Evaluate the candidate's resume strictly against the provided Job Description.
You MUST respond in valid JSON matching this schema:
{
"applicant_name": "string",
"email": "string",
"phone": "string",
"location": "string",
"years_of_experience": 0,
"skills": ["string"],
"match_score": 0,
"match_breakdown": {
    "strong_matches": ["string"],
    "partial_matches": ["string"],
    "missing_requirements": ["string"]
},
"ai_explanation": "Summary of fit",
"improvement_suggestions": ["Actionable advice for the student on what bullet points or skills to add/fix"]
}
Score is 0-100. Be strict and realistic."""

    user_content = (
        f"JOB DESCRIPTION:\n{clean_job}\n\nRESUME TEXT:\n{clean_resume}"
    )

    # Stable, current Groq production models in order of capability
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

    for model_name in models:
        try:
            print(f"[AI] Parsing with {model_name}...")
            response = client.chat.completions.create(
                model=model_name,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.1,
            )
            raw_response = response.choices[0].message.content
            return json.loads(raw_response)
        except Exception as e:
            print(f"[AI ERROR] Model {model_name} failed: {e}")
            continue

    return smart_local_matcher(clean_resume, clean_job)