from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import ProtectedError, Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from .forms import (
    JobApplicationStatusForm,
    JobOpportunityForm,
    PortfolioProjectForm,
    StaffAuthenticationForm,
)
from .models import JobApplication, JobOpportunity, PortfolioProject, contact


def _staff_required(view_func):
    return user_passes_test(
        lambda user: user.is_active and user.is_staff,
        login_url='staff_panel:login',
    )(view_func)


def _has_permission(user, action, model_name):
    return user.has_perm(f'nexaviraapp.{action}_{model_name}')


def _require_permission(request, action, model_name):
    if not _has_permission(request.user, action, model_name):
        raise PermissionDenied


def _can_view(user, model_name):
    return (
        _has_permission(user, 'view', model_name)
        or _has_permission(user, 'change', model_name)
    )


def _panel_context(request, **context):
    user = request.user
    context['panel_permissions'] = {
        'jobs': _can_view(user, 'jobopportunity'),
        'add_jobs': _has_permission(user, 'add', 'jobopportunity'),
        'portfolio': _can_view(user, 'portfolioproject'),
        'add_portfolio': _has_permission(user, 'add', 'portfolioproject'),
        'applications': _can_view(user, 'jobapplication'),
        'contacts': _can_view(user, 'contact'),
    }
    return context


class StaffPanelLoginView(LoginView):
    authentication_form = StaffAuthenticationForm
    template_name = 'admin_panel/login.html'
    next_page = reverse_lazy('staff_panel:dashboard')


class StaffPanelLogoutView(LogoutView):
    next_page = reverse_lazy('staff_panel:login')


@_staff_required
def dashboard(request):
    user = request.user
    can_view_jobs = _can_view(user, 'jobopportunity')
    can_view_portfolio = _can_view(user, 'portfolioproject')
    can_view_applications = _can_view(user, 'jobapplication')
    can_view_contacts = _can_view(user, 'contact')

    context = {
        'active_job_count': (
            JobOpportunity.objects.filter(is_active=True).count()
            if can_view_jobs else None
        ),
        'portfolio_project_count': (
            PortfolioProject.objects.filter(is_active=True).count()
            if can_view_portfolio else None
        ),
        'application_count': (
            JobApplication.objects.count()
            if can_view_applications else None
        ),
        'new_application_count': (
            JobApplication.objects.filter(status=JobApplication.Status.NEW).count()
            if can_view_applications else None
        ),
        'contact_count': contact.objects.count() if can_view_contacts else None,
        'recent_applications': (
            JobApplication.objects.select_related('job')[:5]
            if can_view_applications else ()
        ),
    }
    return render(
        request,
        'admin_panel/dashboard.html',
        _panel_context(request, **context),
    )


@_staff_required
def job_list(request):
    if not _can_view(request.user, 'jobopportunity'):
        raise PermissionDenied

    jobs = JobOpportunity.objects.all()
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'all')
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(location__icontains=query)
            | Q(description__icontains=query)
        )
    if status_filter == 'active':
        jobs = jobs.filter(is_active=True)
    elif status_filter == 'inactive':
        jobs = jobs.filter(is_active=False)
    elif status_filter != 'all':
        status_filter = 'all'

    page_obj = Paginator(jobs, 12).get_page(request.GET.get('page'))
    return render(
        request,
        'admin_panel/job_list.html',
        _panel_context(
            request,
            jobs=page_obj,
            page_obj=page_obj,
            query=query,
            status_filter=status_filter,
        ),
    )


@_staff_required
@require_http_methods(['GET', 'POST'])
def job_create(request):
    _require_permission(request, 'add', 'jobopportunity')
    form = JobOpportunityForm(
        request.POST if request.method == 'POST' else None,
    )
    if request.method == 'POST' and form.is_valid():
        job = form.save()
        messages.success(request, f'{job.title} was added to job opportunities.')
        destination = (
            'staff_panel:job_list'
            if _can_view(request.user, 'jobopportunity')
            else 'staff_panel:dashboard'
        )
        return redirect(destination)
    return render(
        request,
        'admin_panel/job_form.html',
        _panel_context(request, form=form, page_heading='Add a job', job=None),
    )


@_staff_required
@require_http_methods(['GET', 'POST'])
def job_edit(request, job_id):
    _require_permission(request, 'change', 'jobopportunity')
    job = get_object_or_404(JobOpportunity, pk=job_id)
    form = JobOpportunityForm(
        request.POST if request.method == 'POST' else None,
        instance=job,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{job.title} was updated.')
        return redirect('staff_panel:job_list')
    return render(
        request,
        'admin_panel/job_form.html',
        _panel_context(request, form=form, page_heading='Edit job', job=job),
    )


@_staff_required
@require_http_methods(['GET', 'POST'])
def job_delete(request, job_id):
    _require_permission(request, 'delete', 'jobopportunity')
    job = get_object_or_404(JobOpportunity, pk=job_id)
    if request.method == 'POST':
        title = job.title
        try:
            job.delete()
        except ProtectedError:
            messages.error(
                request,
                'This job has applications and cannot be deleted. You can hide it from the Careers page instead.',
            )
        else:
            messages.success(request, f'{title} was deleted.')
        return redirect('staff_panel:job_list')
    return render(
        request,
        'admin_panel/job_confirm_delete.html',
        _panel_context(request, job=job),
    )


@_staff_required
def portfolio_projects(request):
    if not _can_view(request.user, 'portfolioproject'):
        raise PermissionDenied

    projects = PortfolioProject.objects.all()
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'all')
    if query:
        projects = projects.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(technologies__icontains=query)
        )
    if status_filter == 'active':
        projects = projects.filter(is_active=True)
    elif status_filter == 'inactive':
        projects = projects.filter(is_active=False)
    elif status_filter != 'all':
        status_filter = 'all'

    page_obj = Paginator(projects, 12).get_page(request.GET.get('page'))
    return render(
        request,
        'admin_panel/portfolio_list.html',
        _panel_context(
            request,
            projects=page_obj,
            page_obj=page_obj,
            query=query,
            status_filter=status_filter,
        ),
    )


