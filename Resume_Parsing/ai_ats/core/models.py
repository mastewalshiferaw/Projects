from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class JobPosting(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Paste the job description here.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Resume(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

     # 1. Candidate Info
    applicant_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)

# 2. Structured Resume Data
    years_of_experience = models.IntegerField(blank=True, null=True, default=0)
    skills = models.JSONField(blank=True, null=True, default=list)
    
    # 3. The Match Engine Results
    match_score = models.IntegerField(blank=True, null=True)
    match_breakdown = models.JSONField(blank=True, null=True, help_text="Strong, Partial, and Missing matches")
    ai_explanation = models.TextField(blank=True, null=True)
    
    # 4. Pipeline & Status
    STATUS_CHOICES = [
        ('PENDING', 'Pending AI Screening'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Screening Completed'),
        ('FAILED', 'AI Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    PIPELINE_CHOICES = [
        ('APPLIED', 'Applied'),
        ('SHORTLISTED', 'Shortlisted'),
        ('INTERVIEW', 'Interviewing'),
        ('OFFER', 'Offer Extended'),
        ('HIRED', 'Hired'),
        ('REJECTED', 'Rejected'),
    ]
    pipeline_status = models.CharField(max_length=20, choices=PIPELINE_CHOICES, default='APPLIED')

    def __str__(self):
        return f"Resume for {self.job.title} - {self.applicant_name or 'Unknown'}"








# ==========================================
# THE AUTOMATION (DJANGO SIGNAL)
# ==========================================
@receiver(post_save, sender=Resume)
def auto_process_resume(sender, instance, created, **kwargs):
    """
    Triggers automatically when a Resume is saved.
    Sends the heavy lifting to the Celery background worker.
    """
    if created:
        print(f"New resume detected! Sending to Celery queue: {instance.file.name}")
        
        # We import the task down here to prevent "circular import" errors
        from .tasks import process_resume_task
        
        # .delay() is the magic Celery word. It means "Do this in the background!"
        process_resume_task.delay(instance.id)