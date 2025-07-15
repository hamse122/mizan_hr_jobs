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

    path('applicant/<int:pk>/', views.applicant_detail, name='applicant_detail'),

    path('apply/', views.apply, name='apply'),
    path('apply/success/', views.apply_success, name='apply_success'),

       path('', views.home, name='home'), 
]
