from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/employer/', views.employer_signup, name='employer_signup'),
    path('signup/jobseeker/', views.jobseeker_signup, name='jobseeker_signup'),
     # Keep the historic short name `profile` and add `profile_settings` alias
     path('profil/', views.profile_settings, name='profile'),
     path('profil/', views.profile_settings, name='profile_settings'),
    path('profile/', views.user_profile, name='user_profile'),
    path('employer/profile/', views.employer_profile, name='employer_profile'),
    path('notifications/', views.notifications_center, name='notifications'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),
     # Resume Builder removed: routes deleted to disable CV creation UI
]