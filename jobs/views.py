from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import transaction
from .models import Job, Applicant, Education, WorkExperience, Skill
from .forms import ApplicantForm, EducationFormSet, WorkExperienceFormSet, SkillFormSet, JobForm
from .utils import (
    get_job_statistics, get_upcoming_deadlines, 
    calculate_applicant_match_score, export_applicants_to_dict,
    validate_email_domain, check_duplicate_application
)
from django import forms
import json

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


@admin_required
def applicant_list(request):
    """List all applicants with filtering options."""
    applicants = Applicant.objects.all().select_related('position_applied')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        applicants = applicants.filter(status=status_filter)
    
    # Filter by job
    job_filter = request.GET.get('job', '')
    if job_filter:
        applicants = applicants.filter(position_applied_id=job_filter)
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        applicants = applicants.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(applicants, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    jobs = Job.objects.all()
    
    return render(request, 'jobs/applicant_list.html', {
        'applicants': page_obj,
        'jobs': jobs,
        'status_filter': status_filter,
        'job_filter': job_filter,
        'search_query': search_query,
        'page_obj': page_obj,
    })


@admin_required
@require_http_methods(["POST"])
def update_applicant_status(request, pk):
    """Update applicant status (AJAX endpoint)."""
    applicant = get_object_or_404(Applicant, pk=pk)
    new_status = request.POST.get('status')
    
    valid_statuses = ['pending', 'reviewed', 'shortlisted', 'rejected', 'hired']
    if new_status in valid_statuses:
        applicant.status = new_status
        applicant.save()
        return JsonResponse({'success': True, 'status': new_status})
    
    return JsonResponse({'success': False, 'error': 'Invalid status'})


@admin_required
def statistics_view(request):
    """Display detailed statistics."""
    stats = get_job_statistics()
    
    # Additional statistics
    applicants_by_status = Applicant.objects.values('status').annotate(
        count=Count('id')
    ).order_by('status')
    
    jobs_by_month = Job.objects.extra(
        select={'month': "strftime('%%Y-%%m', created_at)"}
    ).values('month').annotate(count=Count('id')).order_by('-month')[:12]
    
    top_skills = Skill.objects.values('name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    recent_applications = Applicant.objects.select_related(
        'position_applied'
    ).order_by('-created_at')[:10]
    
    return render(request, 'jobs/statistics.html', {
        'stats': stats,
        'applicants_by_status': applicants_by_status,
        'jobs_by_month': jobs_by_month,
        'top_skills': top_skills,
        'recent_applications': recent_applications,
    })


@admin_required
def export_applicants_view(request, job_id):
    """Export applicants data for a job."""
    job = get_object_or_404(Job, pk=job_id)
    data = export_applicants_to_dict(job)
    
    format_type = request.GET.get('format', 'json')
    
    if format_type == 'json':
        response = HttpResponse(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="applicants_{job_id}.json"'
        return response
    else:
        # CSV export
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="applicants_{job_id}.csv"'
        
        if data:
            writer = csv.DictWriter(response, fieldnames=data[0].keys())
            writer.writeheader()
            for row in data:
                csv_row = {}
                for key, value in row.items():
                    if isinstance(value, list):
                        csv_row[key] = ', '.join(str(v) for v in value)
                    else:
                        csv_row[key] = value
                writer.writerow(csv_row)
        
        return response


@admin_required
def applicant_match_score(request, pk):
    """Calculate and display applicant match score."""
    applicant = get_object_or_404(Applicant, pk=pk)
    
    if not applicant.position_applied:
        messages.error(request, "Applicant has no associated job.")
        return redirect('jobs:applicant_detail', pk=pk)
    
    match_score = calculate_applicant_match_score(applicant, applicant.position_applied)
    completeness_score = applicant.get_profile_completeness_score()
    
    return render(request, 'jobs/applicant_match.html', {
        'applicant': applicant,
        'job': applicant.position_applied,
        'match_score': match_score,
        'completeness_score': completeness_score,
    })


def api_job_list(request):
    """API endpoint for job listings (JSON) with pagination and filtering."""
    from .api_helpers import api_success, api_error, handle_api_exceptions, paginate_queryset, validate_api_params
    
    @handle_api_exceptions
    def _get_jobs():
        # Validate parameters
        is_valid, params, error = validate_api_params(
            request,
            optional_params={
                'page': 1,
                'page_size': 20,
                'status': 'active',  # active, expired, all
                'search': ''
            }
        )
        
        if not is_valid:
            return error
        
        # Build queryset
        jobs = Job.objects.all()
        
        # Filter by status
        if params.get('status') == 'active':
            jobs = jobs.filter(deadline__gte=timezone.now().date())
        elif params.get('status') == 'expired':
            jobs = jobs.filter(deadline__lt=timezone.now().date())
        
        # Search filter
        search_query = params.get('search', '')
        if search_query:
            jobs = jobs.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Order by deadline
        jobs = jobs.order_by('deadline')
        
        # Paginate
        try:
            page = int(params.get('page', 1))
            page_size = min(int(params.get('page_size', 20)), 100)  # Max 100 per page
        except (ValueError, TypeError):
            return api_error("Invalid pagination parameters", status_code=400)
        
        paginated_data = paginate_queryset(jobs, page, page_size)
        
        # Serialize job data
        job_list = []
        for job in paginated_data['items']:
            job_list.append({
                'id': job.id,
                'title': job.title,
                'description': job.description[:200] + '...' if len(job.description) > 200 else job.description,
                'deadline': str(job.deadline),
                'days_until_deadline': job.days_until_deadline(),
                'applicant_count': job.get_applicant_count(),
                'status': job.get_status(),
                'is_active': job.is_active(),
                'is_urgent': job.is_urgent(),
            })
        
        return api_success({
            'jobs': job_list,
            'pagination': paginated_data['pagination']
        })
    
    return _get_jobs()


def api_job_detail(request, pk):
    """API endpoint for single job detail (JSON) with enhanced error handling."""
    from .api_helpers import api_success, api_error, handle_api_exceptions
    
    @handle_api_exceptions
    def _get_job():
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return api_error("Job not found", status_code=404)
        
        # Get applicants summary
        applicants = job.applicants.all()
        applicants_by_status = {}
        for status_code, status_name in Applicant._meta.get_field('status').choices:
            count = applicants.filter(status=status_code).count()
            if count > 0:
                applicants_by_status[status_name] = count
        
        job_data = {
            'id': job.id,
            'title': job.title,
            'description': job.description,
            'deadline': str(job.deadline),
            'days_until_deadline': job.days_until_deadline(),
            'is_active': job.is_active(),
            'is_urgent': job.is_urgent(),
            'applicant_count': job.get_applicant_count(),
            'status': job.get_status(),
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'updated_at': job.updated_at.isoformat() if job.updated_at else None,
            'applicants_summary': {
                'total': applicants.count(),
                'by_status': applicants_by_status
            }
        }
        
        return api_success(job_data)
    
    return _get_job()


def api_applicant_list(request):
    """API endpoint for listing applicants with filtering and pagination."""
    from .api_helpers import api_success, handle_api_exceptions, paginate_queryset, validate_api_params
    
    @handle_api_exceptions
    def _get_applicants():
        is_valid, params, error = validate_api_params(
            request,
            optional_params={
                'page': 1,
                'page_size': 20,
                'status': '',
                'job_id': ''
            }
        )
        
        if not is_valid:
            return error
        
        applicants = Applicant.objects.all().select_related('position_applied')
        
        # Filter by status
        if params.get('status'):
            applicants = applicants.filter(status=params['status'])
        
        # Filter by job
        if params.get('job_id'):
            try:
                applicants = applicants.filter(position_applied_id=int(params['job_id']))
            except ValueError:
                return api_error("Invalid job_id parameter", status_code=400)
        
        applicants = applicants.order_by('-created_at')
        
        # Paginate
        try:
            page = int(params.get('page', 1))
            page_size = min(int(params.get('page_size', 20)), 100)
        except (ValueError, TypeError):
            return api_error("Invalid pagination parameters", status_code=400)
        
        paginated_data = paginate_queryset(applicants, page, page_size)
        
        # Serialize applicant data
        applicant_list = []
        for applicant in paginated_data['items']:
            applicant_list.append({
                'id': applicant.id,
                'full_name': applicant.full_name,
                'email': applicant.email,
                'status': applicant.status,
                'position_applied': {
                    'id': applicant.position_applied.id if applicant.position_applied else None,
                    'title': applicant.position_applied.title if applicant.position_applied else None,
                } if applicant.position_applied else None,
                'profile_completeness': applicant.get_profile_completeness_score(),
                'created_at': applicant.created_at.isoformat() if applicant.created_at else None,
            })
        
        return api_success({
            'applicants': applicant_list,
            'pagination': paginated_data['pagination']
        })
    
    return _get_applicants()


def api_applicant_detail(request, pk):
    """API endpoint for single applicant detail."""
    from .api_helpers import api_success, api_error, handle_api_exceptions
    
    @handle_api_exceptions
    def _get_applicant():
        try:
            applicant = Applicant.objects.get(pk=pk)
        except Applicant.DoesNotExist:
            return api_error("Applicant not found", status_code=404)
        
        applicant_data = {
            'id': applicant.id,
            'full_name': applicant.full_name,
            'email': applicant.email,
            'phone': applicant.phone,
            'linkedin': applicant.linkedin,
            'cover_letter': applicant.cover_letter,
            'status': applicant.status,
            'position_applied': {
                'id': applicant.position_applied.id if applicant.position_applied else None,
                'title': applicant.position_applied.title if applicant.position_applied else None,
            } if applicant.position_applied else None,
            'profile_completeness': applicant.get_profile_completeness_score(),
            'education': [
                {
                    'school': edu.school,
                    'degree': edu.degree,
                    'year': edu.year,
                    'gpa': float(edu.gpa) if edu.gpa else None,
                }
                for edu in applicant.education_history.all()
            ],
            'work_experience': [
                {
                    'company': work.company,
                    'role': work.role,
                    'duration': work.duration,
                    'is_current': work.is_current,
                }
                for work in applicant.work_experience.all()
            ],
            'skills': [
                {
                    'name': skill.name,
                    'category': skill.category,
                    'proficiency': skill.proficiency,
                }
                for skill in applicant.skills.all()
            ],
            'created_at': applicant.created_at.isoformat() if applicant.created_at else None,
        }
        
        return api_success(applicant_data)
    
    return _get_applicant()