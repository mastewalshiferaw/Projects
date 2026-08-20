from celery import shared_task
from .models import Resume
from .utils import extract_text_from_pdf, parse_resume_with_ai

@shared_task(rate_limit='20/m')
def process_resume_task(resume_id):
    try:
        resume = Resume.objects.get(id=resume_id)
        resume.status = 'PROCESSING'
        resume.save()
        
        print(f"[CELERY] Extracting text for Resume ID: {resume_id}")
        raw_text = extract_text_from_pdf(resume.file.path)
        
        if raw_text:
            print(f"[CELERY] Sending text to Groq AI...")
            
            job_desc = resume.job.description
            ai_data = parse_resume_with_ai(raw_text, job_desc)
            
            if ai_data:
                # --- NEW RICH DATA FIELDS ---
                resume.applicant_name = ai_data.get('applicant_name', 'Unknown')
                resume.email = ai_data.get('email', 'Unknown')
                resume.phone = ai_data.get('phone', 'Unknown')
                resume.location = ai_data.get('location', 'Unknown')
                
                resume.years_of_experience = ai_data.get('years_of_experience', 0)
                resume.skills = ai_data.get('skills', [])
                
                resume.match_score = ai_data.get('match_score', 0)
                resume.match_breakdown = ai_data.get('match_breakdown', {})
                resume.ai_explanation = ai_data.get('ai_explanation', '')
                
                resume.status = 'COMPLETED'
                resume.save()
                print(f"[CELERY] Success! Match Score: {resume.match_score}%")
                return "Success"
            else:
                resume.status = 'FAILED'
                resume.save()
                return "Failed at AI Parsing"
        else:
            resume.status = 'FAILED'
            resume.save()
            return "Failed to extract text"
            
    except Resume.DoesNotExist:
        return "Resume not found"
    except Exception as e:
        print(f"[CELERY] Error: {e}")
        return "Error occurred"