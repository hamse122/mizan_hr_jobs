"""
Custom template filters for the jobs application.
"""

from django import template
from django.utils import timezone
from datetime import timedelta
from jobs.utils import calculate_days_until_deadline, format_phone_number

register = template.Library()


@register.filter
def days_until_deadline(job):
    """Calculate days until job deadline."""
    if not job or not hasattr(job, 'deadline'):
        return None
    return calculate_days_until_deadline(job)


@register.filter
def is_expired(job):
    """Check if job deadline has passed."""
    if not job or not hasattr(job, 'deadline'):
        return False
    return job.deadline < timezone.now().date()


@register.filter
def is_urgent(job, days=7):
    """Check if job deadline is within specified days."""
    if not job or not hasattr(job, 'deadline'):
        return False
    days_left = calculate_days_until_deadline(job)
    return days_left is not None and 0 <= days_left <= days


@register.filter
def format_phone(phone):
    """Format phone number for display."""
    return format_phone_number(phone)


@register.filter
def truncate_text(text, length=100):
    """Truncate text to specified length."""
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[:length] + "..."


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary using key."""
    if not dictionary:
        return None
    return dictionary.get(key)


@register.filter
def pluralize_count(count, singular, plural=None):
    """Return singular or plural form based on count."""
    if plural is None:
        plural = singular + 's'
    count = int(count) if count else 0
    return singular if count == 1 else plural


@register.filter
def list_skills(applicant):
    """Get comma-separated list of skills for applicant."""
    if not applicant or not hasattr(applicant, 'skills'):
        return ""
    skills = applicant.skills.all()
    return ", ".join([skill.name for skill in skills])


@register.filter
def has_linkedin(applicant):
    """Check if applicant has LinkedIn URL."""
    if not applicant or not hasattr(applicant, 'linkedin'):
        return False
    return bool(applicant.linkedin)


@register.filter
def application_status(job):
    """Get application status text for job."""
    if not job or not hasattr(job, 'deadline'):
        return "Unknown"
    
    days_left = calculate_days_until_deadline(job)
    
    if days_left is None:
        return "Unknown"
    elif days_left < 0:
        return "Expired"
    elif days_left <= 3:
        return "Urgent"
    elif days_left <= 7:
        return "Soon"
    else:
        return "Active"


@register.simple_tag
def job_statistics():
    """Get job statistics."""
    from jobs.utils import get_job_statistics
    return get_job_statistics()

