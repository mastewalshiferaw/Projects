# core/utils.py
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

def parse_resume_with_ai(raw_text):
    """
    Enterprise AI parser with Fallback Mechanism and Advanced Extraction.
    """
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv('GROQ_API_KEY')
    )

    # We ask the AI for MUCH better data now to make the portfolio pop!
    system_prompt = """
    You are an expert ATS (Applicant Tracking System) AI. 
    Read the resume and return ONLY a valid JSON object with these exact keys:
    {
      "applicant_name": "string", 
      "email": "string", 
      "skills": ["skill1", "skill2"],
      "years_of_experience": "integer (calculate based on dates, 0 if none)",
      "summary": "A 2-sentence professional summary of the candidate."
    }
    """

    # FALLBACK STRATEGY: List of models to try in order
    models_to_try = [
        "llama-3.1-8b-instant",  # Primary: Fast and smart
        "mixtral-8x7b-32768"     # Fallback: Powerful open-source model
    ]

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
            return parsed_data  # If it works, return the data and stop the loop
            
        except Exception as e:
            print(f"[AI] Model {model_name} failed. Error: {e}")
            # The loop will naturally continue to the next model in the list!

    # If ALL models fail, return None so our Celery task knows to mark it as 'FAILED'
    print("[AI] CRITICAL: All AI models failed.")
    return None