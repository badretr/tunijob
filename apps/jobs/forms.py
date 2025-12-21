from django import forms
from .models import Job, Application, CompanyReview, CandidateReview

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title', 'category', 'description', 'requirements',
            'location', 'salary', 'job_type', 'deadline'
        ]
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'requirements': forms.Textarea(attrs={'rows': 4}),
        }

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(
                attrs={
                    'rows': 6, 
                    'placeholder': 'Écrivez votre lettre de motivation ici... (optionnel)',
                    'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none'
                }
            )
        }
        labels = {
            'cover_letter': 'Lettre de motivation'
        }
        help_texts = {
            'cover_letter': 'Cette lettre est optionnelle mais recommandée.'
        }

class JobSearchForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'placeholder': 'Job title or keyword'}
    ))
    location = forms.CharField(required=False, widget=forms.TextInput(
        attrs={'placeholder': 'Location'}
    ))
    category = forms.ChoiceField(required=False)
    job_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + Job.JOB_TYPE_CHOICES
    )

class JobPostForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'category', 'description', 'requirements', 'location', 'salary', 'job_type', 'experience_level']
        labels = {
            'title': 'Titre du poste',
            'category': 'Catégorie',
            'description': 'Description',
            'requirements': 'Exigences',
            'location': 'Localisation',
            'salary': 'Salaire',
            'job_type': 'Type de poste',
            'experience_level': 'Niveau d\'expérience',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'requirements': forms.Textarea(attrs={'rows': 4}),
        }


# CompanyReviewForm removed — rating feature disabled in UI


# CandidateReviewForm removed — rating feature disabled in UI