from django.shortcuts import render, get_object_or_404
from .models import JobPosting, Resume

def job_list(request):
    """Fetches all jobs from the database and sends them to the HTML page."""
    jobs = JobPosting.objects.all().order_by('-created_at')
    return render(request, 'core/job_list.html', {'jobs': jobs})

def job_detail(request, pk):
    """Fetches one specific job, and all the resumes tied to it."""
    job = get_object_or_404(JobPosting, pk=pk)
    
   
    resumes = job.resumes.all().order_by('-uploaded_at')
    
    return render(request, 'core/job_detail.html', {'job': job, 'resumes': resumes})