"""
Django signals for the jobs application.
"""

from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Job, Applicant


@receiver(post_save, sender=Job)
def job_created_or_updated(sender, instance, created, **kwargs):
    """
    Signal handler when a job is created or updated.
    In production, this could send notifications, update search indexes, etc.
    """
    if created:
        # Job was created
        print(f"New job created: {instance.title}")
        # In production, you might want to:
        # - Send notifications to subscribers
        # - Update search indexes
        # - Log the event
    else:
        # Job was updated
        print(f"Job updated: {instance.title}")
        # In production, you might want to:
        # - Notify applicants if deadline changed
        # - Update cache


@receiver(post_save, sender=Applicant)
def applicant_created(sender, instance, created, **kwargs):
    """
    Signal handler when a new applicant submits an application.
    In production, this could send confirmation emails, notifications, etc.
    """
    if created:
        print(f"New application received from: {instance.full_name} for {instance.position_applied}")
        
        # In production, you might want to:
        # - Send confirmation email to applicant
        # - Send notification to HR/admin
        # - Create automated scoring/ranking
        # - Integrate with HR systems
        
        # Example email (would work if email is configured):
        # try:
        #     send_mail(
        #         subject='Application Received',
        #         message=f'Thank you for applying to {instance.position_applied.title}',
        #         from_email=settings.DEFAULT_FROM_EMAIL,
        #         recipient_list=[instance.email],
        #         fail_silently=True,
        #     )
        # except Exception as e:
        #     print(f"Error sending email: {e}")


@receiver(pre_delete, sender=Job)
def job_before_delete(sender, instance, **kwargs):
    """
    Signal handler before a job is deleted.
    Can be used to archive data or prevent deletion if there are applicants.
    """
    applicant_count = instance.applicants.count()
    if applicant_count > 0:
        print(f"Warning: Deleting job '{instance.title}' which has {applicant_count} applicant(s)")
        # In production, you might want to:
        # - Archive the job instead of deleting
        # - Send notifications to applicants
        # - Prevent deletion if there are active applicants


@receiver(post_delete, sender=Applicant)
def applicant_deleted(sender, instance, **kwargs):
    """
    Signal handler after an applicant is deleted.
    Can be used for cleanup or logging.
    """
    print(f"Applicant deleted: {instance.full_name}")
    # Related Education, WorkExperience, and Skill objects
    # are automatically deleted due to CASCADE relationship


@receiver(post_save, sender=Applicant)
def check_duplicate_application(sender, instance, created, **kwargs):
    """
    Check for duplicate applications when a new applicant is created.
    """
    if created and instance.position_applied:
        # Check if this email already applied to this job
        duplicates = Applicant.objects.filter(
            email=instance.email,
            position_applied=instance.position_applied
        ).exclude(pk=instance.pk)
        
        if duplicates.exists():
            print(f"Warning: Potential duplicate application detected for {instance.email}")
            # In production, you might want to flag this for review


def setup_signals():
    """
    Optional function to explicitly set up signals.
    Can be called from apps.py ready() method.
    """
    # Signals are automatically connected when this module is imported
    # and the @receiver decorators are processed
    pass

