"""
Utility functions for the jobs application.
Provides helper functions for various operations.
"""

from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Count, Q
from .models import Job, Applicant


def calculate_days_until_deadline(job):
    """
    Calculate the number of days until a job deadline.
    
    Args:
        job: Job instance
        
    Returns:
        int: Number of days until deadline, negative if past deadline
    """
    if not job or not job.deadline:
        return None
    today = timezone.now().date()
    delta = job.deadline - today
    return delta.days


def get_job_statistics():
    """
    Get comprehensive statistics about jobs and applicants.
    
    Returns:
        dict: Dictionary containing various statistics
    """
    total_jobs = Job.objects.count()
    total_applicants = Applicant.objects.count()
    active_jobs = Job.objects.filter(deadline__gte=timezone.now().date()).count()
    expired_jobs = Job.objects.filter(deadline__lt=timezone.now().date()).count()
    
    # Jobs with most applicants
    jobs_with_applicants = Job.objects.annotate(
        applicant_count=Count('applicants')
    ).order_by('-applicant_count')[:5]
    
    # Average applicants per job
    avg_applicants = 0
    if total_jobs > 0:
        total_with_applicants = Job.objects.annotate(
            applicant_count=Count('applicants')
        ).aggregate(avg=Count('applicants'))['avg']
        if total_with_applicants:
            avg_applicants = total_applicants / total_jobs
    
    return {
        'total_jobs': total_jobs,
        'total_applicants': total_applicants,
        'active_jobs': active_jobs,
        'expired_jobs': expired_jobs,
        'jobs_with_most_applicants': jobs_with_applicants,
        'average_applicants_per_job': round(avg_applicants, 2),
    }


def filter_jobs_by_search(query):
    """
    Filter jobs based on search query.
    
    Args:
        query: Search string
        
    Returns:
        QuerySet: Filtered jobs
    """
    if not query:
        return Job.objects.all()
    
    return Job.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query)
    )


def get_upcoming_deadlines(days=7):
    """
    Get jobs with deadlines in the next N days.
    
    Args:
        days: Number of days to look ahead (default: 7)
        
    Returns:
        QuerySet: Jobs with upcoming deadlines
    """
    today = timezone.now().date()
    future_date = today + timedelta(days=days)
    return Job.objects.filter(
        deadline__gte=today,
        deadline__lte=future_date
    ).order_by('deadline')


def validate_email_domain(email):
    """
    Basic email domain validation.
    
    Args:
        email: Email address string
        
    Returns:
        bool: True if valid email format
    """
    if not email or '@' not in email:
        return False
    
    parts = email.split('@')
    if len(parts) != 2:
        return False
    
    domain = parts[1]
    if '.' not in domain or len(domain.split('.')) < 2:
        return False
    
    return True


def format_phone_number(phone):
    """
    Format phone number for display.
    
    Args:
        phone: Phone number string
        
    Returns:
        str: Formatted phone number
    """
    if not phone:
        return ""
    
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # Format based on length
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    
    return phone


def get_applicant_summary(applicant):
    """
    Get a summary of an applicant's qualifications.
    
    Args:
        applicant: Applicant instance
        
    Returns:
        dict: Summary information
    """
    education_count = applicant.education_history.count()
    work_count = applicant.work_experience.count()
    skill_count = applicant.skills.count()
    
    # Get latest education
    latest_education = applicant.education_history.order_by('-year').first()
    latest_education_str = ""
    if latest_education:
        latest_education_str = f"{latest_education.degree} from {latest_education.school}"
    
    # Get most recent work experience
    recent_work = applicant.work_experience.first()
    recent_work_str = ""
    if recent_work:
        recent_work_str = f"{recent_work.role} at {recent_work.company}"
    
    # Get skill names
    skill_names = list(applicant.skills.values_list('name', flat=True))
    
    return {
        'education_count': education_count,
        'work_experience_count': work_count,
        'skill_count': skill_count,
        'latest_education': latest_education_str,
        'recent_work': recent_work_str,
        'skills': skill_names,
    }


def export_applicants_to_dict(job):
    """
    Export applicants for a job to dictionary format.
    
    Args:
        job: Job instance
        
    Returns:
        list: List of dictionaries containing applicant data
    """
    applicants = job.applicants.all()
    export_data = []
    
    for applicant in applicants:
        data = {
            'full_name': applicant.full_name,
            'email': applicant.email,
            'phone': applicant.phone,
            'linkedin': applicant.linkedin or '',
            'cover_letter': applicant.cover_letter,
            'education': [
                {
                    'school': edu.school,
                    'degree': edu.degree,
                    'year': edu.year
                }
                for edu in applicant.education_history.all()
            ],
            'work_experience': [
                {
                    'company': work.company,
                    'role': work.role,
                    'duration': work.duration,
                    'description': work.description
                }
                for work in applicant.work_experience.all()
            ],
            'skills': [
                skill.name for skill in applicant.skills.all()
            ]
        }
        export_data.append(data)
    
    return export_data


def check_duplicate_application(email, job):
    """
    Check if an applicant has already applied for the same job.
    
    Args:
        email: Applicant email
        job: Job instance
        
    Returns:
        bool: True if duplicate application exists
    """
    return Applicant.objects.filter(
        email=email,
        position_applied=job
    ).exists()


def get_jobs_by_status(status='active'):
    """
    Get jobs filtered by status.
    
    Args:
        status: 'active', 'expired', or 'all'
        
    Returns:
        QuerySet: Filtered jobs
    """
    today = timezone.now().date()
    
    if status == 'active':
        return Job.objects.filter(deadline__gte=today).order_by('deadline')
    elif status == 'expired':
        return Job.objects.filter(deadline__lt=today).order_by('-deadline')
    else:
        return Job.objects.all().order_by('-deadline')


def calculate_applicant_match_score(applicant, job):
    """
    Calculate a basic match score for an applicant and job.
    This is a simplified implementation.
    
    Args:
        applicant: Applicant instance
        job: Job instance
        
    Returns:
        float: Match score between 0 and 1
    """
    score = 0.0
    
    # Cover letter contains job title or related keywords
    if job.title.lower() in applicant.cover_letter.lower():
        score += 0.3
    
    # Has work experience
    if applicant.work_experience.exists():
        score += 0.2
    
    # Has education
    if applicant.education_history.exists():
        score += 0.2
    
    # Has skills
    if applicant.skills.exists():
        score += 0.2
    
    # Has LinkedIn
    if applicant.linkedin:
        score += 0.1
    
    return min(score, 1.0)

