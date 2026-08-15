# core/utils.py
import os
import json
from django.conf import settings # This forces the .env to load first!
from openai import OpenAI

def extract_text_from_pdf(pdf_path):
    """Reads a PDF and returns raw text."""
    try:
        # lazy import to avoid import-time failures in editors without deps
        from pdfminer.high_level import extract_text
        raw_text = extract_text(pdf_path)
        return raw_text.strip()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def parse_resume_with_ai(raw_text):
    """
    Sends raw text to Groq's Llama-3 model and asks for structured JSON back.
    """
    # Read model from env so we can switch when models are deprecated
    model = os.getenv('GROQ_MODEL')
    if not model:
        print("Groq model not configured. Set GROQ_MODEL in your .env to a supported model. See https://console.groq.com/docs/deprecations")
        return None

    system_prompt = """
    You are an expert HR assistant. Extract the following information from the resume text provided.
    You must respond ONLY in valid JSON format with these exact keys:
    {"applicant_name": "string", "email": "string", "skills": ["skill1", "skill2"]}
    """

    try:
       
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv('GROQ_API_KEY')
        )

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text}
            ],
            temperature=0.1,
        )
        
        ai_response_text = response.choices[0].message.content
        parsed_data = json.loads(ai_response_text)
        return parsed_data
        
    except Exception as e:
        err_str = str(e)
        if 'model_decommissioned' in err_str or 'decommissioned' in err_str:
            print("Groq API Error: model decommissioned. Update GROQ_MODEL to a supported model: https://console.groq.com/docs/deprecations")
        else:
            print(f"Groq API Error: {e}")
        return None