from django.urls import path
from . import views

urlpatterns = [
  
    path('', views.job_list, name='job_list'),
    
    # The job detail page (e.g., /job/1/)
    path('job/<int:pk>/', views.job_detail, name='job_detail'),

    path('candidate/<int:pk>/', views.resume_detail, name='resume_detail'),

    path('job/new/', views.job_create, name='job_create'),
    path('job/<int:job_id>/upload/', views.resume_upload, name='resume_upload'),
]