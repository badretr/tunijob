from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Employer, JobSeeker

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_employer', 'is_job_seeker', 'is_staff')
    list_filter = ('is_employer', 'is_job_seeker', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('User Type', {'fields': ('is_employer', 'is_job_seeker')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Employer)
admin.site.register(JobSeeker)
