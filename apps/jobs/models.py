from django.db import models
from apps.accounts.models import Employer, JobSeeker

class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, help_text="FontAwesome icon class (e.g., 'fas fa-code')")
    
    def __str__(self):
        return self.name
    
    @property
    def job_count(self):
        return self.job_set.filter(is_active=True).count()

class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
    ]

    title = models.CharField(max_length=200)
    employer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='jobs')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    requirements = models.TextField()
    location = models.CharField(max_length=100)
    salary = models.CharField(max_length=100)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default='entry')
    posted_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-posted_date']

    def __str__(self):
        return self.title

class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('reviewing', 'En révision'),
        ('accepted', 'Acceptée'),
        ('rejected', 'Refusée'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    job_seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('job', 'job_seeker')

    def __str__(self):
        return f"{self.job_seeker.user.username} - {self.job.title}"
    
    def can_chat(self):
        """Check if chat is allowed (only for accepted applications)"""
        return self.status == 'accepted'

class Message(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField(blank=True)
    # Optional file attachment (pdf, images, etc.)
    attachment = models.FileField(upload_to='message_attachments/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"
    
    def mark_as_read(self):
        """Mark message as read"""
        from django.utils import timezone
        self.is_read = True
        if not self.read_at:
            self.read_at = timezone.now()
        self.save()

class Activity(models.Model):
    """Model for activity feed"""
    ACTIVITY_TYPES = [
        ('job_posted', 'Offre publiée'),
        ('job_applied', 'Candidature envoyée'),
        ('application_status', 'Statut de candidature modifié'),
        ('company_followed', 'Entreprise suivie'),
        ('profile_updated', 'Profil mis à jour'),
    ]
    
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    related_job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    related_application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Activities'
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"

# Time Management Models
class Interview(models.Model):
    """Model for scheduling interviews"""
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    scheduled_at = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    interview_type = models.CharField(max_length=50, choices=[
        ('phone', 'Téléphone'),
        ('video', 'Visio'),
        ('in_person', 'Présentiel'),
        ('online', 'Test en ligne'),
    ], default='in_person')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('scheduled', 'Planifié'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
        ('rescheduled', 'Replanifié'),
    ], default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_at']
    
    def __str__(self):
        return f"Interview for {self.application.job.title} - {self.scheduled_at}"

class Task(models.Model):
    """Model for task management"""
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Basse'),
        ('medium', 'Moyenne'),
        ('high', 'Haute'),
    ], default='medium')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', 'due_date']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

class Reminder(models.Model):
    """Model for reminders"""
    REMINDER_TYPES = [
        ('application_deadline', 'Date limite de candidature'),
        ('interview', 'Entretien'),
        ('follow_up', 'Relance'),
        ('task', 'Tâche'),
        ('custom', 'Personnalisé'),
    ]
    
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=50, choices=REMINDER_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    remind_at = models.DateTimeField()
    is_sent = models.BooleanField(default=False)
    related_application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True, blank=True, related_name='reminders')
    related_interview = models.ForeignKey(Interview, on_delete=models.CASCADE, null=True, blank=True, related_name='reminders')
    related_task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name='reminders')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['remind_at']
    
    def __str__(self):
        return f"{self.title} - {self.remind_at}"

# Communication Enhancement Models
class MessageTemplate(models.Model):
    """Model for message templates"""
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='message_templates')
    name = models.CharField(max_length=100)
    content = models.TextField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"

