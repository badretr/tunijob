from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import timedelta, datetime
from collections import namedtuple

from .models import (
    Job,
    Application,
    Category,
    Message,
    Interview,
    Task,
    Reminder,
    MessageTemplate,
    Activity,
    Notification,
)
from .forms import JobForm, JobApplicationForm, JobSearchForm, JobPostForm
from apps.accounts.models import Employer


def companies(request):
    """Liste des entreprises."""
    companies = Employer.objects.all()
    return render(request, 'jobs/companies.html', {'companies': companies})
def home(request):
    """Page d'accueil avec offres en vedette et catégories."""
    featured_jobs = Job.objects.filter(is_active=True)[:6]
    categories = Category.objects.all()
    context = {
        'featured_jobs': featured_jobs,
        'categories': categories,
    }
    return render(request, 'jobs/home.html', context)

def job_list(request):
    jobs = Job.objects.filter(is_active=True)
    
    # Initialize form with category choices
    categories = Category.objects.all()
    category_choices = [('', 'Toutes les catégories')] + [(cat.id, cat.name) for cat in categories]
    
    # Create form instance with dynamic category choices
    form_data = request.GET.copy()
    form = JobSearchForm(form_data)
    form.fields['category'].choices = category_choices

    # Filtres à partir du formulaire classique (recherche, localisation, catégorie, type de contrat)
    search = request.GET.get('search', '').strip()
    location = request.GET.get('location', '').strip()
    category_id = request.GET.get('category')
    job_type = request.GET.get('job_type', '').strip()

    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    if location:
        jobs = jobs.filter(location__icontains=location)
    if category_id:
        try:
            jobs = jobs.filter(category_id=int(category_id))
        except (ValueError, TypeError):
            pass  # Invalid category ID, ignore
    if job_type:
        jobs = jobs.filter(job_type=job_type)

    paginator = Paginator(jobs, 9)  # 9 offres par page
    page = request.GET.get('page')
    jobs = paginator.get_page(page)

    context = {
        'jobs': jobs,
        'form': form,
    }
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, is_active=True)
    application_form = JobApplicationForm() if request.user.is_authenticated else None
    has_applied = False

    if request.user.is_authenticated and hasattr(request.user, 'jobseeker'):
        has_applied = Application.objects.filter(
            job=job, job_seeker=request.user.jobseeker
        ).exists()

    context = {
        'job': job,
        'application_form': application_form,
        'has_applied': has_applied,
    }
    return render(request, 'jobs/job_detail.html', context)

@login_required
def post_job(request):
    """Créer une nouvelle offre (recruteur uniquement)."""
    if not hasattr(request.user, 'employer'):
        messages.error(request, "Seuls les recruteurs peuvent publier des offres.")
        return redirect('jobs:home')

    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = request.user.employer
            job.save()
            messages.success(request, "Offre publiée avec succès.")
            return redirect('jobs:job_detail', job_id=job.id)
    else:
        form = JobPostForm()

    return render(request, 'jobs/post_job.html', {'form': form})


@login_required
def edit_job(request, job_id):
    """Modifier une offre existante (recruteur propriétaire uniquement)."""
    if not hasattr(request.user, 'employer'):
        messages.error(request, "Seuls les recruteurs peuvent modifier des offres.")
        return redirect('jobs:home')

    job = get_object_or_404(Job, id=job_id, employer=request.user.employer)

    if request.method == 'POST':
        form = JobPostForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Offre mise à jour avec succès.")
            return redirect('jobs:job_detail', job_id=job.id)
    else:
        form = JobPostForm(instance=job)

    return render(request, 'jobs/post_job.html', {'form': form, 'job': job})


@login_required
def delete_job(request, job_id):
    """Supprimer une offre (recruteur propriétaire uniquement)."""
    if not hasattr(request.user, 'employer'):
        messages.error(request, "Seuls les recruteurs peuvent supprimer des offres.")
        return redirect('jobs:home')

    job = get_object_or_404(Job, id=job_id, employer=request.user.employer)

    if request.method == 'POST':
        job.delete()
        messages.success(request, "Offre supprimée avec succès.")
        return redirect('dashboard:employer_dashboard')

    # Pas de template de confirmation dédié pour l'instant
    return redirect('jobs:job_detail', job_id=job.id)


