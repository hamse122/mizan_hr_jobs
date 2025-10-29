"""
Management command to generate test data for the jobs application.
Usage: python manage.py generate_test_data [--jobs N] [--applicants M]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from jobs.models import Job, Applicant, Education, WorkExperience, Skill


class Command(BaseCommand):
    help = 'Generate test data for jobs and applicants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--jobs',
            type=int,
            default=10,
            help='Number of jobs to create',
        )
        parser.add_argument(
            '--applicants',
            type=int,
            default=5,
            help='Number of applicants per job',
        )

    def handle(self, *args, **options):
        num_jobs = options['jobs']
        num_applicants_per_job = options['applicants']
        
        self.stdout.write(self.style.SUCCESS(f'Generating {num_jobs} jobs...'))
        
        job_titles = [
            'Software Engineer', 'Data Scientist', 'Product Manager',
            'DevOps Engineer', 'Frontend Developer', 'Backend Developer',
            'Full Stack Developer', 'UI/UX Designer', 'QA Engineer',
            'System Administrator', 'Database Administrator', 'Security Analyst'
        ]
        
        job_descriptions = [
            'We are looking for an experienced professional to join our team.',
            'This role requires strong technical skills and teamwork abilities.',
            'Join a dynamic team working on cutting-edge technology.',
            'Great opportunity for growth and professional development.',
            'Work on challenging projects with industry-leading technologies.'
        ]
        
        schools = [
            'MIT', 'Stanford University', 'Harvard University',
            'Carnegie Mellon', 'UC Berkeley', 'University of Washington',
            'Georgia Tech', 'University of Michigan'
        ]
        
        degrees = [
            'Bachelor of Science in Computer Science',
            'Master of Science in Software Engineering',
            'Bachelor of Engineering',
            'Master of Computer Science'
        ]
        
        companies = [
            'Google', 'Microsoft', 'Amazon', 'Apple', 'Facebook',
            'Netflix', 'Uber', 'Airbnb', 'Twitter', 'LinkedIn'
        ]
        
        roles = [
            'Software Engineer', 'Senior Developer', 'Tech Lead',
            'Principal Engineer', 'Engineering Manager'
        ]
        
        skills_list = [
            'Python', 'JavaScript', 'Java', 'C++', 'React', 'Django',
            'Node.js', 'AWS', 'Docker', 'Kubernetes', 'SQL', 'MongoDB'
        ]
        
        # Create jobs
        created_jobs = []
        for i in range(num_jobs):
            title = random.choice(job_titles)
            if i > len(job_titles) - 1:
                title = f"{title} {i+1}"
            
            deadline = timezone.now().date() + timedelta(days=random.randint(1, 60))
            job = Job.objects.create(
                title=title,
                description=random.choice(job_descriptions),
                deadline=deadline
            )
            created_jobs.append(job)
            self.stdout.write(f'Created job: {job.title}')
        
        # Create applicants for each job
        first_names = ['John', 'Jane', 'Bob', 'Alice', 'Charlie', 'Diana', 'Eve', 'Frank']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
        email_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'company.com']
        
        total_applicants = 0
        for job in created_jobs:
            for j in range(num_applicants_per_job):
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                full_name = f"{first_name} {last_name}"
                email = f"{first_name.lower()}.{last_name.lower()}{j}@{random.choice(email_domains)}"
                
                applicant = Applicant.objects.create(
                    full_name=full_name,
                    email=email,
                    phone=f"{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
                    linkedin=f"https://linkedin.com/in/{first_name.lower()}-{last_name.lower()}",
                    cover_letter=f"Dear Hiring Manager, I am excited to apply for the {job.title} position...",
                    position_applied=job
                )
                
                # Add education
                num_education = random.randint(1, 2)
                for k in range(num_education):
                    Education.objects.create(
                        applicant=applicant,
                        school=random.choice(schools),
                        degree=random.choice(degrees),
                        year=str(random.randint(2015, 2024))
                    )
                
                # Add work experience
                num_work = random.randint(1, 3)
                for k in range(num_work):
                    WorkExperience.objects.create(
                        applicant=applicant,
                        company=random.choice(companies),
                        role=random.choice(roles),
                        duration=f"{random.randint(2020, 2023)}-{random.randint(2023, 2024)}",
                        description=f"Worked on various projects and technologies..."
                    )
                
                # Add skills
                num_skills = random.randint(3, 6)
                selected_skills = random.sample(skills_list, num_skills)
                for skill_name in selected_skills:
                    Skill.objects.create(
                        applicant=applicant,
                        name=skill_name
                    )
                
                total_applicants += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated {num_jobs} jobs and {total_applicants} applicants!'
            )
        )

