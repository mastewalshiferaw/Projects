import os
import json
from django.conf import settings
from openai import OpenAI
from pdfminer.high_level import extract_text




client = OpenAI(
    base_url="https://api.groq/.com/openai/v1",
    api_key=os.getenv('OPENAI_API_KEY')

)

def extract_text_from_pdf(pdf_path):
    """Reads a PDF and returns raw text."""
    try:
        raw_text = extract_text(pdf_path)
        return raw_text.strip()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None

def parse_resume_with_ai(raw_text):
    """
      Sends raw text to Groq's Llama-3 model and asks for structured JSON back.
    """
    # We tell the AI exactly what format we want.
    system_prompt = """
   You are an expert HR assistant. Extract the following information from the resume text provided.
    You must respond ONLY in valid JSON format with these exact keys:
    {"applicant_name": "string", "email": "string", "skills": ["skill1", "skill2"]}
    """

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192", 
            response_format={ "type": "json_object" }, # Forces pure JSON output
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text}
            ],
            temperature=0.2, # Low temperature makes the AI more strict/factual
        )
        
        # Extract the text string from the AI's response
        ai_response_text = response.choices[0].message.content
        
        # Convert that text string into an actual Python dictionary
        parsed_data = json.loads(ai_response_text)
        return parsed_data
        
    except Exception as e:
        print(f"Groq API Error: {e}")
        return None