@_staff_required
@require_http_methods(['GET', 'POST'])
def portfolio_create(request):
    _require_permission(request, 'add', 'portfolioproject')
    form = PortfolioProjectForm(
        request.POST if request.method == 'POST' else None,
        request.FILES if request.method == 'POST' else None,
    )
    if request.method == 'POST' and form.is_valid():
        project = form.save()
        messages.success(request, f'{project.title} was added to the portfolio.')
        destination = (
            'staff_panel:portfolio_projects'
            if _can_view(request.user, 'portfolioproject')
            else 'staff_panel:dashboard'
        )
        return redirect(destination)
    return render(
        request,
        'admin_panel/portfolio_form.html',
        _panel_context(
            request,
            form=form,
            page_heading='Add a portfolio project',
            project=None,
        ),
    )


@_staff_required
@require_http_methods(['GET', 'POST'])
def portfolio_edit(request, project_id):
    _require_permission(request, 'change', 'portfolioproject')
    project = get_object_or_404(PortfolioProject, pk=project_id)
    form = PortfolioProjectForm(
        request.POST if request.method == 'POST' else None,
        request.FILES if request.method == 'POST' else None,
        instance=project,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{project.title} was updated.')
        return redirect('staff_panel:portfolio_projects')
    return render(
        request,
        'admin_panel/portfolio_form.html',
        _panel_context(
            request,
            form=form,
            page_heading='Edit portfolio project',
            project=project,
        ),
    )


@_staff_required
@require_http_methods(['GET', 'POST'])
def portfolio_delete(request, project_id):
    _require_permission(request, 'delete', 'portfolioproject')
    project = get_object_or_404(PortfolioProject, pk=project_id)
    if request.method == 'POST':
        title = project.title
        project.delete()
        messages.success(request, f'{title} was deleted.')
        return redirect('staff_panel:portfolio_projects')
    return render(
        request,
        'admin_panel/portfolio_confirm_delete.html',
        _panel_context(request, project=project),
    )


@_staff_required
def application_list(request):
    if not _can_view(request.user, 'jobapplication'):
        raise PermissionDenied

    applications = JobApplication.objects.select_related('job')
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    if query:
        applications = applications.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(job__title__icontains=query)
        )
    valid_statuses = {value for value, _label in JobApplication.Status.choices}
    if status_filter in valid_statuses:
        applications = applications.filter(status=status_filter)
    else:
        status_filter = ''

    page_obj = Paginator(applications, 15).get_page(request.GET.get('page'))
    return render(
        request,
        'admin_panel/application_list.html',
        _panel_context(
            request,
            applications=page_obj,
            page_obj=page_obj,
            query=query,
            status_filter=status_filter,
            status_choices=JobApplication.Status.choices,
        ),
    )


@_staff_required
@require_http_methods(['GET', 'POST'])
def application_detail(request, application_id):
    if not _can_view(request.user, 'jobapplication'):
        raise PermissionDenied
    application = get_object_or_404(
        JobApplication.objects.select_related('job'),
        pk=application_id,
    )

    can_change = _has_permission(request.user, 'change', 'jobapplication')
    form = JobApplicationStatusForm(
        request.POST if request.method == 'POST' else None,
        instance=application,
    ) if can_change else None
    if request.method == 'POST':
        if not can_change:
            raise PermissionDenied
        if form.is_valid():
            form.save()
            messages.success(request, 'Application status was updated.')
            return redirect(
                'staff_panel:application_detail',
                application_id=application.pk,
            )

    return render(
        request,
        'admin_panel/application_detail.html',
        _panel_context(
            request,
            application=application,
            form=form,
            can_change_application=can_change,
        ),
    )


@_staff_required
def application_resume(request, application_id):
    if not _can_view(request.user, 'jobapplication'):
        raise PermissionDenied
    application = get_object_or_404(JobApplication, pk=application_id)
    if not application.resume:
        messages.error(request, 'This application has no resume attached.')
        return redirect(
            'staff_panel:application_detail',
            application_id=application.pk,
        )
    return FileResponse(
        application.resume.open('rb'),
        as_attachment=True,
        filename=application.resume.name.rsplit('/', 1)[-1],
    )


@_staff_required
def contact_list(request):
    if not _can_view(request.user, 'contact'):
        raise PermissionDenied

    inquiries = contact.objects.all()
    query = request.GET.get('q', '').strip()
    if query:
        inquiries = inquiries.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(company__icontains=query)
            | Q(service__icontains=query)
        )
    page_obj = Paginator(inquiries, 15).get_page(request.GET.get('page'))
    return render(
        request,
        'admin_panel/contact_list.html',
        _panel_context(
            request,
            inquiries=page_obj,
            page_obj=page_obj,
            query=query,
        ),
    )


@_staff_required
def contact_detail(request, contact_id):
    if not _can_view(request.user, 'contact'):
        raise PermissionDenied
    inquiry = get_object_or_404(contact, pk=contact_id)
    return render(
        request,
        'admin_panel/contact_detail.html',
        _panel_context(request, inquiry=inquiry),
    )
