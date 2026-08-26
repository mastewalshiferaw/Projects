from django.urls import path
from . import views

urlpatterns = [

    path('', views.landing_page, name='landing_page'),
  
    path('', views.job_list, name='job_list'),
    
    # The job detail page (e.g., /job/1/)
    path('job/<int:pk>/', views.job_detail, name='job_detail'),

    path('candidate/<int:pk>/', views.resume_detail, name='resume_detail'),

    path('job/new/', views.job_create, name='job_create'),
    path('job/<int:job_id>/upload/', views.resume_upload, name='resume_upload'),

      
    path('apply/<uuid:public_id>/', views.public_apply, name='public_apply'),
    
    
    path('student/ats-check/', views.student_ats_check, name='student_ats_check'),
    path('student/ats-check/<int:pk>/', views.student_ats_result, name='student_ats_result'),

     # RECRUITER ROUTES
    path('recruiter/', views.job_list, name='job_list'),
    path('recruiter/job/<int:pk>/', views.job_detail, name='job_detail'),
    path('recruiter/candidate/<int:pk>/', views.resume_detail, name='resume_detail'),
    path('recruiter/job/new/', views.job_create, name='job_create'),
    path('recruiter/job/<int:job_id>/upload/', views.resume_upload, name='resume_upload'),
    
    # PUBLIC APPLY LINK
    path('apply/<uuid:public_id>/', views.public_apply, name='public_apply'),
    
    # STUDENT ROUTES 
    path('student/ats-check/', views.student_ats_check, name='student_ats_check'),
    path('student/ats-check/<int:pk>/', views.student_ats_result, name='student_ats_result'),

    path('signup/', views.signup, name='signup')
]