# Notification Model
class Notification(models.Model):
    """Model for user notifications"""
    NOTIFICATION_TYPES = [
        ('new_interview', 'Nouvel entretien'),
        ('interview_reminder', 'Rappel d’entretien'),
        ('application_status', 'Statut de candidature modifié'),
        ('new_application', 'Nouvelle candidature'),
        ('new_message', 'Nouveau message'),
        ('job_posted', 'Offre publiée'),
        ('job_updated', 'Offre mise à jour'),
    ]
    
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    link = models.CharField(max_length=255, blank=True, help_text="URL to navigate when notification is clicked")
    related_job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    related_application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    related_interview = models.ForeignKey(Interview, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        self.is_read = True
        if not self.read_at:
            self.read_at = timezone.now()
        self.save()

# Review and Rating Models
class CompanyReview(models.Model):
    """Model for job seekers to review companies after interview/application process"""
    REVIEW_TAGS = [
        ('fast_process', 'Processus rapide'),
        ('good_communication', 'Bonne communication'),
        ('professional', 'Professionnel'),
        ('transparent', 'Transparent'),
        ('respectful', 'Respectueux'),
        ('organized', 'Bien organisé'),
        ('slow_process', 'Processus lent'),
        ('poor_communication', 'Communication insuffisante'),
        ('unprofessional', 'Peu professionnel'),
    ]
    
    company = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey('accounts.JobSeeker', on_delete=models.CASCADE, related_name='company_reviews')
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='company_review', null=True, blank=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], help_text="Note de 1 à 5 étoiles")
    title = models.CharField(max_length=200, help_text="Titre de l'avis")
    comment = models.TextField(help_text="Commentaire détaillé")
    tags = models.JSONField(default=list, blank=True, help_text="Tags associés à l'avis")
    is_anonymous = models.BooleanField(default=False, help_text="Avis anonyme")
    is_verified = models.BooleanField(default=False, help_text="Avis vérifié (candidat a vraiment postulé)")
    is_approved = models.BooleanField(default=True, help_text="Avis approuvé par modération")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('company', 'reviewer', 'application')
        verbose_name = "Avis entreprise"
        verbose_name_plural = "Avis entreprises"
    
    def __str__(self):
        return f"{self.reviewer.user.username} - {self.company.company_name} ({self.rating}★)"
    
    def get_reviewer_display(self):
        """Get reviewer name or Anonymous"""
        if self.is_anonymous:
            return "Candidat anonyme"
        return self.reviewer.user.get_full_name() or self.reviewer.user.username


class CandidateReview(models.Model):
    """Model for employers to review candidates after interview/application process"""
    REVIEW_TAGS = [
        ('punctual', 'Ponctuel'),
        ('prepared', 'Bien préparé'),
        ('good_communication', 'Bonne communication'),
        ('professional', 'Professionnel'),
        ('qualified', 'Qualifié'),
        ('cultural_fit', 'Bonne intégration culturelle'),
        ('late', 'En retard'),
        ('unprepared', 'Mal préparé'),
        ('poor_communication', 'Communication insuffisante'),
        ('not_qualified', 'Non qualifié'),
    ]
    
    candidate = models.ForeignKey('accounts.JobSeeker', on_delete=models.CASCADE, related_name='candidate_reviews')
    reviewer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='candidate_reviews')
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='candidate_review', null=True, blank=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], help_text="Note de 1 à 5 étoiles")
    title = models.CharField(max_length=200, help_text="Titre de l'avis")
    comment = models.TextField(help_text="Commentaire détaillé")
    tags = models.JSONField(default=list, blank=True, help_text="Tags associés à l'avis")
    is_anonymous = models.BooleanField(default=False, help_text="Avis anonyme")
    is_verified = models.BooleanField(default=False, help_text="Avis vérifié (employeur a vraiment recruté)")
    is_approved = models.BooleanField(default=True, help_text="Avis approuvé par modération")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('candidate', 'reviewer', 'application')
        verbose_name = "Avis candidat"
        verbose_name_plural = "Avis candidats"
    
    def __str__(self):
        return f"{self.reviewer.company_name} - {self.candidate.user.username} ({self.rating}★)"
    
    def get_reviewer_display(self):
        """Get reviewer name or Anonymous"""
        if self.is_anonymous:
            return "Employeur anonyme"
        return self.reviewer.company_name

# CompanyReview and CandidateReview models removed per request — rating feature deleted