@login_required
def toggle_job_status(request, job_id):
    """Activer/Désactiver une offre (recruteur propriétaire uniquement)."""
    if request.method != 'POST':
        return redirect('dashboard:employer_dashboard')

    if not hasattr(request.user, 'employer'):
        messages.error(request, "Seuls les recruteurs peuvent modifier le statut des offres.")
        return redirect('jobs:home')

    job = get_object_or_404(Job, id=job_id, employer=request.user.employer)
    job.is_active = not job.is_active
    job.save(update_fields=['is_active'])

    if job.is_active:
        messages.success(request, "L'offre est maintenant active.")
    else:
        messages.info(request, "L'offre a été désactivée.")

    return redirect('dashboard:employer_dashboard')

@login_required
def apply_job(request, job_id):
    """Candidature à une offre (candidat uniquement)."""
    if not hasattr(request.user, 'jobseeker'):
        messages.error(request, "Seuls les candidats peuvent postuler aux offres.")
        return redirect('jobs:job_detail', job_id=job_id)

    job = get_object_or_404(Job, id=job_id, is_active=True)

    if Application.objects.filter(job=job, job_seeker=request.user.jobseeker).exists():
        messages.info(request, "Vous avez déjà postulé à cette offre.")
        return redirect('jobs:job_detail', job_id=job_id)

    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.job_seeker = request.user.jobseeker
            application.save()
            messages.success(request, "Votre candidature a été envoyée avec succès.")
            return redirect('dashboard:jobseeker_dashboard')
        else:
            messages.error(request, "Erreur lors de la soumission de votre candidature. Veuillez réessayer.")
            return redirect('jobs:job_detail', job_id=job_id)

    return redirect('jobs:job_detail', job_id=job_id)

def search_jobs(request):
    form = JobSearchForm(request.GET)
    jobs = Job.objects.filter(is_active=True)

    if form.is_valid():
        search = form.cleaned_data.get('search')
        location = form.cleaned_data.get('location')
        category = form.cleaned_data.get('category')
        job_type = form.cleaned_data.get('job_type')

        if search:
            jobs = jobs.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        if location:
            jobs = jobs.filter(location__icontains=location)
        if category:
            jobs = jobs.filter(category=category)
        if job_type:
            jobs = jobs.filter(job_type=job_type)

    paginator = Paginator(jobs, 9)  # 9 jobs per page
    page = request.GET.get('page')
    jobs = paginator.get_page(page)

    context = {
        'jobs': jobs,
        'form': form,
    }
    return render(request, 'jobs/search_results.html', context)

def categories(request):
    """Liste des catégories sur la page dédiée."""
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'jobs/categories.html', context)


def company_detail(request, pk):
    """Détail d'une entreprise avec ses offres actives."""
    company = get_object_or_404(Employer, pk=pk)
    active_jobs = Job.objects.filter(employer=company, is_active=True)
    # Ratings/reviews feature disabled: provide neutral values for templates
    context = {
        'company': company,
        'active_jobs': active_jobs,
        'avg_rating': 0,
        'total_reviews': 0,
        'recent_reviews': [],
    }
    return render(request, 'jobs/company_detail.html', context)


@login_required
def chat_list(request):
    """Liste des conversations pour l'utilisateur connecté."""
    if not (request.user.is_employer or request.user.is_job_seeker):
        messages.error(request, "Accès refusé.")
        return redirect('jobs:home')

    if request.user.is_employer:
        applications = Application.objects.filter(
            job__employer=request.user.employer,
            status='accepted',
        ).select_related('job', 'job_seeker__user', 'job__employer__user')
    else:
        applications = Application.objects.filter(
            job_seeker=request.user.jobseeker,
            status='accepted',
        ).select_related('job', 'job_seeker__user', 'job__employer__user')

    Conversation = namedtuple('Conversation', 'application other_user last_message unread_count')
    conversations = []

    for app in applications:
        last_message = app.messages.order_by('-created_at').first()
        unread_count = app.messages.filter(receiver=request.user, is_read=False).count()
        other_user = app.job_seeker.user if request.user.is_employer else app.job.employer.user

        conversations.append(
            Conversation(
                application=app,
                other_user=other_user,
                last_message=last_message,
                unread_count=unread_count,
            )
        )

    # Trier les conversations par dernier message (plus récent en premier)
    conversations.sort(key=lambda c: c.last_message.created_at if c.last_message else app.applied_date, reverse=True)

    return render(request, 'jobs/chat_list.html', {'conversations': conversations})


