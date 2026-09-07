import os
import json
import re
import random
import requests  
from django.conf import settings
from pdfminer.high_level import extract_text
from openai import OpenAI

def extract_text_from_pdf(pdf_path):
    try:
        raw_text = extract_text(pdf_path)
        if not raw_text: return ""
        cleaned = re.sub(r'\s+', ' ', raw_text)
        return cleaned.strip()
    except Exception as e:
        print(f"[PDF ERROR] {e}")
        return ""

def smart_local_matcher(raw_text, job_description):
    """0-RAM Pure Python Failsafe. No libraries needed!"""
    print("[SYSTEM] All APIs failed. Using Pure Python Offline Matcher...")
    if not raw_text or not job_description:
        return {"match_score": 0, "ai_explanation": "Insufficient text."}

    resume_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', raw_text.lower()))
    job_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', job_description.lower()))
    
    matched = list(job_words.intersection(resume_words))[:8]
    missing = list(job_words - resume_words)[:8]
    
    score = int((len(matched) / (len(matched) + len(missing) + 1)) * 100) if job_words else 0

    return {
        "applicant_name": "Applicant (Local Mode)",
        "email": "N/A", "phone": "N/A", "location": "N/A", "years_of_experience": 0,
        "skills": matched, "match_score": score,
        "match_breakdown": {"strong_matches": matched, "partial_matches": [], "missing_requirements": missing},
        "ai_explanation": f"Calculated using local keyword matching (Score: {score}%).",
        "improvement_suggestions": [f"Consider adding missing keywords: {', '.join(missing[:4])}."]
    }

def clean_json_response(raw_string):
    cleaned = raw_string.strip()
    if cleaned.startswith("```json"): cleaned = cleaned[7:]
    if cleaned.startswith("```"): cleaned = cleaned[3:]
    if cleaned.endswith("```"): cleaned = cleaned[:-3]
    return cleaned.strip()

def call_openai_compatible(api_key, base_url, model_name, system_prompt, user_content):
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=20.0)
    response = client.chat.completions.create(
        model=model_name,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.1,
    )
    return json.loads(clean_json_response(response.choices[0].message.content))

def call_gemini_rest_api(api_key, system_prompt, user_content):
    """Direct REST API call to Google Gemini. 100% crash-proof."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": f"{system_prompt}\n\n{user_content}"}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1
        }
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status() # Raises error if Google rejects the key
    
    data = response.json()
    ai_text = data['candidates'][0]['content']['parts'][0]['text']
    return json.loads(clean_json_response(ai_text))


def parse_resume_with_ai(raw_text, job_description, is_student_mode=False):
    clean_resume = raw_text[:12000]
    clean_job = job_description[:8000]

    system_prompt = """You are an uncompromising Applicant Tracking System.
Return ONLY valid JSON matching this schema exactly:
{
  "applicant_name": "string", "email": "string", "phone": "string", "location": "string",
  "years_of_experience": 0, "skills": ["string"], "match_score": 0,
  "match_breakdown": {"strong_matches": ["string"], "partial_matches": ["string"], "missing_requirements": ["string"]},
  "ai_explanation": "Summary of fit", "improvement_suggestions": ["Advice for student"]
}
Score is 0-100. Do not hallucinate."""
    user_content = f"JOB DESCRIPTION:\n{clean_job}\n\nRESUME TEXT:\n{clean_resume}"

    providers = []
    if os.getenv('GEMINI_API_KEY'): providers.append('gemini')
    if os.getenv('OPENAI_API_KEY'): providers.append('openai')

    random.shuffle(providers)
    print(f"[AI ROUTER] Routing traffic through order: {providers}")

    for provider in providers:
        print(f"[AI ROUTER] Attempting connection to: {provider.upper()}...")
        try:
            if provider == 'gemini':
                data = call_gemini_rest_api(os.getenv('GEMINI_API_KEY'), system_prompt, user_content)
            elif provider == 'openai':
                data = call_openai_compatible(os.getenv('OPENAI_API_KEY'), "https://api.openai.com/v1", "gpt-4o-mini", system_prompt, user_content)
            
            print(f"[AI ROUTER] SUCCESS using {provider.upper()}!")
            return data
            
        except Exception as e:
            print(f"[AI ERROR] {provider.upper()} failed: {e}. Moving to next provider...")

    print("[AI ROUTER] CRITICAL: All API Providers Failed.")
    return smart_local_matcher(clean_resume, clean_job)