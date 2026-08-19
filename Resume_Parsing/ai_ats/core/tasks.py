from celery import shared_task
from .models import Resume
from .utils import extract_text_from_pdf, parse_resume_with_ai

@shared_task
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
                resume.applicant_name = ai_data.get('applicant_name', 'Unknown')
                resume.email = ai_data.get('email', 'Unknown')
                resume.skills = ai_data.get('skills', [])
                
                resume.match_score = ai_data.get('match_score', 0)
                
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