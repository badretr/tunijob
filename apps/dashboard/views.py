from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from apps.jobs.models import Job, Application, Notification, Interview
from django.db.models import Prefetch
from django.utils import timezone
from django.shortcuts import render

def home(request):
    return render(request, 'dashboard/home.html')

@login_required
def employer_dashboard(request):
    if not request.user.is_employer:
        messages.error(request, "Accès refusé. Compte employeur requis.")
        return redirect('jobs:home')
    
    all_posted_jobs = Job.objects.filter(employer=request.user.employer)
    posted_jobs = all_posted_jobs[:5]  # Limit to 5 for dashboard display
    all_applications = Application.objects.filter(
        job__employer=request.user.employer
    ).order_by('-applied_date')
    
    # Get status filter from request
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        all_applications = all_applications.filter(status=status_filter)
    
    # Count unread notifications
    unread_new_applications = Notification.objects.filter(
        user=request.user,
        notification_type='new_application',
        is_read=False
    ).count()
    
    # Get IDs of applications with unread notifications
    unread_new_application_ids = list(
        Notification.objects.filter(
            user=request.user,
            notification_type='new_application',
            is_read=False,
            related_application__isnull=False
        ).values_list('related_application_id', flat=True)
    )
    
    # Mark new application notifications as read when viewing dashboard
    if unread_new_applications > 0:
        Notification.objects.filter(
            user=request.user,
            notification_type='new_application',
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

    upcoming_interviews = Interview.objects.filter(
        application__job__employer=request.user.employer,
        status__in=['scheduled', 'rescheduled']
    ).select_related('application__job', 'application__job_seeker__user').order_by('scheduled_at')
    scheduled_interviews_count = upcoming_interviews.count()
    
    context = {
        'posted_jobs': posted_jobs,
        'applications': all_applications,
        'total_jobs': all_posted_jobs.count(),
        'total_applications': Application.objects.filter(
            job__employer=request.user.employer
        ).count(),
        'pending_applications': Application.objects.filter(
            job__employer=request.user.employer, status='pending'
        ).count(),
        'reviewing_applications': Application.objects.filter(
            job__employer=request.user.employer, status='reviewing'
        ).count(),
        'accepted_applications': Application.objects.filter(
            job__employer=request.user.employer, status='accepted'
        ).count(),
        'rejected_applications': Application.objects.filter(
            job__employer=request.user.employer, status='rejected'
        ).count(),
        'status_filter': status_filter,
        'unread_new_applications': unread_new_applications,
        'unread_new_application_ids': unread_new_application_ids,
        'upcoming_interviews': upcoming_interviews,
        'scheduled_interviews_count': scheduled_interviews_count,
    }
    return render(request, 'dashboard/employer_dashboard.html', context)

@login_required
def job_seeker_dashboard(request):
    if not request.user.is_job_seeker:
        messages.error(request, "Accès refusé. Compte candidat requis.")
        return redirect('jobs:home')
    
    all_applications = Application.objects.filter(
        job_seeker=request.user.jobseeker
    ).order_by('-applied_date').prefetch_related(
        Prefetch('interviews', queryset=Interview.objects.order_by('-updated_at'), to_attr='prefetched_interviews')
    )
    
    # Get status filter from request
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        all_applications = all_applications.filter(status=status_filter)
    
    # Count unread notifications
    unread_interview_notifications = Notification.objects.filter(
        user=request.user,
        notification_type='new_interview',
        is_read=False
    ).count()
    
    unread_status_notifications = Notification.objects.filter(
        user=request.user,
        notification_type='application_status',
        is_read=False
    ).count()

    # Fetch unread notifications to show as pop-up toasts on the dashboard
    new_notifications = Notification.objects.filter(
        user=request.user,
        notification_type__in=['application_status', 'new_interview'],
        is_read=False
    ).order_by('-created_at')[:5]
    
    # Get IDs of applications with unread status notifications
    unread_status_application_ids = list(
        Notification.objects.filter(
            user=request.user,
            notification_type='application_status',
            is_read=False,
            related_application__isnull=False
        ).values_list('related_application_id', flat=True)
    )
    
    # Mark these notifications as read when viewing dashboard
    if unread_status_notifications > 0 or unread_interview_notifications > 0:
        Notification.objects.filter(
            user=request.user,
            notification_type__in=['application_status', 'new_interview'],
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
    
    context = {
        'applications': all_applications,
        'total_applications': Application.objects.filter(
            job_seeker=request.user.jobseeker
        ).count(),
        'pending_applications': Application.objects.filter(
            job_seeker=request.user.jobseeker, status='pending'
        ).count(),
        'reviewing_applications': Application.objects.filter(
            job_seeker=request.user.jobseeker, status='reviewing'
        ).count(),
        'accepted_applications': Application.objects.filter(
            job_seeker=request.user.jobseeker, status='accepted'
        ).count(),
        'rejected_applications': Application.objects.filter(
            job_seeker=request.user.jobseeker, status='rejected'
        ).count(),
        'status_filter': status_filter,
        'unread_interview_notifications': unread_interview_notifications,
        'unread_status_notifications': unread_status_notifications,
        'unread_status_application_ids': unread_status_application_ids,
        'new_notifications': new_notifications,
    }
    return render(request, 'dashboard/job_seeker_dashboard.html', context)

@login_required
def manage_application(request, application_id):
    if not request.user.is_employer:
        messages.error(request, "Accès refusé.")
        return redirect('home')
    
    application = get_object_or_404(
        Application,
        id=application_id,
        job__employer=request.user.employer
    )
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Application.STATUS_CHOICES):
            application.status = new_status
            application.save()
            messages.success(request, "Statut de la candidature mis à jour avec succès !")
    
    dashboard_url = reverse('dashboard:employer_dashboard') + '#applications-section'
    return HttpResponseRedirect(dashboard_url)

@login_required
def edit_application(request, application_id):
    application = get_object_or_404(Application, id=application_id, job_seeker=request.user.jobseeker)
    
    if application.status not in ['pending', 'reviewing']:
        messages.error(request, "Vous ne pouvez modifier que les candidatures en attente ou en révision.")
        return redirect('dashboard:jobseeker_dashboard')
    
    if request.method == 'POST':
        application.cover_letter = request.POST.get('cover_letter')
        application.save()
        messages.success(request, "Candidature mise à jour avec succès !")
        return redirect('dashboard:jobseeker_dashboard')
    
    return redirect('dashboard:jobseeker_dashboard')

@login_required
def withdraw_application(request, application_id):
    if request.method == 'POST':
        application = get_object_or_404(Application, id=application_id, job_seeker=request.user.jobseeker)
        
        if application.status not in ['pending', 'reviewing']:
            messages.error(request, "Vous ne pouvez retirer que les candidatures en attente ou en révision.")
            return redirect('dashboard:jobseeker_dashboard')
        
        application.delete()
        messages.success(request, "Candidature retirée avec succès !")
    
    return redirect('dashboard:jobseeker_dashboard')
