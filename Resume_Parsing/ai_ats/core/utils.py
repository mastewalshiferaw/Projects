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
    Enterprise AI parser that compares a resume against a job description.
    """
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv('GROQ_API_KEY')
    )

    system_prompt = f"""
    You are an expert ATS (Applicant Tracking System). 
    I will provide you with a candidate's resume text.
    
    You must compare their resume against this Job Description:
    "{job_description}"
    
    Calculate a match score from 0 to 100 based on how well their skills and experience match the job description.
    
    Return ONLY a valid JSON object with these exact keys:
    {{
      "applicant_name": "string", 
      "email": "string", 
      "skills": ["skill1", "skill2"],
      "years_of_experience": "integer",
      "summary": "A 2-sentence professional summary.",
      "match_score": "integer between 0 and 100"
    }}
    """

    models_to_try = ["llama-3.1-8b-instant", "mixtral-8x7b-32768"]

    for model_name in models_to_try:
        print(f"[AI] Attempting extraction with model: {model_name}...")
        try:
            response = client.chat.completions.create(
                model=model_name,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_text}
                ],
                temperature=0.1,
            )
            
            ai_response_text = response.choices[0].message.content
            parsed_data = json.loads(ai_response_text)
            
            print(f"[AI] Success using {model_name}!")
            return parsed_data 
            
        except Exception as e:
            print(f"[AI] Model {model_name} failed. Error: {e}")

    print("[AI] CRITICAL: All AI models failed.")
    return None