@login_required
def chat_detail(request, application_id):
    """Vue détaillée du chat pour une candidature acceptée."""
    application = get_object_or_404(Application, id=application_id)

    # Vérifier les permissions et le droit au chat
    if request.user.is_employer:
        if not hasattr(request.user, 'employer') or application.job.employer != request.user.employer:
            messages.error(request, "Accès refusé à cette conversation.")
            return redirect('jobs:chat_list')
    elif request.user.is_job_seeker:
        if application.job_seeker != request.user.jobseeker:
            messages.error(request, "Accès refusé à cette conversation.")
            return redirect('jobs:chat_list')
    else:
        messages.error(request, "Accès refusé.")
        return redirect('jobs:home')

    if not application.can_chat():
        messages.error(request, "Le chat est disponible uniquement pour les candidatures acceptées.")
        return redirect('dashboard:jobseeker_dashboard' if request.user.is_job_seeker else 'dashboard:employer_dashboard')

    other_user = application.job_seeker.user if request.user.is_employer else application.job.employer.user

    # Marquer les messages reçus comme lus
    application.messages.filter(receiver=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now(),
    )

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        attachment = request.FILES.get('attachment')

        # Basic validation: require either text or attachment
        if not content and not attachment:
            messages.error(request, "Veuillez saisir un message ou joindre un fichier.")
            return redirect('jobs:chat_detail', application_id=application.id)

        # Validate attachment size and type if provided
        if attachment:
            # 10 MB limit
            max_size = 10 * 1024 * 1024
            if attachment.size > max_size:
                messages.error(request, "Le fichier est trop volumineux (max 10MB).")
                return redirect('jobs:chat_detail', application_id=application.id)

            content_type = getattr(attachment, 'content_type', '')
            allowed = False
            if content_type.startswith('image/'):
                allowed = True
            if content_type == 'application/pdf':
                allowed = True
            if not allowed:
                messages.error(request, "Type de fichier non autorisé. Autorisé: images et PDF.")
                return redirect('jobs:chat_detail', application_id=application.id)

        Message.objects.create(
            application=application,
            sender=request.user,
            receiver=other_user,
            content=content,
            attachment=attachment if attachment else None,
        )
        return redirect('jobs:chat_detail', application_id=application.id)

    chat_messages = application.messages.select_related('sender').all()
    # Prefill from template if requested
    prefill_message = None
    template_id = request.GET.get('template_id')
    if template_id:
        try:
            tpl = MessageTemplate.objects.get(id=int(template_id), user=request.user)
            prefill_message = tpl.content
        except (ValueError, MessageTemplate.DoesNotExist):
            prefill_message = None

    templates = MessageTemplate.objects.filter(user=request.user).order_by('-is_default', 'name')

    context = {
        'application': application,
        'other_user': other_user,
        'chat_messages': chat_messages,
        'prefill_message': prefill_message,
        'templates': templates,
    }
    return render(request, 'jobs/chat_detail.html', context)


@login_required
def check_new_messages(request):
    """Retourne le nombre de nouveaux messages non lus (pour le header)."""
    unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
    return JsonResponse({'unread_count': unread_count, 'has_new': unread_count > 0})


