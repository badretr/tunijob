from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.home, name='home'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/post/', views.post_job, name='post_job'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
    path('jobs/<int:job_id>/edit/', views.edit_job, name='edit_job'),
    path('jobs/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    path('jobs/<int:job_id>/toggle-status/', views.toggle_job_status, name='toggle_job_status'),
    path('jobs/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('categories/', views.categories, name='categories'),
    path('companies/', views.companies, name='companies'),
    path('companies/<int:pk>/', views.company_detail, name='company_detail'),
    # Chat/Messaging URLs
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/<int:application_id>/', views.chat_detail, name='chat_detail'),
    path('api/check-new-messages/', views.check_new_messages, name='check_new_messages'),
    path('api/mark-message-read/<int:message_id>/', views.mark_message_read, name='mark_message_read'),
    
    # Social & Networking URLs
    path('activity/', views.activity_feed, name='activity_feed'),
    
    # Time Management URLs
    path('interviews/', views.interview_list, name='interview_list'),
    path('interviews/<int:interview_id>/', views.interview_detail, name='interview_detail'),
    path('interviews/<int:interview_id>/edit/', views.edit_interview, name='edit_interview'),
    path('interviews/<int:interview_id>/cancel/', views.cancel_interview, name='cancel_interview'),
    path('interviews/schedule/<int:application_id>/', views.schedule_interview, name='schedule_interview'),
    path('tasks/', views.task_list, name='task_list'),
    path('reminders/', views.reminder_list, name='reminder_list'),
    
    # Analytics & Insights URLs
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/export/', views.export_analytics, name='export_analytics'),
    
    # Communication Enhancement URLs
    path('message-templates/', views.message_templates, name='message_templates'),
    
    # Reviews & Ratings URLs (removed)
    # Candidate/company review endpoints were removed from the public UI per project settings.
]