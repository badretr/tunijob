from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django import forms
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json

from .forms import (
    EmployerSignUpForm,
    JobSeekerSignUpForm,
    UserProfileForm,
    EmployerProfileForm,
    JobSeekerProfileForm,
)
from .models import CustomUser, JobSeeker, Employer
from apps.jobs.models import Application, Message
import io
from datetime import datetime
try:
    from xhtml2pdf import pisa
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def signup_view(request):
    return render(request, 'accounts/signup_choice.html')


def employer_signup(request):
    if request.method == 'POST':
        form = EmployerSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Bienvenue, {user.username} ! Votre compte employeur a été créé avec succès.")
            return redirect('dashboard:employer_dashboard')
    else:
        form = EmployerSignUpForm()
    return render(request, 'accounts/signup_employer.html', {'form': form})


def jobseeker_signup(request):
    if request.method == 'POST':
        form = JobSeekerSignUpForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Bienvenue, {user.username} ! Votre compte candidat a été créé avec succès.")
            return redirect('dashboard:jobseeker_dashboard')
    else:
        form = JobSeekerSignUpForm()
    return render(request, 'accounts/signup_jobseeker.html', {'form': form})


@login_required
def user_profile(request):
    if request.user.is_employer:
        return redirect('accounts:employer_profile')
    elif request.user.is_job_seeker:
        # Send jobseekers to the public homepage so they can browse listings
        return redirect('jobs:home')
    return redirect('home')


@login_required
def employer_profile(request):
    if not request.user.is_employer:
        messages.error(request, "Accès refusé. Compte employeur requis.")
        return redirect('home')
    
    employer = request.user.employer
    jobs = employer.jobs.all()
    
    context = {
        'employer': employer,
        'jobs': jobs,
    }
    return render(request, 'accounts/employer_profile.html', context)


@ensure_csrf_cookie
def login_view(request):
    if request.method == 'POST':
        print("POST:", request.POST)
        print("BODY:", request.body)
        print("CONTENT_TYPE:", request.content_type)
        username_or_email = request.POST.get('username_or_email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type', 'job_seeker')

        try:
            user = CustomUser.objects.get(
                Q(username=username_or_email) | Q(email=username_or_email)
            )
            if user_type == 'job_seeker' and not user.is_job_seeker:
                messages.error(request, "Veuillez sélectionner le bon type d'utilisateur (Candidat).")
                return render(request, 'accounts/login.html')
            elif user_type == 'employer' and not user.is_employer:
                messages.error(request, "Veuillez sélectionner le bon type d'utilisateur (Employeur).")
                return render(request, 'accounts/login.html')

            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bon retour, {user.username} !")
                # Respect 'next' parameter if provided (useful for redirects from protected pages)
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                # Employers go to their dashboard by default
                if user.is_employer:
                    return redirect('dashboard:employer_dashboard')
                # Jobseekers: default to site homepage so they can browse listings after login
                return redirect('jobs:home')
            else:
                messages.error(request, "Mot de passe invalide.")
        except CustomUser.DoesNotExist:
            messages.error(request, "Aucun compte trouvé avec ces identifiants.")
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('/')


@login_required
def profile_view(request):
    if request.user.is_employer:
        return redirect('dashboard:employer_dashboard')
    elif request.user.is_job_seeker:
        # When a jobseeker tries to view 'profile' route, send them to homepage
        return redirect('jobs:home')
    return redirect('home')


