from django.urls import path

from . import admin_views


app_name = 'staff_panel'

urlpatterns = [
    path('login/', admin_views.StaffPanelLoginView.as_view(), name='login'),
    path('logout/', admin_views.StaffPanelLogoutView.as_view(), name='logout'),
    path('', admin_views.dashboard, name='dashboard'),
    path('jobs/', admin_views.job_list, name='job_list'),
    path('jobs/new/', admin_views.job_create, name='job_create'),
    path('jobs/<int:job_id>/edit/', admin_views.job_edit, name='job_edit'),
    path('jobs/<int:job_id>/delete/', admin_views.job_delete, name='job_delete'),
    path('portfolio/', admin_views.portfolio_projects, name='portfolio_projects'),
    path('portfolio/new/', admin_views.portfolio_create, name='portfolio_create'),
    path(
        'portfolio/<int:project_id>/edit/',
        admin_views.portfolio_edit,
        name='portfolio_edit',
    ),
    path(
        'portfolio/<int:project_id>/delete/',
        admin_views.portfolio_delete,
        name='portfolio_delete',
    ),
    path('applications/', admin_views.application_list, name='application_list'),
    path(
        'applications/<int:application_id>/',
        admin_views.application_detail,
        name='application_detail',
    ),
    path(
        'applications/<int:application_id>/resume/',
        admin_views.application_resume,
        name='application_resume',
    ),
    path('contacts/', admin_views.contact_list, name='contact_list'),
    path('contacts/<int:contact_id>/', admin_views.contact_detail, name='contact_detail'),
]