@login_required
def mark_message_read(request, message_id):
    """Marquer un message comme lu (appelé via AJAX)."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

    try:
        message_obj = Message.objects.get(id=message_id, receiver=request.user)
    except Message.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Message introuvable'}, status=404)

    message_obj.mark_as_read()
    return JsonResponse({'success': True})


@login_required
def analytics_dashboard(request):
    """Tableau de bord analytique pour candidat ou recruteur."""
    # Tableau de bord candidat
    if request.user.is_job_seeker:
        qs = Application.objects.filter(job_seeker=request.user.jobseeker)
        total_applications = qs.count()

        responded = qs.exclude(status='pending').count()
        response_rate = round((responded * 100) / total_applications, 1) if total_applications else 0

        recent_applications = qs.filter(
            applied_date__gte=timezone.now() - timedelta(days=30)
        ).count()

        status_data = {
            'pending': qs.filter(status='pending').count(),
            'reviewing': qs.filter(status='reviewing').count(),
            'accepted': qs.filter(status='accepted').count(),
            'rejected': qs.filter(status='rejected').count(),
        }

        category_stats = (
            qs.values('job__category__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        context = {
            'total_applications': total_applications,
            'response_rate': response_rate,
            'recent_applications': recent_applications,
            'status_data': status_data,
            'category_stats': category_stats,
        }
        return render(request, 'jobs/analytics_jobseeker.html', context)

    # Tableau de bord recruteur
    if request.user.is_employer:
        jobs_qs = Job.objects.filter(employer=request.user.employer)
        total_jobs = jobs_qs.count()
        active_jobs = jobs_qs.filter(is_active=True).count()

        apps_qs = Application.objects.filter(job__employer=request.user.employer)
        total_applications = apps_qs.count()
        avg_applications = round(total_applications / total_jobs, 1) if total_jobs else 0

        status_data = {
            'pending': apps_qs.filter(status='pending').count(),
            'reviewing': apps_qs.filter(status='reviewing').count(),
            'accepted': apps_qs.filter(status='accepted').count(),
            'rejected': apps_qs.filter(status='rejected').count(),
        }

        popular_jobs = (
            jobs_qs.annotate(application_count=Count('applications'))
            .order_by('-application_count')[:5]
        )

        context = {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'total_applications': total_applications,
            'avg_applications': avg_applications,
            'status_data': status_data,
            'popular_jobs': popular_jobs,
        }
        return render(request, 'jobs/analytics_employer.html', context)

    messages.error(request, "Accès refusé.")
    return redirect('jobs:home')


@login_required
def export_analytics(request):
    """Exporter les statistiques au format CSV pour le profil connecté."""
    import csv

    if request.user.is_job_seeker:
        qs = Application.objects.filter(job_seeker=request.user.jobseeker).select_related('job__employer')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="analytics_candidat.csv"'

        writer = csv.writer(response)
        writer.writerow(['Offre', 'Entreprise', 'Statut', 'Date de candidature'])
        for app in qs:
            writer.writerow([
                app.job.title,
                app.job.employer.company_name,
                app.get_status_display(),
                timezone.localtime(app.applied_date).strftime('%d/%m/%Y %H:%M'),
            ])
        return response

    if request.user.is_employer:
        qs = Application.objects.filter(job__employer=request.user.employer).select_related('job', 'job_seeker__user')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="analytics_recruteur.csv"'

        writer = csv.writer(response)
        writer.writerow(['Candidat', 'Offre', 'Statut', 'Date de candidature'])
        for app in qs:
            writer.writerow([
                app.job_seeker.user.get_full_name() or app.job_seeker.user.username,
                app.job.title,
                app.get_status_display(),
                timezone.localtime(app.applied_date).strftime('%d/%m/%Y %H:%M'),
            ])
        return response

    messages.error(request, "Accès refusé.")
    return redirect('jobs:home')


@login_required
def message_templates(request):
    """Liste des modèles de messages de l'utilisateur (simple pour l'instant)."""
    # Handle create/delete via POST
    next_url = request.POST.get('next') or request.GET.get('next')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            name = request.POST.get('name', '').strip()
            content = request.POST.get('content', '').strip()
            is_default = bool(request.POST.get('is_default'))
            if name and content:
                if is_default:
                    # unset previous defaults for this user
                    MessageTemplate.objects.filter(user=request.user, is_default=True).update(is_default=False)
                MessageTemplate.objects.create(user=request.user, name=name, content=content, is_default=is_default)
                messages.success(request, 'Modèle créé avec succès.')
            else:
                messages.error(request, 'Le nom et le contenu sont requis pour créer un modèle.')
        elif action == 'delete':
            try:
                template_id = int(request.POST.get('template_id'))
                t = MessageTemplate.objects.get(id=template_id, user=request.user)
                t.delete()
                messages.success(request, 'Modèle supprimé.')
            except (ValueError, MessageTemplate.DoesNotExist):
                messages.error(request, 'Modèle introuvable.')

        # Redirect back to next if provided, else to templates list
        if next_url:
            return redirect(next_url)
        return redirect('jobs:message_templates')

    templates = MessageTemplate.objects.filter(user=request.user).order_by('-is_default', 'name')
    context = {'templates': templates, 'next': next_url}
    return render(request, 'jobs/message_templates.html', context)


@login_required
def activity_feed(request):
    """Fil d'activité de l'utilisateur connecté."""
    activities = Activity.objects.filter(user=request.user).select_related('related_job', 'related_application')
    return render(request, 'jobs/activity_feed.html', {'activities': activities})


@login_required
def interview_list(request):
    """Liste des entretiens liés à l'utilisateur (candidat ou recruteur)."""
    if request.user.is_employer:
        interviews = Interview.objects.filter(
            application__job__employer=request.user.employer
        ).select_related('application__job', 'application__job_seeker__user').order_by('-created_at')
    elif request.user.is_job_seeker:
        interviews = Interview.objects.filter(
            application__job_seeker=request.user.jobseeker
        ).select_related('application__job', 'application__job__employer__user').order_by('-created_at')
    else:
        messages.error(request, "Accès refusé.")
        return redirect('jobs:home')

    interview_notifications = Notification.objects.filter(
        user=request.user,
        notification_type__in=['new_interview', 'interview_cancelled', 'interview_reminder'],
        is_read=False
    )

    unread_interview_notifications = interview_notifications.count()
    unread_interview_ids = set(
        interview_notifications.filter(related_interview__isnull=False)
        .values_list('related_interview_id', flat=True)
    )

    context = {
        'interviews': interviews,
        'unread_interview_notifications': unread_interview_notifications,
        'unread_interview_ids': unread_interview_ids,
    }

    return render(request, 'jobs/interview_list.html', context)


