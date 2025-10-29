"""
Custom validators for the jobs application.
"""

from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Applicant, Job
import re


def validate_phone_number(value):
    """
    Validate phone number format.
    Accepts formats: (123) 456-7890, 123-456-7890, 1234567890, +1-123-456-7890
    """
    if not value:
        return
    
    # Remove common separators
    cleaned = re.sub(r'[^\d+]', '', value)
    
    # Check if it starts with + and country code
    if cleaned.startswith('+'):
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValidationError('Invalid phone number format.')
    else:
        # Should be 10-11 digits
        if len(cleaned) < 10 or len(cleaned) > 11:
            raise ValidationError(
                'Phone number must contain 10-11 digits. '
                'Accepted formats: (123) 456-7890, 123-456-7890, 1234567890'
            )


def validate_linkedin_url(value):
    """
    Validate LinkedIn URL format.
    """
    if not value:
        return
    
    linkedin_pattern = r'^https?://(www\.)?linkedin\.com/.*'
    if not re.match(linkedin_pattern, value, re.IGNORECASE):
        raise ValidationError(
            'Invalid LinkedIn URL. Must start with https://linkedin.com/ or http://linkedin.com/'
        )


def validate_email_duplicate(email, job_id, applicant_id=None):
    """
    Validate that an applicant hasn't already applied for the same job.
    
    Args:
        email: Applicant email
        job_id: Job ID
        applicant_id: Optional applicant ID (for updates)
    
    Raises:
        ValidationError: If duplicate application exists
    """
    if not email or not job_id:
        return
    
    queryset = Applicant.objects.filter(email=email, position_applied_id=job_id)
    
    # Exclude current applicant if updating
    if applicant_id:
        queryset = queryset.exclude(pk=applicant_id)
    
    if queryset.exists():
        raise ValidationError(
            'You have already submitted an application for this position.'
        )


def validate_cover_letter_length(value):
    """
    Validate cover letter has minimum required length.
    """
    if not value:
        raise ValidationError('Cover letter is required.')
    
    min_length = 50
    if len(value.strip()) < min_length:
        raise ValidationError(
            f'Cover letter must be at least {min_length} characters long.'
        )


def validate_job_deadline(value):
    """
    Validate that job deadline is in the future.
    """
    if not value:
        return
    
    today = timezone.now().date()
    if value < today:
        raise ValidationError('Job deadline must be in the future.')


def validate_year_format(value):
    """
    Validate education year format (YYYY or YYYY-YYYY).
    """
    if not value:
        return
    
    # Allow single year (YYYY) or range (YYYY-YYYY)
    year_pattern = r'^\d{4}(-\d{4})?$'
    if not re.match(year_pattern, value):
        raise ValidationError(
            'Year must be in format YYYY (e.g., 2020) or YYYY-YYYY (e.g., 2020-2024).'
        )


def validate_work_duration_format(value):
    """
    Validate work experience duration format.
    """
    if not value:
        return
    
    # Allow formats: YYYY-YYYY, YYYY-MM - YYYY-MM, "Present", "Current"
    duration_pattern = r'^(\d{4}(-\d{2})?)\s*-\s*(\d{4}(-\d{2})?|Present|Current)$'
    special_values = ['Present', 'Current', 'present', 'current']
    
    if value in special_values:
        return
    
    if not re.match(duration_pattern, value, re.IGNORECASE):
        raise ValidationError(
            'Duration must be in format: YYYY-YYYY, YYYY-MM-YYYY-MM, "Present", or "Current"'
        )


def validate_skill_name(value):
    """
    Validate skill name (alphanumeric and common special characters).
    """
    if not value:
        return
    
    # Allow alphanumeric, spaces, and common tech symbols
    skill_pattern = r'^[a-zA-Z0-9\s\+\#\.\/\-]+$'
    if not re.match(skill_pattern, value):
        raise ValidationError(
            'Skill name contains invalid characters. Use only letters, numbers, spaces, '
            'and common symbols (+, #, ., /, -).'
        )
    
    if len(value.strip()) < 2:
        raise ValidationError('Skill name must be at least 2 characters long.')


def validate_full_name(value):
    """
    Validate full name format.
    """
    if not value:
        raise ValidationError('Full name is required.')
    
    # Should have at least first and last name
    parts = value.strip().split()
    if len(parts) < 2:
        raise ValidationError('Please provide your full name (first and last name).')
    
    # Each part should be at least 2 characters
    for part in parts:
        if len(part) < 2:
            raise ValidationError('Name parts must be at least 2 characters long.')
    
    # Should not contain numbers or special characters (except hyphens and apostrophes)
    name_pattern = r'^[a-zA-Z\s\-\']+$'
    if not re.match(name_pattern, value):
        raise ValidationError(
            'Name can only contain letters, spaces, hyphens, and apostrophes.'
        )

