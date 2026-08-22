# core/views.py (Add to the bottom)
from .models import StudentATSCheck


# RECRUITER SIDE: PUBLIC APPLY LINK
def public_apply(request, public_id):
    """The public page where a student uploads their CV for a specific job."""
    job = get_object_or_404(JobPosting, public_id=public_id)
    
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            # Save the resume
            resume = Resume.objects.create(job=job, file=uploaded_file)
            
            # Send to background worker
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
            # Save the student's request
            ats_check = StudentATSCheck.objects.create(
                job_description=job_desc, 
                cv_file=cv_file
            )
            
            # Send to background worker
            from .tasks import process_student_check_task
            process_student_check_task.delay(ats_check.id)
            
            # Redirect to the loading/results page
            return redirect('student_ats_result', pk=ats_check.id)
            
    return render(request, 'core/student_ats_check.html')

def student_ats_result(request, pk):
    """Shows the student their Match Score, Missing Skills, and Feedback."""
    ats_check = get_object_or_404(StudentATSCheck, pk=pk)
    return render(request, 'core/student_ats_result.html', {'check': ats_check})