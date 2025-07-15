from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.contrib import messages
from .models import Job, Applicant, Education, WorkExperience, Skill
from .forms import ApplicantForm, EducationFormSet, WorkExperienceFormSet, SkillFormSet, JobForm
from django import forms

# Hardcoded admin credentials
ADMIN_USERNAME = "xamse"
ADMIN_PASSWORD = "123"

def home(request):
    return render(request, 'home.html')

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            request.session['admin_logged_in'] = True
            messages.success(request, "Successfully logged in!")
            return redirect('jobs:admin_dashboard')
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'jobs/admin_login.html')

def admin_logout(request):
    request.session.flush()
    messages.info(request, "Logged out successfully.")
    return redirect('jobs:admin_login')

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_logged_in'):
            return redirect('jobs:admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper

# JobForm for admin job CRUD
class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'deadline']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows':4}),
            'deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

@admin_required
def admin_dashboard(request):
    jobs = Job.objects.all().order_by('-deadline')
    total_jobs = jobs.count()
    total_applicants = Applicant.objects.count()
    upcoming_deadlines = jobs.filter(deadline__gte=timezone.now()).count()
    recent_jobs = jobs[:5]  # Get the 5 most recent jobs

    return render(request, 'jobs/admin_dashboard.html', {
        'jobs': jobs,
        'total_jobs': total_jobs,
        'total_applicants': total_applicants,
        'upcoming_deadlines': upcoming_deadlines,
        'recent_jobs': recent_jobs
    })

@admin_required
def job_list(request):
    jobs = Job.objects.all().order_by('-deadline')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(jobs, 10)  # Show 10 jobs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'jobs/job_list.html', {
        'jobs': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj
    })

@admin_required
def job_create(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Job created successfully.")
            return redirect('jobs:admin_dashboard')
    else:
        form = JobForm()
    return render(request, 'jobs/job_form.html', {'form': form, 'action': 'Create Job'})

@admin_required
def job_edit(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully.")
            return redirect('jobs:admin_dashboard')
    else:
        form = JobForm(instance=job)
    return render(request, 'jobs/job_form.html', {'form': form, 'action': 'Edit Job'})

@admin_required
def job_delete(request, pk):
    job = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        job.delete()
        messages.success(request, "Job deleted successfully.")
        return redirect('jobs:admin_dashboard')
    return render(request, 'jobs/job_confirm_delete.html', {'job': job})

@admin_required
def job_applicants(request, pk):
    job = get_object_or_404(Job, pk=pk)
    applicants = job.applicants.all()
    return render(request, 'jobs/job_applicants.html', {'job': job, 'applicants': applicants})



@admin_required
def applicant_detail(request, pk):
    applicant = get_object_or_404(Applicant, pk=pk)
    education = applicant.education_history.all()
    work_experience = applicant.work_experience.all()
    skills = applicant.skills.all()
    return render(request, 'jobs/applicant_detail.html', {
        'applicant': applicant,
        'education': education,
        'work_experience': work_experience,
        'skills': skills,
    })

def apply(request):
    if request.method == 'POST':
        applicant_form = ApplicantForm(request.POST, request.FILES)
        education_formset = EducationFormSet(request.POST, prefix='education')
        work_formset = WorkExperienceFormSet(request.POST, prefix='work')
        skill_formset = SkillFormSet(request.POST, prefix='skill')

        if all([applicant_form.is_valid(), education_formset.is_valid(), work_formset.is_valid(), skill_formset.is_valid()]):
            applicant = applicant_form.save()

            for edu_form in education_formset:
                if edu_form.cleaned_data and not edu_form.cleaned_data.get('DELETE', False):
                    Education.objects.create(applicant=applicant, **edu_form.cleaned_data)

            for work_form in work_formset:
                if work_form.cleaned_data and not work_form.cleaned_data.get('DELETE', False):
                    WorkExperience.objects.create(applicant=applicant, **work_form.cleaned_data)

            for skill_form in skill_formset:
                if skill_form.cleaned_data and skill_form.cleaned_data.get('name'):
                    Skill.objects.create(applicant=applicant, **skill_form.cleaned_data)

            messages.success(request, "Application submitted successfully!")
            return redirect('jobs:apply_success')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        applicant_form = ApplicantForm()
        education_formset = EducationFormSet(prefix='education')
        work_formset = WorkExperienceFormSet(prefix='work')
        skill_formset = SkillFormSet(prefix='skill')

    return render(request, 'jobs/apply.html', {
        'applicant_form': applicant_form,
        'education_formset': education_formset,
        'work_formset': work_formset,
        'skill_formset': skill_formset,
    })

def apply_success(request):
    return render(request, 'jobs/apply_success.html')