from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Employer, JobSeeker

INPUT_CLASSES = 'w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all'
TEXTAREA_CLASSES = INPUT_CLASSES

class EmployerSignUpForm(UserCreationForm):
    company_name = forms.CharField(max_length=255)
    company_description = forms.CharField(widget=forms.Textarea, required=False)
    company_website = forms.URLField(required=False)
    company_logo = forms.ImageField(required=False)
    profile_picture = forms.ImageField(required=False, label='Photo de profil')

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_employer = True
        if commit:
            user.save()
            if self.cleaned_data.get('profile_picture'):
                user.profile_picture = self.cleaned_data.get('profile_picture')
                user.save()
            Employer.objects.create(
                user=user,
                company_name=self.cleaned_data.get('company_name'),
                company_description=self.cleaned_data.get('company_description'),
                company_website=self.cleaned_data.get('company_website'),
                company_logo=self.cleaned_data.get('company_logo')
            )
        return user

class JobSeekerSignUpForm(UserCreationForm):
    profile_picture = forms.ImageField(required=False, label='Photo de profil')
    resume = forms.FileField(required=False, label='CV / Lettre de motivation', help_text='Formats: PDF, DOC, DOCX. Taille max 10MB')

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_job_seeker = True
        if commit:
            user.save()
            # Save optional profile picture
            if self.cleaned_data.get('profile_picture'):
                user.profile_picture = self.cleaned_data.get('profile_picture')
                user.save()
            # Create JobSeeker and attach resume if provided
            jobseeker = JobSeeker.objects.create(user=user)
            resume_file = self.cleaned_data.get('resume')
            if resume_file:
                jobseeker.resume = resume_file
                jobseeker.save()
        return user

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(label='Adresse email', widget=forms.EmailInput())

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'profile_picture']
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'profile_picture': 'Photo de profil',
        }
        help_texts = {
            'profile_picture': 'Formats acceptés : PNG, JPG, GIF. Taille max 5 Mo.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'profile_picture':
                field.widget.attrs.update({
                    'class': INPUT_CLASSES,
                    'accept': 'image/*',
                })
            else:
                field.widget.attrs.update({
                    'class': INPUT_CLASSES,
                    'placeholder': field.label,
                })

class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = Employer
        fields = [
            'company_name',
            'company_description',
            'company_website',
            'company_logo',
            'location',
            'phone',
            'industry',
        ]
        labels = {
            'company_name': 'Nom de l’entreprise',
            'company_description': 'Description',
            'company_website': 'Site web',
            'company_logo': 'Logo',
            'location': 'Localisation',
            'phone': 'Téléphone',
            'industry': 'Secteur',
        }
        help_texts = {
            'company_logo': 'Formats acceptés : PNG, JPG, GIF.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'company_description':
                field.widget = forms.Textarea(attrs={'rows': 4})
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({
                    'class': INPUT_CLASSES,
                })
            else:
                field.widget.attrs.update({
                    'class': INPUT_CLASSES,
                    'placeholder': field.label,
                })

class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeeker
        fields = ['resume']
        labels = {
            'resume': 'CV (PDF / DOC / DOCX)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in ['skills', 'experience', 'education']:
                field.widget = forms.Textarea(attrs={'rows': 4})
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({
                    'class': INPUT_CLASSES,
                    'accept': '.pdf,.doc,.docx',
                })
            else:
                field.widget.attrs.update({
                    'class': TEXTAREA_CLASSES if isinstance(field.widget, forms.Textarea) else INPUT_CLASSES,
                    'placeholder': field.label,
                })

# Resume builder forms removed — feature deleted