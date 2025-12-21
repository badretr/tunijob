from django import forms
from django.contrib import admin
from .models import Job, Category, Application, Message, Activity, Interview, Task, Reminder, MessageTemplate, Notification

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'employer', 'category', 'location', 'job_type', 'posted_date', 'is_active')
    list_filter = ('is_active', 'job_type', 'category')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'posted_date'

class CategoryForm(forms.ModelForm):
    ICON_CHOICES = [
        ('fas fa-code', '💻 Code (Web Development)'),
        ('fas fa-mobile-alt', '📱 Mobile'),
        ('fas fa-palette', '🎨 Design'),
        ('fas fa-database', '🗄️ Database'),
        ('fas fa-bullhorn', '📢 Marketing'),
        ('fas fa-chart-line', '📈 Sales'),
        ('fas fa-headset', '🎧 Customer Service'),
        ('fas fa-money-bill-wave', '💰 Finance'),
        ('fas fa-hospital', '🏥 Healthcare'),
        ('fas fa-graduation-cap', '🎓 Education'),
        ('fas fa-cogs', '⚙️ Engineering'),
        ('fas fa-users', '👥 Human Resources'),
        ('fas fa-tasks', '📋 Project Management'),
        ('fas fa-pen', '✍️ Writing'),
        ('fas fa-balance-scale', '⚖️ Legal'),
        ('fas fa-briefcase', '💼 Administration'),
    ]
    
    icon = forms.ChoiceField(
        choices=ICON_CHOICES,
        widget=forms.Select(attrs={'class': 'select2'}),
        help_text='Select an icon for this category'
    )

    class Meta:
        model = Category
        fields = '__all__'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    list_display = ('name', 'icon_preview', 'job_count')
    search_fields = ('name',)

    def icon_preview(self, obj):
        return f'<i class="{obj.icon}"></i> {obj.icon}'
    icon_preview.short_description = 'Icon'
    icon_preview.allow_tags = True

    def job_count(self, obj):
        return obj.job_set.count()
    job_count.short_description = 'Number of Jobs'

    class Media:
        css = {
            'all': (
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
                'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css',
            )
        }
        js = (
            'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js',
        )

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'job_seeker', 'applied_date', 'status')
    list_filter = ('status', 'applied_date')
    search_fields = ('job__title', 'job_seeker__user__username')
    date_hierarchy = 'applied_date'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin for chat messages"""
    list_display = ('application', 'sender', 'receiver', 'short_content', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = (
        'application__job__title',
        'sender__username',
        'receiver__username',
        'content',
    )
    date_hierarchy = 'created_at'

    def short_content(self, obj):
        return (obj.content[:75] + '...') if len(obj.content) > 75 else obj.content

    short_content.short_description = 'Contenu'


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'title', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'title', 'description')
    date_hierarchy = 'created_at'


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'scheduled_at', 'interview_type', 'status')
    list_filter = ('interview_type', 'status', 'scheduled_at')
    search_fields = (
        'application__job__title',
        'application__job_seeker__user__username',
    )
    date_hierarchy = 'scheduled_at'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'priority', 'is_completed', 'due_date', 'created_at')
    list_filter = ('priority', 'is_completed', 'due_date', 'created_at')
    search_fields = ('title', 'user__username', 'description')
    date_hierarchy = 'created_at'


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'reminder_type', 'remind_at', 'is_sent')
    list_filter = ('reminder_type', 'is_sent', 'remind_at')
    search_fields = ('title', 'user__username', 'description')
    date_hierarchy = 'remind_at'


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('name', 'user__username', 'content')
    date_hierarchy = 'created_at'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    date_hierarchy = 'created_at'