from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Job, Application, Activity, Notification, Interview

@receiver(post_save, sender=Job)
def create_job_posted_activity(sender, instance, created, **kwargs):
    """Create activity when a job is posted"""
    if created:
        Activity.objects.create(
            user=instance.employer.user,
            activity_type='job_posted',
            title=f"Nouvelle offre publiée: {instance.title}",
            description=f"Vous avez publié une nouvelle offre d'emploi: {instance.title}",
            related_job=instance
        )

@receiver(post_save, sender=Application)
def create_application_activity(sender, instance, created, **kwargs):
    """Create activity and notification when an application is submitted or status changes"""
    if created:
        # Activity for job seeker
        Activity.objects.create(
            user=instance.job_seeker.user,
            activity_type='job_applied',
            title=f"Candidature envoyée: {instance.job.title}",
            description=f"Vous avez postulé pour: {instance.job.title} chez {instance.job.employer.company_name}",
            related_job=instance.job,
            related_application=instance
        )
        
        # Notification for employer
        Notification.objects.create(
            user=instance.job.employer.user,
            notification_type='new_application',
            title=f"Nouvelle candidature",
            message=f"{instance.job_seeker.user.get_full_name() or instance.job_seeker.user.username} a postulé pour '{instance.job.title}'",
            link=f"/dashboard/",
            related_job=instance.job,
            related_application=instance
        )
    else:
        # Activity and notification when status changes
        update_fields = kwargs.get('update_fields')
        # If update_fields is None, Django saved all fields (including status)
        if update_fields is None or 'status' in update_fields:
            # Activity for job seeker
            Activity.objects.create(
                user=instance.job_seeker.user,
                activity_type='application_status',
                title=f"Statut mis à jour: {instance.job.title}",
                description=f"Le statut de votre candidature pour {instance.job.title} a été mis à jour: {instance.get_status_display()}",
                related_job=instance.job,
                related_application=instance
            )
            
            # Notification for job seeker about status change
            status_messages = {
                'accepted': f"Félicitations! Votre candidature pour '{instance.job.title}' a été acceptée!",
                'rejected': f"Votre candidature pour '{instance.job.title}' a été refusée.",
                'reviewing': f"Votre candidature pour '{instance.job.title}' est en cours de révision.",
            }
            
            if instance.status in status_messages:
                Notification.objects.create(
                    user=instance.job_seeker.user,
                    notification_type='application_status',
                    title=f"Statut de candidature mis à jour",
                    message=status_messages[instance.status],
                    link=f"/jobs/jobs/{instance.job.id}/" if instance.status != 'accepted' else f"/jobs/chat/{instance.id}/",
                    related_job=instance.job,
                    related_application=instance
                )


@receiver(post_save, sender=Interview)
def create_interview_notification(sender, instance, created, **kwargs):
    """Créer une notification lorsque un entretien est planifié."""
    if created:
        Notification.objects.create(
            user=instance.application.job_seeker.user,
            notification_type='new_interview',
            title='Nouvel entretien programmé',
            message=f"Un entretien a été programmé pour {instance.application.job.title} le {instance.scheduled_at.strftime('%d/%m/%Y à %H:%M')}",
            link=f"/interviews/{instance.id}/",
            related_job=instance.application.job,
            related_application=instance.application,
            related_interview=instance,
        )
        Activity.objects.create(
            user=instance.application.job_seeker.user,
            activity_type='job_applied',
            title=f"Entretien programmé: {instance.application.job.title}",
            description=f"Un entretien a été programmé pour {instance.application.job.title} le {instance.scheduled_at.strftime('%d/%m/%Y à %H:%M')}",
            related_job=instance.application.job,
            related_application=instance.application
        )

