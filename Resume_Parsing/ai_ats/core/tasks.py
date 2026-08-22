from celery import shared_task
from .models import Resume, StudentATSCheck
from .utils import extract_text_from_pdf, parse_resume_with_ai

@shared_task(rate_limit='20/m')
def process_resume_task(resume_id):
    """Processes CVs submitted to a Recruiter's Job (Public Apply)"""
    try:
        resume = Resume.objects.get(id=resume_id)
        resume.status = 'PROCESSING'
        resume.save()
        
        raw_text = extract_text_from_pdf(resume.file.path)
        if raw_text:
            ai_data = parse_resume_with_ai(raw_text, resume.job.description)
            if ai_data:
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
                return "Recruiter Resume Processed"
        resume.status = 'FAILED'
        resume.save()
    except Exception as e:
        print(f"Error: {e}")

@shared_task(rate_limit='20/m')
def process_student_check_task(check_id):
    """Processes CVs for the Student Self-Serve ATS Checker"""
    try:
        check = StudentATSCheck.objects.get(id=check_id)
        check.status = 'PROCESSING'
        check.save()
        
        raw_text = extract_text_from_pdf(check.cv_file.path)
        if raw_text:
            ai_data = parse_resume_with_ai(raw_text, check.job_description)
            if ai_data:
                check.match_score = ai_data.get('match_score', 0)
               
                breakdown = ai_data.get('match_breakdown', {})
                check.missing_skills = breakdown.get('missing_requirements', [])
                check.feedback_and_rewrites = ai_data.get('ai_explanation', '')
                
                check.status = 'COMPLETED'
                check.save()
                return "Student Check Processed"
        check.status = 'FAILED'
        check.save()
    except Exception as e:
        print(f"Error: {e}")