@login_required
def interview_detail(request, interview_id):
    """Détail d'un entretien spécifique."""
    interview = get_object_or_404(Interview, id=interview_id)

    if request.user.is_employer:
        if interview.application.job.employer != request.user.employer:
            messages.error(request, "Accès refusé à cet entretien.")
            return redirect('jobs:interview_list')
    elif request.user.is_job_seeker:
        if interview.application.job_seeker != request.user.jobseeker:
            messages.error(request, "Accès refusé à cet entretien.")
            return redirect('jobs:interview_list')
    else:
        messages.error(request, "Accès refusé.")
        return redirect('jobs:home')

    Notification.objects.filter(
        user=request.user,
        related_interview=interview,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())

    return render(request, 'jobs/interview_detail.html', {'interview': interview})


@login_required
def edit_interview(request, interview_id):
    """Permettre à l'employeur de modifier un entretien (date, lieu, type, notes)."""
    if not request.user.is_employer:
        messages.error(request, "Accès refusé.")
        return redirect('jobs:home')

    interview = get_object_or_404(
        Interview,
        id=interview_id,
        application__job__employer=request.user.employer
    )

    if request.method == 'POST':
        scheduled_at = request.POST.get('scheduled_at')
        location = request.POST.get('location', '')
        interview_type = request.POST.get('interview_type', interview.interview_type)
        notes = request.POST.get('notes', '')

        try:
            # Parse datetime-local input
            parsed_datetime = datetime.fromisoformat(scheduled_at)
            parsed_datetime = timezone.make_aware(parsed_datetime) if timezone.is_naive(parsed_datetime) else parsed_datetime
        except Exception:
            messages.error(request, "Date/heure invalide.")
            return redirect('jobs:edit_interview', interview_id=interview.id)

        # Detect reschedule
        status_value = interview.status
        if interview.scheduled_at != parsed_datetime:
            status_value = 'rescheduled'

        interview.scheduled_at = parsed_datetime
        interview.location = location
        interview.interview_type = interview_type
        interview.notes = notes
        interview.status = status_value
        interview.save()

        Notification.objects.create(
            user=interview.application.job_seeker.user,
            notification_type='new_interview',
            title='Entretien mis à jour',
            message=f"Votre entretien pour {interview.application.job.title} a été mis à jour au {interview.scheduled_at.strftime('%d/%m/%Y à %H:%M')}",
            link=f'/interviews/{interview.id}/',
            related_job=interview.application.job,
            related_application=interview.application,
            related_interview=interview,
        )

        messages.success(request, "Entretien mis à jour avec succès.")
        return redirect('jobs:interview_list')

    context = {
        'interview': interview,
    }
    return render(request, 'jobs/edit_interview.html', context)


@login_required
def cancel_interview(request, interview_id):
    """Annuler un entretien programmé (employeur)."""
    if not request.user.is_employer:
        messages.error(request, "Accès refusé.")
        return redirect('jobs:home')

    interview = get_object_or_404(
        Interview,
        id=interview_id,
        application__job__employer=request.user.employer
    )

    if interview.status in ['scheduled', 'rescheduled']:
        interview.status = 'cancelled'
        interview.save()

        Notification.objects.create(
            user=interview.application.job_seeker.user,
            notification_type='interview_cancelled',
            title='Entretien annulé',
            message=f"Votre entretien pour {interview.application.job.title} a été annulé.",
            link=f'/interviews/{interview.id}/',
            related_job=interview.application.job,
            related_application=interview.application,
            related_interview=interview,
        )
        messages.success(request, "Entretien annulé.")
    else:
        messages.warning(request, "Cet entretien ne peut pas être annulé.")

    return redirect('jobs:interview_list')


