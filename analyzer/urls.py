from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/new/', views.job_create, name='job_create'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/upload/', views.upload_resume, name='job_upload_resume'),
    path('upload/', views.upload_resume, name='upload_resume'),
    path('evaluation/<int:eval_id>/', views.evaluation_detail, name='evaluation_detail'),
    path('evaluation/<int:eval_id>/interview/submit/', views.submit_interview_answer, name='submit_interview_answer'),
    path('evaluation/<int:eval_id>/pdf/', views.download_report_pdf, name='download_report_pdf'),
]
