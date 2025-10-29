"""
Management command to clean up expired jobs.
Usage: python manage.py cleanup_expired_jobs [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from jobs.models import Job, Applicant
from jobs.utils import get_jobs_by_status


class Command(BaseCommand):
    help = 'Clean up or report on expired jobs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show expired jobs without deleting them',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete expired jobs (default is to just report)',
        )

    def handle(self, *args, **options):
        expired_jobs = get_jobs_by_status('expired')
        
        if not expired_jobs.exists():
            self.stdout.write(self.style.SUCCESS('No expired jobs found.'))
            return
        
        self.stdout.write(f'Found {expired_jobs.count()} expired job(s):\n')
        
        for job in expired_jobs:
            applicant_count = job.applicants.count()
            self.stdout.write(
                f'  - {job.title} (Deadline: {job.deadline}, '
                f'Applicants: {applicant_count})'
            )
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\nDry run mode - no changes made.'))
        elif options['delete']:
            count = expired_jobs.count()
            expired_jobs.delete()
            self.stdout.write(
                self.style.SUCCESS(f'\nDeleted {count} expired job(s).')
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '\nUse --delete to actually delete expired jobs, '
                    'or --dry-run to see what would be deleted.'
                )
            )

