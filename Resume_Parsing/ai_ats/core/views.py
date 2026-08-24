from django.shortcuts import get_object_or_404, redirect, render

from .models import JobPosting, Resume, StudentATSCheck


# RECRUITER SIDE: MANAGE JOBS AND RESUMES

def job_list(request):
    """List all active job postings for the recruiter dashboard."""
    jobs = JobPosting.objects.order_by('-created_at')
    return render(request, 'core/job_list.html', {'jobs': jobs})


def job_detail(request, pk):
    """Show a single job posting and all candidate resumes for it."""
    job = get_object_or_404(JobPosting, pk=pk)
    resumes = job.resumes.order_by('-uploaded_at')
    return render(request, 'core/job_detail.html', {'job': job, 'resumes': resumes})


def job_create(request):
    """Create a new job posting from the recruiter dashboard."""
    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        description = (request.POST.get('description') or '').strip()

        if title and description:
            job = JobPosting.objects.create(title=title, description=description)
            return redirect('job_detail', pk=job.pk)

    return render(request, 'core/job_create.html')


def resume_detail(request, pk):
    """Show the AI analysis for a candidate resume."""
    resume = get_object_or_404(Resume, pk=pk)
    return render(request, 'core/resume_detail.html', {'resume': resume})


def resume_upload(request, job_id):
    """Upload a new resume for a specific job posting."""
    job = get_object_or_404(JobPosting, pk=job_id)

    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            resume = Resume.objects.create(job=job, file=uploaded_file)

            from .tasks import process_resume_task
            process_resume_task.delay(resume.id)
            return redirect('job_detail', pk=job.pk)

    return render(request, 'core/resume_upload.html', {'job': job})


# RECRUITER SIDE: PUBLIC APPLY LINK
def public_apply(request, public_id):
    """The public page where a student uploads their CV for a specific job."""
    job = get_object_or_404(JobPosting, public_id=public_id)

    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            resume = Resume.objects.create(job=job, file=uploaded_file)

            from .tasks import process_resume_task
            process_resume_task.delay(resume.id)

            return render(request, 'core/apply_success.html', {'job': job})

    return render(request, 'core/public_apply.html', {'job': job})


# STUDENT SIDE: SELF-SERVE ATS CHECKER

def student_ats_check(request):
    """Where a student pastes a Job Description and uploads their CV to get feedback."""
    if request.method == 'POST':
        job_desc = request.POST.get('job_description')
        cv_file = request.FILES.get('file')

        if job_desc and cv_file:
            ats_check = StudentATSCheck.objects.create(
                job_description=job_desc,
                cv_file=cv_file
            )

            from .tasks import process_student_check_task
            process_student_check_task.delay(ats_check.id)

            return redirect('student_ats_result', pk=ats_check.id)

    return render(request, 'core/student_ats_check.html')


def student_ats_result(request, pk):
    """Shows the student their Match Score, Missing Skills, and Feedback."""
    ats_check = get_object_or_404(StudentATSCheck, pk=pk)
    return render(request, 'core/student_ats_result.html', {'check': ats_check})

def landing_page(request):
    
    return render(request, 'core/landing.html')