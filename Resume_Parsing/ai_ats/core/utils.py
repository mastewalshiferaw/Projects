import os
import json
import re
from openai import OpenAI
from pdfminer.high_level import extract_text
from django.conf import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def extract_text_from_pdf(pdf_path):
    """Extract and sanitize raw text from PDF."""
    try:
        raw_text = extract_text(pdf_path)
        if not raw_text:
            return ""
        # Remove multiple newlines, weird symbols, and excessive spaces
        cleaned = re.sub(r'\s+', ' ', raw_text)
        return cleaned.strip()
    except Exception as e:
        print(f"[PDF ERROR] {e}")
        return ""

def smart_local_matcher(raw_text, job_description):
    """
    Intelligent local fallback using TF-IDF vector similarity.
    Works offline with zero API calls.
    """
    print("[SYSTEM] Using Smart TF-IDF Local Matcher...")
    
    if not raw_text or not job_description:
        return {"match_score": 0, "ai_explanation": "Insufficient text provided."}

    # Calculate TF-IDF Cosine Similarity
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform([job_description, raw_text])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        score = int(similarity * 100)
    except Exception:
        score = 25  # safe default

    # Extract common technical/action keywords
    job_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', job_description.lower()))
    resume_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', raw_text.lower()))
    matched_skills = list(job_words.intersection(resume_words))[:8]
    missing_skills = list(job_words - resume_words)[:8]

    return {
        "applicant_name": "Applicant (Local Mode)",
        "email": "N/A",
        "phone": "N/A",
        "location": "N/A",
        "years_of_experience": 0,
        "skills": matched_skills,
        "match_score": score,
        "match_breakdown": {
            "strong_matches": matched_skills,
            "partial_matches": [],
            "missing_requirements": missing_skills
        },
        "ai_explanation": f"Calculated using local TF-IDF vector matching (Cosine Similarity: {score}%).",
        "improvement_suggestions": [
            f"Consider adding missing keywords found in the job description: {', '.join(missing_skills[:4])}."
        ]
    }

def parse_resume_with_ai(raw_text, job_description, is_student_mode=False):
    """
    Parses resume against a job description using Groq LLMs.
    """
    api_key = os.getenv('GROQ_API_KEY') or getattr(settings, 'GROQ_API_KEY', None)
    if not api_key:
        return smart_local_matcher(raw_text, job_description)

    # Sanitize & truncate text to prevent context blowup (max ~12,000 chars each)
    clean_resume = raw_text[:12000]
    clean_job = job_description[:8000]

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
        timeout=20.0  # Prevent hanging requests
    )

    system_prompt = f"""You are an elite Applicant Tracking System (ATS) and Career Reviewer.
Evaluate the candidate's resume strictly against the provided Job Description.

You MUST respond in valid JSON matching this schema:
{{
  "applicant_name": "string",
  "email": "string",
  "phone": "string",
  "location": "string",
  "years_of_experience": 0,
  "skills": ["string"],
  "match_score": 0,
  "match_breakdown": {{
    "strong_matches": ["string"],
    "partial_matches": ["string"],
    "missing_requirements": ["string"]
  }},
  "ai_explanation": "Summary of fit",
  "improvement_suggestions": ["Actionable advice for the student on what bullet points or skills to add/fix"]
}}
Score is 0-100. Be strict and realistic."""

    user_content = f"JOB DESCRIPTION:\n{clean_job}\n\nRESUME TEXT:\n{clean_resume}"

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
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
            )
            raw_response = response.choices[0].message.content
            return json.loads(raw_response)
        except Exception as e:
            print(f"[AI ERROR] Model {model_name} failed: {e}")
            continue

    return smart_local_matcher(clean_resume, clean_job)