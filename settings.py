from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

# Ne pas utiliser ce fichier en production, mais si jamais il est
# chargé comme settings Django, on accepte tous les hôtes pour éviter
# les erreurs DisallowedHost pendant tes tests.
ALLOWED_HOSTS = ["*"]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Make sure this points to your templates directory
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
] 
