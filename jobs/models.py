from django.db import models
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta


class Job(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    deadline = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-deadline']
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        indexes = [
            models.Index(fields=['deadline']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.title
    
    def is_expired(self):
        """Check if job deadline has passed."""
        return self.deadline < timezone.now().date()
    
    def is_active(self):
        """Check if job is still active (not expired)."""
        return not self.is_expired()
    
    def days_until_deadline(self):
        """Calculate days until deadline."""
        if not self.deadline:
            return None
        delta = self.deadline - timezone.now().date()
        return delta.days
    
    def get_applicant_count(self):
        """Get number of applicants for this job."""
        return self.applicants.count()
    
    def get_recent_applicants(self, limit=5):
        """Get most recent applicants."""
        return self.applicants.all()[:limit]
    
    def is_urgent(self, days=7):
        """Check if deadline is within specified days."""
        days_left = self.days_until_deadline()
        return days_left is not None and 0 <= days_left <= days
    
    def get_status(self):
        """Get human-readable status."""
        if self.is_expired():
            return "Expired"
        days = self.days_until_deadline()
        if days is None:
            return "Unknown"
        if days <= 3:
            return "Urgent"
        if days <= 7:
            return "Soon"
        return "Active"


class Applicant(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    linkedin = models.URLField(blank=True, null=True)
    cover_letter = models.TextField()
    position_applied = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, related_name='applicants')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Review'),
            ('reviewed', 'Reviewed'),
            ('shortlisted', 'Shortlisted'),
            ('rejected', 'Rejected'),
            ('hired', 'Hired'),
        ],
        default='pending'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Applicant'
        verbose_name_plural = 'Applicants'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
        unique_together = [['email', 'position_applied']]

    def __str__(self):
        return self.full_name
    
    def get_full_qualifications(self):
        """Get all qualifications in a structured format."""
        return {
            'education': list(self.education_history.all().values()),
            'work_experience': list(self.work_experience.all().values()),
            'skills': list(self.skills.all().values_list('name', flat=True)),
        }
    
    def has_complete_profile(self):
        """Check if applicant has complete profile."""
        has_education = self.education_history.exists()
        has_work = self.work_experience.exists()
        has_skills = self.skills.exists()
        has_linkedin = bool(self.linkedin)
        return has_education and has_work and has_skills and has_linkedin
    
    def get_profile_completeness_score(self):
        """Calculate profile completeness as percentage."""
        score = 0
        if self.full_name and self.email and self.phone:
            score += 30
        if self.cover_letter:
            score += 20
        if self.education_history.exists():
            score += 15
        if self.work_experience.exists():
            score += 15
        if self.skills.exists():
            score += 10
        if self.linkedin:
            score += 10
        return min(score, 100)
    
    def get_skills_list(self):
        """Get comma-separated list of skills."""
        return ", ".join(self.skills.values_list('name', flat=True))
    
    def get_latest_education(self):
        """Get most recent education entry."""
        return self.education_history.order_by('-year').first()
    
    def get_latest_work_experience(self):
        """Get most recent work experience."""
        return self.work_experience.first()


class Education(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='education_history')
    school = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    year = models.CharField(max_length=10)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    major = models.CharField(max_length=255, blank=True)
    honors = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-year']
        verbose_name = 'Education'
        verbose_name_plural = 'Education Records'

    def __str__(self):
        return f"{self.school} - {self.degree}"
    
    def get_display_year(self):
        """Format year for display."""
        if not self.year:
            return "N/A"
        if '-' in self.year:
            return self.year
        return self.year
    
    def is_recent(self, years=5):
        """Check if education is recent (within X years)."""
        try:
            year_end = int(self.year.split('-')[0]) if '-' in self.year else int(self.year)
            current_year = timezone.now().year
            return (current_year - year_end) <= years
        except (ValueError, AttributeError):
            return False


class WorkExperience(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='work_experience')
    company = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    duration = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    location = models.CharField(max_length=255, blank=True)
    achievements = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-start_date', '-end_date']
        verbose_name = 'Work Experience'
        verbose_name_plural = 'Work Experience Records'

    def __str__(self):
        return f"{self.company} - {self.role}"
    
    def get_duration_months(self):
        """Calculate duration in months if dates are available."""
        if not self.start_date:
            return None
        
        end = self.end_date if self.end_date else timezone.now().date()
        
        months = (end.year - self.start_date.year) * 12 + (end.month - self.start_date.month)
        return max(months, 0)
    
    def is_long_term(self, months=12):
        """Check if work experience is long-term."""
        duration_months = self.get_duration_months()
        return duration_months is not None and duration_months >= months
    
    def get_formatted_duration(self):
        """Get formatted duration string."""
        if self.duration:
            return self.duration
        
        if self.start_date:
            start_str = self.start_date.strftime('%Y-%m')
            if self.is_current or not self.end_date:
                return f"{start_str} - Present"
            end_str = self.end_date.strftime('%Y-%m')
            return f"{start_str} - {end_str}"
        
        return "N/A"


class Skill(models.Model):
    SKILL_CATEGORIES = [
        ('programming', 'Programming Languages'),
        ('framework', 'Frameworks & Libraries'),
        ('database', 'Databases'),
        ('cloud', 'Cloud & DevOps'),
        ('tools', 'Tools & Software'),
        ('soft', 'Soft Skills'),
        ('other', 'Other'),
    ]
    
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=SKILL_CATEGORIES, default='other')
    proficiency = models.IntegerField(
        choices=[(1, 'Beginner'), (2, 'Intermediate'), (3, 'Advanced'), (4, 'Expert')],
        default=2
    )
    years_experience = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'

    def __str__(self):
        return self.name
    
    def get_proficiency_display_short(self):
        """Get short proficiency display."""
        proficiency_map = {1: 'Beginner', 2: 'Intermediate', 3: 'Advanced', 4: 'Expert'}
        return proficiency_map.get(self.proficiency, 'Intermediate')
    
    def is_technical_skill(self):
        """Check if skill is a technical skill."""
        return self.category in ['programming', 'framework', 'database', 'cloud', 'tools']
