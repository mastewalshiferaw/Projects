import json
from django.conf import settings
from openai import OpenAI
from pdfminer.high_level import extract_text

# Initialize the OpenAI client using the key from our .env file
import os
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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
    Sends raw resume text to OpenAI and asks for structured JSON back.
    """
    # We tell the AI exactly what format we want.
    system_prompt = """
    You are an expert HR assistant. Extract the following information from the resume text provided.
    You must respond ONLY in valid JSON format with these exact keys:
    - "applicant_name": (string, or null if not found)
    - "email": (string, or null if not found)
    - "skills": (array of strings, e.g., ["Python", "Django", "React"])
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # The cheapest, fastest model
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
        print(f"OpenAI Error: {e}")
        return None