from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from .models import Job, Applicant, Education, WorkExperience, Skill
from .utils import get_job_statistics, calculate_applicant_match_score


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0
    fields = ['school', 'degree', 'year', 'gpa', 'major']
    readonly_fields = ['created_at']
    can_delete = True


class WorkExperienceInline(admin.TabularInline):
    model = WorkExperience
    extra = 0
    fields = ['company', 'role', 'duration', 'start_date', 'end_date', 'is_current']
    readonly_fields = ['created_at']
    can_delete = True


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 0
    fields = ['name', 'category', 'proficiency', 'years_experience']
    can_delete = True


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'deadline', 'status_display', 'applicant_count_link', 'created_at', 'is_expired_badge']
    list_filter = ['deadline', 'created_at', 'status']
    search_fields = ['title', 'description']
    date_hierarchy = 'deadline'
    readonly_fields = ['created_at', 'updated_at', 'applicant_statistics']
    list_per_page = 25
    
    fieldsets = (
        ('Job Information', {
            'fields': ('title', 'description', 'deadline')
        }),
        ('Statistics', {
            'fields': ('applicant_statistics',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        status = obj.get_status()
        color_map = {
            'Expired': '#dc3545',
            'Urgent': '#fd7e14',
            'Soon': '#ffc107',
            'Active': '#28a745',
        }
        color = color_map.get(status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold; padding: 3px 8px; border-radius: 3px; background-color: {}20;">{}</span>',
            color, color, status
        )
    status_display.short_description = 'Status'
    
    def is_expired_badge(self, obj):
        if obj.is_expired():
            return format_html(
                '<span style="color: #dc3545; font-size: 11px;">EXPIRED</span>'
            )
        return format_html(
            '<span style="color: #28a745; font-size: 11px;">ACTIVE</span>'
        )
    is_expired_badge.short_description = 'Status'
    
    def applicant_count_link(self, obj):
        count = obj.get_applicant_count()
        if count > 0:
            url = reverse('admin:jobs_applicant_changelist') + f'?position_applied__id__exact={obj.id}'
            return format_html('<a href="{}"><strong>{}</strong> applicant(s)</a>', url, count)
        return format_html('<span style="color: #6c757d;">No applicants</span>')
    applicant_count_link.short_description = 'Applicants'
    
    def applicant_statistics(self, obj):
        """Display detailed applicant statistics for a job."""
        applicants = obj.applicants.all()
        total = applicants.count()
        
        if total == 0:
            return "No applications received yet."
        
        status_count = {}
        for status_code, status_name in Applicant._meta.get_field('status').choices:
            count = applicants.filter(status=status_code).count()
            if count > 0:
                status_count[status_name] = count
        
        stats_html = f"<strong>Total Applications: {total}</strong><br/><br/>"
        stats_html += "<strong>By Status:</strong><ul>"
        for status, count in status_count.items():
            stats_html += f"<li>{status}: {count}</li>"
        stats_html += "</ul>"
        
        return format_html(stats_html)
    applicant_statistics.short_description = 'Applicant Statistics'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(app_count=Count('applicants'))
    
    actions = ['mark_as_featured', 'extend_deadline_30_days']
    
    def mark_as_featured(self, request, queryset):
        """Custom action placeholder - can be extended with featured flag."""
        count = queryset.count()
        self.message_user(request, f'{count} job(s) marked as featured (feature pending implementation).')
    mark_as_featured.short_description = 'Mark selected jobs as featured'


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'position_applied', 'status_display', 'profile_completeness', 'created_at', 'contact_info']
    list_filter = ['status', 'position_applied', 'created_at']
    search_fields = ['full_name', 'email', 'phone', 'position_applied__title']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at', 'profile_completeness_display', 'qualifications_summary']
    inlines = [EducationInline, WorkExperienceInline, SkillInline]
    list_per_page = 50
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'email', 'phone', 'linkedin')
        }),
        ('Application', {
            'fields': ('position_applied', 'cover_letter', 'status')
        }),
        ('Profile Metrics', {
            'fields': ('profile_completeness_display', 'qualifications_summary'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_reviewed', 'mark_as_shortlisted', 'mark_as_rejected', 'export_selected']
    
    def status_display(self, obj):
        status_colors = {
            'pending': '#6c757d',
            'reviewed': '#007bff',
            'shortlisted': '#28a745',
            'rejected': '#dc3545',
            'hired': '#155724',
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold; padding: 3px 8px; border-radius: 3px; background-color: {}20;">{}</span>',
            color, color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def contact_info(self, obj):
        """Display contact information with clickable links."""
        info = f'<strong>{obj.email}</strong><br/>'
        if obj.phone:
            info += f'📞 {obj.phone}<br/>'
        if obj.linkedin:
            info += f'<a href="{obj.linkedin}" target="_blank">LinkedIn Profile</a>'
        return format_html(info)
    contact_info.short_description = 'Contact'
    
    def profile_completeness(self, obj):
        score = obj.get_profile_completeness_score()
        if score >= 80:
            color = '#28a745'
            icon = '✓'
        elif score >= 50:
            color = '#ffc107'
            icon = '⚠'
        else:
            color = '#dc3545'
            icon = '✗'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}%</span>',
            color, icon, score
        )
    profile_completeness.short_description = 'Profile %'
    
    def profile_completeness_display(self, obj):
        score = obj.get_profile_completeness_score()
        has_education = obj.education_history.exists()
        has_work = obj.work_experience.exists()
        has_skills = obj.skills.exists()
        has_linkedin = bool(obj.linkedin)
        
        return format_html(
            '<div style="padding: 10px; background-color: #f8f9fa; border-radius: 5px;">'
            '<strong style="font-size: 16px;">Completeness: {}%</strong><br/><br/>'
            '<table style="width: 100%;">'
            '<tr><td>Education:</td><td style="color: {};">{} ({})</td></tr>'
            '<tr><td>Work Experience:</td><td style="color: {};">{} ({})</td></tr>'
            '<tr><td>Skills:</td><td style="color: {};">{} ({})</td></tr>'
            '<tr><td>LinkedIn:</td><td style="color: {};">{}</td></tr>'
            '</table></div>',
            score,
            '#28a745' if has_education else '#dc3545', '✓' if has_education else '✗',
            obj.education_history.count() if has_education else 0,
            '#28a745' if has_work else '#dc3545', '✓' if has_work else '✗',
            obj.work_experience.count() if has_work else 0,
            '#28a745' if has_skills else '#dc3545', '✓' if has_skills else '✗',
            obj.skills.count() if has_skills else 0,
            '#28a745' if has_linkedin else '#dc3545', '✓' if has_linkedin else '✗'
        )
    profile_completeness_display.short_description = 'Profile Completeness Details'
    
    def qualifications_summary(self, obj):
        """Display a summary of applicant qualifications."""
        summary = []
        
        latest_edu = obj.get_latest_education()
        if latest_edu:
            summary.append(f"<strong>Education:</strong> {latest_edu.degree} from {latest_edu.school}")
        
        latest_work = obj.get_latest_work_experience()
        if latest_work:
            summary.append(f"<strong>Recent Work:</strong> {latest_work.role} at {latest_work.company}")
        
        skills = obj.get_skills_list()
        if skills:
            summary.append(f"<strong>Skills:</strong> {skills}")
        
        if not summary:
            return "No qualifications added yet."
        
        return format_html('<br/>'.join(summary))
    qualifications_summary.short_description = 'Qualifications Summary'
    
    def mark_as_reviewed(self, request, queryset):
        queryset.update(status='reviewed')
        self.message_user(request, f'{queryset.count()} applicant(s) marked as reviewed.')
    mark_as_reviewed.short_description = 'Mark selected as reviewed'
    
    def mark_as_shortlisted(self, request, queryset):
        queryset.update(status='shortlisted')
        self.message_user(request, f'{queryset.count()} applicant(s) marked as shortlisted.')
    mark_as_shortlisted.short_description = 'Mark selected as shortlisted'
    
    def mark_as_rejected(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, f'{queryset.count()} applicant(s) marked as rejected.')
    mark_as_rejected.short_description = 'Mark selected as rejected'
    
    def export_selected(self, request, queryset):
        """Export selected applicants (placeholder for implementation)."""
        count = queryset.count()
        self.message_user(request, f'Export functionality for {count} applicant(s) - feature pending implementation.')
    export_selected.short_description = 'Export selected applicants'


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'school', 'degree', 'year', 'gpa', 'created_at']
    list_filter = ['year', 'created_at']
    search_fields = ['school', 'degree', 'applicant__full_name', 'applicant__email']
    raw_id_fields = ['applicant']
    list_per_page = 50


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ['applicant', 'company', 'role', 'duration', 'is_current', 'created_at']
    list_filter = ['is_current', 'created_at']
    search_fields = ['company', 'role', 'applicant__full_name', 'applicant__email']
    raw_id_fields = ['applicant']
    date_hierarchy = 'start_date'
    list_per_page = 50


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'applicant', 'category', 'proficiency_display', 'years_experience']
    list_filter = ['category', 'proficiency', 'created_at']
    search_fields = ['name', 'applicant__full_name', 'applicant__email']
    raw_id_fields = ['applicant']
    list_per_page = 50
    
    def proficiency_display(self, obj):
        proficiency_colors = {
            1: ('#6c757d', 'Beginner'),
            2: ('#17a2b8', 'Intermediate'),
            3: ('#ffc107', 'Advanced'),
            4: ('#28a745', 'Expert'),
        }
        color, label = proficiency_colors.get(obj.proficiency, ('#6c757d', 'Unknown'))
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, label
        )
    proficiency_display.short_description = 'Proficiency'
