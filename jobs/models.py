from django.db import models

class Job(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    deadline = models.DateField()

    def __str__(self):
        return self.title


class Applicant(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    linkedin = models.URLField(blank=True, null=True)
    cover_letter = models.TextField()
    position_applied = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, related_name='applicants')

    def __str__(self):
        return self.full_name


class Education(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='education_history')
    school = models.CharField(max_length=255)
    degree = models.CharField(max_length=255)
    year = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.school} - {self.degree}"


class WorkExperience(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='work_experience')
    company = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    duration = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return f"{self.company} - {self.role}"


class Skill(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
