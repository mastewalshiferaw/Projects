# core/models.py
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import extract_text_from_pdf, parse_resume_with_ai

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

    applicant_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    skills = models.JSONField(blank=True, null=True)
    match_score = models.IntegerField(blank=True, null=True)
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"Resume for {self.job.title} - {self.applicant_name or 'Unknown'}"



# THE AUTOMATION 

@receiver(post_save, sender=Resume)
def auto_process_resume(sender, instance, created, **kwargs):
    """
    This function runs AUTOMATICALLY every time a Resume is saved.
    """
    # We only want this to run the FIRST time it's uploaded (created=True)
    if created:
        print(f"New resume detected! Starting AI processing for: {instance.file.name}")
        
        # 1. Read the PDF
        raw_text = extract_text_from_pdf(instance.file.path)
        
        if raw_text:
            # 2. Ask OpenAI for the JSON data
            ai_data = parse_resume_with_ai(raw_text)
            
            if ai_data:
                # 3. Update the database fields with the AI's answers
                instance.applicant_name = ai_data.get('applicant_name', 'Unknown')
                instance.email = ai_data.get('email', 'Unknown')
                instance.skills = ai_data.get('skills', [])
                instance.status = 'COMPLETED'
                
                # 4. Save the new data!
                instance.save()
                print(f"Successfully processed {instance.applicant_name}")
            else:
                instance.status = 'FAILED'
                instance.save()


# core/models.py (bottom of the file)

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