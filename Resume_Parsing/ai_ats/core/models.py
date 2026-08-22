import uuid
from django.db import models

class JobPosting(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Paste the job description here.")
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.title

class Resume(models.Model):
    """For Candidates applying to a Recruiter's Job"""
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    applicant_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    
    years_of_experience = models.IntegerField(blank=True, null=True, default=0)
    skills = models.JSONField(blank=True, null=True, default=list)
    
    match_score = models.IntegerField(blank=True, null=True)
    match_breakdown = models.JSONField(blank=True, null=True)
    ai_explanation = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, default='PENDING')

    def __str__(self):
        return f"Resume for {self.job.title} - {self.applicant_name or 'Unknown'}"



#STUDENT SELF-SERVE ATS CHECK

class StudentATSCheck(models.Model):
    """For Students testing their own CV against a pasted Job Description"""
    job_description = models.TextField(help_text="The job the student wants to test against.")
    cv_file = models.FileField(upload_to='student_checks/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    match_score = models.IntegerField(blank=True, null=True)
    missing_skills = models.JSONField(blank=True, null=True, default=list)
    feedback_and_rewrites = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, default='PENDING')

    def __str__(self):
        return f"Student ATS Check - {self.uploaded_at.strftime('%Y-%m-%d')}"