@login_required
def schedule_interview(request, application_id):
    """Planifier rapidement un entretien depuis le chat (version simple)."""
    if not request.user.is_employer:
        messages.error(request, "Seuls les recruteurs peuvent programmer des entretiens.")
        return redirect('jobs:home')

    application = get_object_or_404(
        Application,
        id=application_id,
        job__employer=request.user.employer,
    )

    if request.method == 'POST':
        # Récupérer les données du formulaire
        scheduled_at = request.POST.get('scheduled_at')
        location = request.POST.get('location', '')
        interview_type = request.POST.get('interview_type', 'in_person')
        notes = request.POST.get('notes', '')

        try:
            # Parser la date/heure
            scheduled_datetime = datetime.fromisoformat(scheduled_at)
            scheduled_datetime = timezone.make_aware(scheduled_datetime) if timezone.is_naive(scheduled_datetime) else scheduled_datetime
            
            # Créer l'entretien
            interview = Interview.objects.create(
                application=application,
                scheduled_at=scheduled_datetime,
                location=location,
                interview_type=interview_type,
                notes=notes,
                status='scheduled'
            )
            
            messages.success(request, "Entretien programmé avec succès!")
            return redirect('jobs:interview_list')
        except ValueError as e:
            messages.error(request, f"Erreur de date/heure invalide: {str(e)}")
        except Exception as e:
            messages.error(request, f"Erreur lors de la programmation: {str(e)}")

    # Utiliser le template existant pour les détails de planification
    return render(request, 'jobs/schedule_interview.html', {'application': application})


@login_required
def task_list(request):
    """Liste simple des tâches de l'utilisateur connecté."""
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            # Créer une nouvelle tâche
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            due_date = request.POST.get('due_date')
            priority = request.POST.get('priority', 'medium')
            
            try:
                task_data = {
                    'user': request.user,
                    'title': title,
                    'description': description,
                    'priority': priority,
                }
                
                if due_date:
                    task_data['due_date'] = datetime.fromisoformat(due_date)
                    task_data['due_date'] = timezone.make_aware(task_data['due_date']) if timezone.is_naive(task_data['due_date']) else task_data['due_date']
                
                Task.objects.create(**task_data)
                messages.success(request, "Tâche créée avec succès!")
            except Exception as e:
                messages.error(request, f"Erreur lors de la création de la tâche: {str(e)}")
        
        elif action == 'toggle':
            # Marquer comme complétée/non complétée
            task_id = request.POST.get('task_id')
            try:
                task = Task.objects.get(id=task_id, user=request.user)
                task.is_completed = not task.is_completed
                task.save()
                messages.success(request, "Statut de la tâche mis à jour!")
            except Task.DoesNotExist:
                messages.error(request, "Tâche non trouvée.")
        
        elif action == 'delete':
            # Supprimer une tâche
            task_id = request.POST.get('task_id')
            try:
                task = Task.objects.get(id=task_id, user=request.user)
                task.delete()
                messages.success(request, "Tâche supprimée avec succès!")
            except Task.DoesNotExist:
                messages.error(request, "Tâche non trouvée.")
        
        return redirect('jobs:task_list')
    
    tasks = Task.objects.filter(user=request.user).order_by('is_completed', 'due_date')
    return render(request, 'jobs/task_list.html', {'tasks': tasks})


@login_required
def reminder_list(request):
    """Liste simple des rappels de l'utilisateur connecté."""
    reminders = Reminder.objects.filter(user=request.user).order_by('remind_at')
    return render(request, 'jobs/reminder_list.html', {'reminders': reminders})


# ========== REVIEWS & RATINGS VIEWS ==========

@login_required
def review_company(request, company_id):
    """Permettre à un candidat de laisser un avis sur une entreprise"""
    messages.info(request, "La fonctionnalité d'avis d'entreprise a été désactivée.")
    return redirect('jobs:company_detail', pk=company_id)


@login_required
def review_candidate(request, candidate_id, application_id=None):
    """Permettre à un employeur de laisser un avis sur un candidat"""
    messages.info(request, "La fonctionnalité d'évaluation des candidats a été désactivée.")
    return redirect('dashboard:employer_dashboard')


def company_reviews(request, company_id):
    """Afficher tous les avis d'une entreprise"""
    messages.info(request, "La fonctionnalité d'avis d'entreprise a été désactivée.")
    return redirect('jobs:home')


def candidate_reviews(request, candidate_id):
    """Afficher tous les avis d'un candidat"""
    messages.info(request, "La fonctionnalité d'avis de candidats a été désactivée.")
    return redirect('jobs:home')
