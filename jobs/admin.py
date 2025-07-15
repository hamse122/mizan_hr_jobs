from django.contrib import admin
from .models import Job, Applicant, Education, WorkExperience, Skill

class EducationInline(admin.TabularInline):
    model = Education
    extra = 0

class WorkExperienceInline(admin.TabularInline):
    model = WorkExperience
    extra = 0

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 0

class ApplicantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'position_applied']
    inlines = [EducationInline, WorkExperienceInline, SkillInline]

admin.site.register(Job)
admin.site.register(Applicant, ApplicantAdmin)
