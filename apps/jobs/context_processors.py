from .models import Message, Application, Notification

def unread_messages_count(request):
    """Context processor to add unread messages count and notifications to all templates"""
    if request.user.is_authenticated:
        # Get all accepted applications where user can chat
        if request.user.is_employer:
            applications = Application.objects.filter(
                job__employer=request.user.employer,
                status='accepted'
            )
        elif request.user.is_job_seeker:
            applications = Application.objects.filter(
                job_seeker=request.user.jobseeker,
                status='accepted'
            )
        else:
            applications = Application.objects.none()

        # Count total unread messages
        unread_count = Message.objects.filter(
            application__in=applications,
            receiver=request.user,
            is_read=False
        ).count()
        
        # Count unread notifications by type
        unread_notifications_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        # Count interview notifications specifically (new, cancelled, reminder)
        unread_interview_notifications_count = Notification.objects.filter(
            user=request.user,
            notification_type__in=['new_interview', 'interview_cancelled', 'interview_reminder'],
            is_read=False
        ).count()

        return {
            'unread_messages_count': unread_count,
            'has_unread_messages': unread_count > 0,
            'unread_notifications_count': unread_notifications_count,
            'has_unread_notifications': unread_notifications_count > 0,
            'unread_interview_notifications_count': unread_interview_notifications_count,
            'has_unread_interview_notifications': unread_interview_notifications_count > 0,
            # legacy key used in templates
            'unread_interview_notifications': unread_interview_notifications_count,
        }
    return {
        'unread_messages_count': 0,
        'has_unread_messages': False,
        'unread_notifications_count': 0,
        'has_unread_notifications': False,
    }


