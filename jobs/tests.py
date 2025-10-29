from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Job, Applicant, Education, WorkExperience, Skill


class JobModelTest(TestCase):
    def setUp(self):
        self.job = Job.objects.create(
            title="Software Engineer",
            description="We are looking for a software engineer",
            deadline=timezone.now().date() + timedelta(days=30)
        )
    
    def test_job_creation(self):
        self.assertEqual(self.job.title, "Software Engineer")
        self.assertIn("software engineer", self.job.description.lower())
    
    def test_job_str_method(self):
        self.assertEqual(str(self.job), "Software Engineer")
    
    def test_job_deadline(self):
        future_date = timezone.now().date() + timedelta(days=30)
        self.assertEqual(self.job.deadline, future_date)


class ApplicantModelTest(TestCase):
    def setUp(self):
        self.job = Job.objects.create(
            title="Data Scientist",
            description="Data science position",
            deadline=timezone.now().date() + timedelta(days=20)
        )
        self.applicant = Applicant.objects.create(
            full_name="John Doe",
            email="john@example.com",
            phone="1234567890",
            linkedin="https://linkedin.com/in/johndoe",
            cover_letter="I am interested in this position",
            position_applied=self.job
        )
    
    def test_applicant_creation(self):
        self.assertEqual(self.applicant.full_name, "John Doe")
        self.assertEqual(self.applicant.email, "john@example.com")
        self.assertEqual(self.applicant.position_applied, self.job)
    
    def test_applicant_str_method(self):
        self.assertEqual(str(self.applicant), "John Doe")
    
    def test_applicant_without_linkedin(self):
        applicant = Applicant.objects.create(
            full_name="Jane Smith",
            email="jane@example.com",
            phone="0987654321",
            cover_letter="Application letter",
            position_applied=self.job
        )
        self.assertIsNone(applicant.linkedin)


class EducationModelTest(TestCase):
    def setUp(self):
        self.job = Job.objects.create(
            title="Developer",
            description="Developer role",
            deadline=timezone.now().date() + timedelta(days=10)
        )
        self.applicant = Applicant.objects.create(
            full_name="Bob Johnson",
            email="bob@example.com",
            phone="1112223333",
            cover_letter="Cover letter",
            position_applied=self.job
        )
        self.education = Education.objects.create(
            applicant=self.applicant,
            school="University of Technology",
            degree="Bachelor of Science",
            year="2020"
        )
    
    def test_education_creation(self):
        self.assertEqual(self.education.school, "University of Technology")
        self.assertEqual(self.education.degree, "Bachelor of Science")
        self.assertEqual(self.education.applicant, self.applicant)
    
    def test_education_str_method(self):
        expected = "University of Technology - Bachelor of Science"
        self.assertEqual(str(self.education), expected)


class WorkExperienceModelTest(TestCase):
    def setUp(self):
        self.job = Job.objects.create(
            title="Manager",
            description="Management position",
            deadline=timezone.now().date() + timedelta(days=15)
        )
        self.applicant = Applicant.objects.create(
            full_name="Alice Williams",
            email="alice@example.com",
            phone="4445556666",
            cover_letter="Application",
            position_applied=self.job
        )
        self.work_exp = WorkExperience.objects.create(
            applicant=self.applicant,
            company="Tech Corp",
            role="Senior Developer",
            duration="2021-2024",
            description="Developed web applications"
        )
    
    def test_work_experience_creation(self):
        self.assertEqual(self.work_exp.company, "Tech Corp")
        self.assertEqual(self.work_exp.role, "Senior Developer")
        self.assertIn("web applications", self.work_exp.description)
    
    def test_work_experience_str_method(self):
        expected = "Tech Corp - Senior Developer"
        self.assertEqual(str(self.work_exp), expected)


class SkillModelTest(TestCase):
    def setUp(self):
        self.job = Job.objects.create(
            title="Programmer",
            description="Programming role",
            deadline=timezone.now().date() + timedelta(days=25)
        )
        self.applicant = Applicant.objects.create(
            full_name="Charlie Brown",
            email="charlie@example.com",
            phone="7778889999",
            cover_letter="My application",
            position_applied=self.job
        )
        self.skill = Skill.objects.create(
            applicant=self.applicant,
            name="Python"
        )
    
    def test_skill_creation(self):
        self.assertEqual(self.skill.name, "Python")
        self.assertEqual(self.skill.applicant, self.applicant)
    
    def test_skill_str_method(self):
        self.assertEqual(str(self.skill), "Python")


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.job = Job.objects.create(
            title="Test Job",
            description="Test Description",
            deadline=timezone.now().date() + timedelta(days=10)
        )
    
    def test_home_view(self):
        response = self.client.get(reverse('jobs:home'))
        self.assertEqual(response.status_code, 200)
    
    def test_apply_view_get(self):
        response = self.client.get(reverse('jobs:apply'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('applicant_form', response.context)
    
    def test_job_list_requires_admin(self):
        response = self.client.get(reverse('jobs:job_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_admin_dashboard_requires_login(self):
        response = self.client.get(reverse('jobs:admin_dashboard'))
        self.assertEqual(response.status_code, 302)


class ApplicantFormSubmissionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.job = Job.objects.create(
            title="New Position",
            description="Position description",
            deadline=timezone.now().date() + timedelta(days=30)
        )
    
    def test_applicant_submission(self):
        url = reverse('jobs:apply')
        data = {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'phone': '1234567890',
            'cover_letter': 'Test cover letter',
            'position_applied': self.job.id,
            'education-TOTAL_FORMS': '1',
            'education-INITIAL_FORMS': '0',
            'education-0-school': 'Test University',
            'education-0-degree': 'BS',
            'education-0-year': '2020',
            'work-TOTAL_FORMS': '1',
            'work-INITIAL_FORMS': '0',
            'work-0-company': 'Test Company',
            'work-0-role': 'Developer',
            'work-0-duration': '2021-2023',
            'work-0-description': 'Work description',
            'skill-TOTAL_FORMS': '1',
            'skill-INITIAL_FORMS': '0',
            'skill-0-name': 'Python',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Applicant.objects.filter(email='test@example.com').exists())


class RelationshipTests(TestCase):
    def setUp(self):
        self.job = Job.objects.create(
            title="Lead Developer",
            description="Lead role",
            deadline=timezone.now().date() + timedelta(days=20)
        )
        self.applicant = Applicant.objects.create(
            full_name="Test Applicant",
            email="test@test.com",
            phone="1234567890",
            cover_letter="Letter",
            position_applied=self.job
        )
    
    def test_job_applicants_relationship(self):
        applicants = self.job.applicants.all()
        self.assertIn(self.applicant, applicants)
    
    def test_applicant_education_relationship(self):
        education = Education.objects.create(
            applicant=self.applicant,
            school="Test School",
            degree="BS",
            year="2020"
        )
        self.assertIn(education, self.applicant.education_history.all())
    
    def test_applicant_work_experience_relationship(self):
        work = WorkExperience.objects.create(
            applicant=self.applicant,
            company="Company",
            role="Role",
            duration="2020-2022",
            description="Description"
        )
        self.assertIn(work, self.applicant.work_experience.all())
    
    def test_applicant_skills_relationship(self):
        skill = Skill.objects.create(
            applicant=self.applicant,
            name="JavaScript"
        )
        self.assertIn(skill, self.applicant.skills.all())
