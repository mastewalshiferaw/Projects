from django.db import models

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