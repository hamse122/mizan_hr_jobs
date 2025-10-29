"""
Management command to export applicants data.
Usage: python manage.py export_applicants [--job-id N] [--format json|csv]
"""

import json
import csv
from django.core.management.base import BaseCommand
from django.http import HttpResponse
from jobs.models import Job, Applicant
from jobs.utils import export_applicants_to_dict


class Command(BaseCommand):
    help = 'Export applicants data to JSON or CSV format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--job-id',
            type=int,
            help='Export applicants for specific job ID',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv'],
            default='json',
            help='Output format (json or csv)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (optional)',
        )

    def handle(self, *args, **options):
        job_id = options.get('job_id')
        output_format = options['format']
        output_file = options.get('output')
        
        if job_id:
            try:
                job = Job.objects.get(pk=job_id)
                data = export_applicants_to_dict(job)
                job_title = job.title
            except Job.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Job with ID {job_id} not found.'))
                return
        else:
            # Export all applicants
            applicants = Applicant.objects.all()
            data = []
            for applicant in applicants:
                applicant_data = {
                    'full_name': applicant.full_name,
                    'email': applicant.email,
                    'phone': applicant.phone,
                    'linkedin': applicant.linkedin or '',
                    'position_applied': applicant.position_applied.title if applicant.position_applied else '',
                    'skills': [skill.name for skill in applicant.skills.all()],
                }
                data.append(applicant_data)
            job_title = 'All Jobs'
        
        if output_format == 'json':
            output = json.dumps(data, indent=2)
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(output)
                self.stdout.write(self.style.SUCCESS(f'Data exported to {output_file}'))
            else:
                self.stdout.write(output)
        else:  # CSV
            if not data:
                self.stdout.write(self.style.WARNING('No data to export.'))
                return
            
            fieldnames = data[0].keys()
            
            if output_file:
                with open(output_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in data:
                        # Convert lists to strings for CSV
                        csv_row = {}
                        for key, value in row.items():
                            if isinstance(value, list):
                                csv_row[key] = ', '.join(value)
                            else:
                                csv_row[key] = value
                        writer.writerow(csv_row)
                self.stdout.write(self.style.SUCCESS(f'Data exported to {output_file}'))
            else:
                # Print to stdout
                import sys
                writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
                writer.writeheader()
                for row in data:
                    csv_row = {}
                    for key, value in row.items():
                        if isinstance(value, list):
                            csv_row[key] = ', '.join(value)
                        else:
                            csv_row[key] = value
                    writer.writerow(csv_row)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Exported {len(data)} applicant(s) for "{job_title}"'
            )
        )