@login_required
def profile_settings(request):
    """Allow any authenticated user to update their profile and password"""
    user = request.user
    detail_form = None
    detail_form_title = None

    if request.method == 'POST' and request.POST.get('form_type') == 'profile':
        user_form = UserProfileForm(request.POST, request.FILES, instance=user)
        if user.is_employer:
            detail_form = EmployerProfileForm(request.POST, request.FILES, instance=user.employer)
            detail_form_title = "Informations de l'entreprise"
        elif user.is_job_seeker:
            detail_form = JobSeekerProfileForm(request.POST, request.FILES, instance=user.jobseeker)
            detail_form_title = "Informations professionnelles"
        else:
            detail_form_title = "Informations supplémentaires"

        forms_valid = user_form.is_valid()
        if detail_form:
            forms_valid = forms_valid and detail_form.is_valid()

        if forms_valid:
            user_form.save()
            if detail_form:
                detail_form.save()
            messages.success(request, "Profil mis à jour avec succès !")
            return redirect('accounts:profile_settings')
    elif request.method == 'POST' and request.POST.get('form_type') == 'password':
        password_form = PasswordChangeForm(user, request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Mot de passe modifié avec succès !")
            return redirect('accounts:profile_settings')
        else:
            for field, errors in password_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        user_form = UserProfileForm(instance=user)
        if user.is_employer:
            detail_form = EmployerProfileForm(instance=user.employer)
            detail_form_title = "Informations de l'entreprise"
        elif user.is_job_seeker:
            detail_form = JobSeekerProfileForm(instance=user.jobseeker)
            detail_form_title = "Informations professionnelles"
        password_form = PasswordChangeForm(user)

    # Determine which detail form fields should be textareas
    detail_textarea_fields = []
    if detail_form:
        for field_name, field in detail_form.fields.items():
            if isinstance(field.widget, forms.Textarea):
                detail_textarea_fields.append(field_name)

    context = {
        'user_form': user_form,
        'detail_form': detail_form,
        'detail_form_title': detail_form_title,
        'password_form': password_form,
        'detail_textarea_fields': detail_textarea_fields,
    }
    return render(request, 'accounts/profile_settings.html', context)


@login_required
def notifications_center(request):
    """Notification center for job seekers and employers"""
    from apps.jobs.models import Notification
    
    # Get all notifications for the user
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    
    # Mark all as read when viewing
    if request.method == 'GET':
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
    
    context = {
        'notifications': notifications,
    }

    return render(request, "accounts/notifications.html", context)


@login_required
def mark_notification_read(request, notification_id):
    """Marquer une notification spécifique comme lue"""
    from apps.jobs.models import Notification
    
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            messages.success(request, "Notification marquée comme lue.")
        except Notification.DoesNotExist:
            messages.error(request, "Notification non trouvée.")
    
    return redirect('accounts:notifications')


@login_required
def mark_all_notifications_read(request):
    """Marquer toutes les notifications comme lues"""
    from apps.jobs.models import Notification
    
    if request.method == 'POST':
        count = Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        messages.success(request, f"{count} notification(s) marquée(s) comme lue(s).")
    
    return redirect('accounts:notifications')


# Resume views (feature removed) — keep stubs that redirect to dashboards
@login_required
def resume_list(request):
    messages.info(request, "La fonctionnalité de création et gestion des CV a été supprimée.")
    return redirect('dashboard:jobseeker_dashboard' if request.user.is_job_seeker else 'home')


@login_required
def resume_builder(request, resume_id=None):
    messages.info(request, "La fonctionnalité de création et gestion des CV a été supprimée.")
    return redirect('dashboard:jobseeker_dashboard' if request.user.is_job_seeker else 'home')


@login_required
def resume_view(request, resume_id):
    messages.info(request, "La fonctionnalité de création et gestion des CV a été supprimée.")
    return redirect('dashboard:jobseeker_dashboard' if request.user.is_job_seeker else 'home')


@login_required
def resume_delete(request, resume_id):
    messages.info(request, "La fonctionnalité de création et gestion des CV a été supprimée.")
    return redirect('dashboard:jobseeker_dashboard' if request.user.is_job_seeker else 'home')


@login_required
def resume_pdf(request, resume_id):
    messages.info(request, "La fonctionnalité de création et gestion des CV a été supprimée.")
    return redirect('dashboard:jobseeker_dashboard' if request.user.is_job_seeker else 'home')

