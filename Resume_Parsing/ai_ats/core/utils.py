import os
import json
import re
import random
from django.conf import settings
from pdfminer.high_level import extract_text
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
import google.generativeai as genai

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
    """Offline Failsafe using TF-IDF."""
    print("[SYSTEM] All APIs failed. Using Offline TF-IDF Matcher...")
    if not raw_text or not job_description:
        return {"match_score": 0, "ai_explanation": "Insufficient text."}
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform([job_description, raw_text])
        score = int(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0] * 100)
    except Exception:
        score = 25  
    job_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', job_description.lower()))
    resume_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', raw_text.lower()))
    matched = list(job_words.intersection(resume_words))[:8]
    missing = list(job_words - resume_words)[:8]
    return {
        "applicant_name": "Applicant (Local Mode)",
        "email": "N/A", "phone": "N/A", "location": "N/A", "years_of_experience": 0,
        "skills": matched, "match_score": score,
        "match_breakdown": {"strong_matches": matched, "partial_matches": [], "missing_requirements": missing},
        "ai_explanation": f"Calculated using local TF-IDF (Cosine Similarity: {score}%).",
        "improvement_suggestions": [f"Consider adding missing keywords: {', '.join(missing[:4])}."]
    }

def clean_json_response(raw_string):
    cleaned = raw_string.strip()
    if cleaned.startswith("```json"): cleaned = cleaned[7:]
    if cleaned.startswith("```"): cleaned = cleaned[3:]
    if cleaned.endswith("```"): cleaned = cleaned[:-3]
    return cleaned.strip()

def call_openai_compatible(api_key, base_url, model_name, system_prompt, user_content):
    """Helper function to call ANY OpenAI-compatible API."""
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

def call_gemini(api_key, system_prompt, user_content):
    """Helper function for Google Gemini."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(
        f"{system_prompt}\n\n{user_content}",
        generation_config=genai.GenerationConfig(response_mime_type="application/json", temperature=0.1)
    )
    return json.loads(clean_json_response(response.text))

def parse_resume_with_ai(raw_text, job_description, is_student_mode=False):
    """
    ULTIMATE LOAD-BALANCING AI ROUTER.
    Shuffles available APIs to distribute traffic and avoid rate limits.
    """
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
    if os.getenv('TOGETHER_API_KEY'): providers.append('together')
    if os.getenv('MISTRAL_API_KEY'): providers.append('mistral')
    if os.getenv('DEEPSEEK_API_KEY'): providers.append('deepseek')

    random.shuffle(providers)
    print(f"[AI ROUTER] Routing traffic through order: {providers}")

    for provider in providers:
        print(f"[AI ROUTER] Attempting connection to: {provider.upper()}...")
        try:
            if provider == 'gemini':
                data = call_gemini(os.getenv('GEMINI_API_KEY'), system_prompt, user_content)
            elif provider == 'openai':
                data = call_openai_compatible(os.getenv('OPENAI_API_KEY'), "https://api.openai.com/v1", "gpt-4o-mini", system_prompt, user_content)
            elif provider == 'together':
                data = call_openai_compatible(os.getenv('TOGETHER_API_KEY'), "https://api.together.xyz/v1", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", system_prompt, user_content)
            elif provider == 'mistral':
                data = call_openai_compatible(os.getenv('MISTRAL_API_KEY'), "https://api.mistral.ai/v1", "mistral-small-latest", system_prompt, user_content)
            elif provider == 'deepseek':
                data = call_openai_compatible(os.getenv('DEEPSEEK_API_KEY'), "https://api.deepseek.com", "deepseek-chat", system_prompt, user_content)
            
            print(f"[AI ROUTER] SUCCESS using {provider.upper()}!")
            return data
            
        except Exception as e:
            print(f"[AI ERROR] {provider.upper()} failed: {e}. Moving to next provider...")


    print("[AI ROUTER] CRITICAL: All providers failed.")
    return smart_local_matcher(clean_resume, clean_job)