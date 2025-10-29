from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('jobs/', views.job_list, name='job_list'),

    path('job/create/', views.job_create, name='job_create'),
    path('job/<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('job/<int:pk>/delete/', views.job_delete, name='job_delete'),
    path('job/<int:pk>/applicants/', views.job_applicants, name='job_applicants'),
    path('job/<int:job_id>/export/', views.export_applicants_view, name='export_applicants'),

    path('applicants/', views.applicant_list, name='applicant_list'),
    path('applicant/<int:pk>/', views.applicant_detail, name='applicant_detail'),
    path('applicant/<int:pk>/status/', views.update_applicant_status, name='update_applicant_status'),
    path('applicant/<int:pk>/match/', views.applicant_match_score, name='applicant_match_score'),

    path('statistics/', views.statistics_view, name='statistics'),

    path('apply/', views.apply, name='apply'),
    path('apply/success/', views.apply_success, name='apply_success'),

    # API endpoints
    path('api/jobs/', views.api_job_list, name='api_job_list'),
    path('api/job/<int:pk>/', views.api_job_detail, name='api_job_detail'),

    path('', views.home, name='home'), 
]
