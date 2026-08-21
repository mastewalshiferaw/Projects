from django.shortcuts import render, get_object_or_404, redirect
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

def resume_detail(request, pk):
    """Fetches a specific candidate's full profile and AI breakdown."""
    resume = get_object_or_404(Resume, pk=pk)
    return render(request, 'core/resume_detail.html', {'resume': resume})

def job_create(request):
    """Handles the creation of a new Job Posting from the UI."""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        
        if title and description:
            # Create and save the new job to the database
            JobPosting.objects.create(title=title, description=description)
            return redirect('job_list') # Send them back to the homepage
            
    return render(request, 'core/job_create.html')

def resume_upload(request, job_id):
    """Handles uploading a PDF resume to a specific job."""
    job = get_object_or_404(JobPosting, id=job_id)
    
    if request.method == 'POST':
        # Grab the uploaded file from request.FILES
        uploaded_file = request.FILES.get('file')
        
        if uploaded_file:
            
            Resume.objects.create(job=job, file=uploaded_file)
            return redirect('job_detail', pk=job.id)
            
    return render(request, 'core/resume_upload.html', {'job': job})