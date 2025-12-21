from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
import random

class CustomUser(AbstractUser):
    is_employer = models.BooleanField(default=False)
    is_job_seeker = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    
    def get_profile_picture_url(self):
        """Get profile picture URL or return a default/random avatar"""
        if self.profile_picture:
            return self.profile_picture.url
        
        # Use a service like UI Avatars or generate based on username
        # Using UI Avatars API for consistent avatars based on user ID
        colors = ['3B82F6', '10B981', 'F59E0B', 'EF4444', '8B5CF6', 'EC4899', '06B6D4', 'F97316']
        # Use user ID to consistently select a color (or username hash if no ID yet)
        color_index = (self.id or hash(self.username)) % len(colors)
        color = colors[abs(color_index)]
        initials = self.get_initials()
        return f"https://ui-avatars.com/api/?name={initials}&background={color}&color=fff&size=128&bold=true"
    
    def get_initials(self):
        """Get user initials for avatar"""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return self.first_name[0].upper()
        elif self.last_name:
            return self.last_name[0].upper()
        else:
            return self.username[0:2].upper() if len(self.username) >= 2 else self.username[0].upper()

class Employer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    company_description = models.TextField(blank=True)
    company_website = models.URLField(blank=True)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True)
    location = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.company_name

    def get_absolute_url(self):
        return reverse('accounts:employer_profile', args=[str(self.id)])

    @property
    def job_count(self):
        return self.jobs.filter(is_active=True).count()

class JobSeeker(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    
    def __str__(self):
        return self.user.username

# Resume-related models removed as feature is deleted
