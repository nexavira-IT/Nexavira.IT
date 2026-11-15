from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('team/', views.team, name='team'),
    path('services/', views.services, name='services'),
    path('pricing/', views.pricing, name='pricing'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path(
        'portfolio/<int:project_id>/',
        views.portfolio_detail,
        name='portfolio_detail',
    ),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('career/', views.career, name='career'),
    path('career/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    # path('404/', views.error_404, name='error_404'),
    path('services/web-development/', views.web_development, name='web-development'),
    path('services/mobile-app-development/', views.mobile_app_development, name='mobile-app-development'),
    path('services/software-development/', views.software_development, name='software-development'),
    path('services/cloud-services/', views.cloud_services, name='cloud-services'),
    path('services/automation-ai-integration/', views.automation_ai_integration, name='automation-ai-integration'),
    path('services/it-consulting-advisory/', views.it_consulting_advisory, name='it-consulting-advisory'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('save_contact/', views.save_contact, name='save_contact'),
]