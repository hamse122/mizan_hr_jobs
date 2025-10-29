from django import forms
from django.forms import formset_factory
from django.utils import timezone
from .models import Applicant, Education, WorkExperience, Skill, Job
from .validators import (
    validate_phone_number, validate_linkedin_url, validate_cover_letter_length,
    validate_job_deadline, validate_year_format, validate_work_duration_format,
    validate_skill_name, validate_full_name
)

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        validate_job_deadline(deadline)
        return deadline
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title.strip()) < 5:
            raise forms.ValidationError("Job title must be at least 5 characters long.")
        return title
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description and len(description.strip()) < 20:
            raise forms.ValidationError("Job description must be at least 20 characters long.")
        return description

class ApplicantForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = ['full_name', 'email', 'phone', 'linkedin', 'cover_letter', 'position_applied']
        widgets = {
            'position_applied': forms.Select(attrs={'class': 'form-select'}),
            'cover_letter': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
        }
    
    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name')
        if full_name:
            validate_full_name(full_name)
        return full_name
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            validate_phone_number(phone)
        return phone
    
    def clean_linkedin(self):
        linkedin = self.cleaned_data.get('linkedin')
        if linkedin:
            validate_linkedin_url(linkedin)
        return linkedin
    
    def clean_cover_letter(self):
        cover_letter = self.cleaned_data.get('cover_letter')
        if cover_letter:
            validate_cover_letter_length(cover_letter)
        return cover_letter
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        position_applied = cleaned_data.get('position_applied')
        
        # Check for duplicate application if we have both email and job
        if email and position_applied and self.instance:
            from .validators import validate_email_duplicate
            try:
                validate_email_duplicate(email, position_applied.id, self.instance.pk if self.instance.pk else None)
            except Exception as e:
                raise forms.ValidationError(str(e))
        
        return cleaned_data

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['school', 'degree', 'year', 'gpa', 'major', 'honors']
        widgets = {
            'school': forms.TextInput(attrs={'class': 'form-control'}),
            'degree': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.TextInput(attrs={'class': 'form-control'}),
            'gpa': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '4.0'}),
            'major': forms.TextInput(attrs={'class': 'form-control'}),
            'honors': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_year(self):
        year = self.cleaned_data.get('year')
        if year:
            validate_year_format(year)
        return year
    
    def clean_gpa(self):
        gpa = self.cleaned_data.get('gpa')
        if gpa is not None:
            if gpa < 0 or gpa > 4.0:
                raise forms.ValidationError("GPA must be between 0.0 and 4.0")
        return gpa

class WorkExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkExperience
        fields = ['company', 'role', 'duration', 'description', 'start_date', 'end_date', 'is_current', 'location', 'achievements']
        widgets = {
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.TextInput(attrs={'class': 'form-control'}),
            'duration': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'achievements': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def clean_duration(self):
        duration = self.cleaned_data.get('duration')
        if duration:
            validate_work_duration_format(duration)
        return duration
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_current = cleaned_data.get('is_current')
        
        if start_date and end_date and not is_current:
            if end_date < start_date:
                raise forms.ValidationError("End date must be after start date.")
        
        return cleaned_data

class SkillForm(forms.Form):
    name = forms.CharField(
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        validators=[validate_skill_name]
    )
    category = forms.ChoiceField(
        choices=Skill.SKILL_CATEGORIES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    proficiency = forms.ChoiceField(
        choices=[(1, 'Beginner'), (2, 'Intermediate'), (3, 'Advanced'), (4, 'Expert')],
        required=False,
        initial=2,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

EducationFormSet = formset_factory(EducationForm, extra=1, can_delete=True)
WorkExperienceFormSet = formset_factory(WorkExperienceForm, extra=1, can_delete=True)
SkillFormSet = formset_factory(SkillForm, extra=1, can_delete=True)
