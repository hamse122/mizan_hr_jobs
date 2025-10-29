from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count
from .models import Job, Applicant, Education, WorkExperience, Skill
from .utils import get_job_statistics, calculate_applicant_match_score


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0
    fields = ['school', 'degree', 'year', 'gpa', 'major']
    readonly_fields = ['created_at']


class WorkExperienceInline(admin.TabularInline):
    model = WorkExperience
    extra = 0
    fields = ['company', 'role', 'duration', 'start_date', 'end_date', 'is_current']
    readonly_fields = ['created_at']


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 0
    fields = ['name', 'category', 'proficiency', 'years_experience']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'deadline', 'status_display', 'applicant_count_link', 'created_at']
    list_filter = ['deadline', 'created_at']
    search_fields = ['title', 'description']
    date_hierarchy = 'deadline'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Job Information', {
            'fields': ('title', 'description', 'deadline')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        status = obj.get_status()
        color_map = {
            'Expired': 'red',
            'Urgent': 'orange',
            'Soon': 'yellow',
            'Active': 'green',
        }
        color = color_map.get(status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    status_display.short_description = 'Status'
    
    def applicant_count_link(self, obj):
        count = obj.get_applicant_count()
        if count > 0:
            url = reverse('admin:jobs_applicant_changelist') + f'?position_applied__id__exact={obj.id}'
            return format_html('<a href="{}">{} applicants</a>', url, count)
        return '0 applicants'
    applicant_count_link.short_description = 'Applicants'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(app_count=Count('applicants'))


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'position_applied', 'status_display', 'profile_completeness', 'created_at']
    list_filter = ['status', 'position_applied', 'created_at']
    search_fields = ['full_name', 'email', 'phone']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'profile_completeness_display']
    inlines = [EducationInline, WorkExperienceInline, SkillInline]
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'email', 'phone', 'linkedin')
        }),
        ('Application', {
            'fields': ('position_applied', 'cover_letter', 'status')
        }),
        ('Profile Metrics', {
            'fields': ('profile_completeness_display',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_reviewed', 'mark_as_shortlisted', 'mark_as_rejected']
    
    def status_display(self, obj):
        status_colors = {
            'pending': 'gray',
            'reviewed': 'blue',
            'shortlisted': 'green',
            'rejected': 'red',
            'hired': 'darkgreen',
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def profile_completeness(self, obj):
        score = obj.get_profile_completeness_score()
        if score >= 80:
            color = 'green'
        elif score >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{}%</span>',
            color, score
        )
    profile_completeness.short_description = 'Profile %'
    
    def profile_completeness_display(self, obj):
        score = obj.get_profile_completeness_score()
        has_education = obj.education_history.exists()
        has_work = obj.work_experience.exists()
        has_skills = obj.skills.exists()
        has_linkedin = bool(obj.linkedin)
        
        return format_html(
            '<strong>Completeness: {}%</strong><br/>'
            'Education: {}<br/>'
            'Work Experience: {}<br/>'
            'Skills: {}<br/>'
            'LinkedIn: {}',
            score,
            '✓' if has_education else '✗',
            '✓' if has_work else '✗',
            '✓' if has_skills else '✗',
            '✓' if has_linkedin else '✗'
        )
    profile_completeness_display.short_description = 'Profile Completeness'
    
    def mark_as_reviewed(self, request, queryset):
        queryset.update(status='reviewed')
        self.message_user(request, f'{queryset.count()} applicants marked as reviewed.')
    mark_as_reviewed.short_description = 'Mark selected as reviewed'
    
    def mark_as_shortlisted(self, request, queryset):
        queryset.update(status='shortlisted')
        self.message_user(request, f'{queryset.count()} applicants marked as shortlisted.')
    mark_as_shortlisted.short_description = 'Mark selected as shortlisted'
    
    def mark_as_rejected(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f'{queryset.count()} applicants marked as rejected.')
    mark_as_rejected.short_description = 'Mark selected as rejected'


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'school', 'degree', 'year', 'gpa', 'created_at']
    list_filter = ['year', 'created_at']
    search_fields = ['school', 'degree', 'applicant__full_name']
    raw_id_fields = ['applicant']


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'company', 'role', 'duration', 'is_current', 'created_at']
    list_filter = ['is_current', 'created_at']
    search_fields = ['company', 'role', 'applicant__full_name']
    raw_id_fields = ['applicant']
    date_hierarchy = 'start_date'


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'applicant', 'category', 'proficiency_display', 'years_experience']
    list_filter = ['category', 'proficiency', 'created_at']
    search_fields = ['name', 'applicant__full_name']
    raw_id_fields = ['applicant']
    
    def proficiency_display(self, obj):
        return obj.get_proficiency_display_short()
    proficiency_display.short_description = 'Proficiency'
