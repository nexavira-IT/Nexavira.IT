from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from . import models
from django.core.mail import send_mail
from django.conf import settings
from .forms import JobApplicationForm
from .models import JobOpportunity, PortfolioProject
from .pricing_data import PRICING_SERVICES
# Create your views here.

def home(request):
    # Show latest 6 active projects on homepage
    projects = PortfolioProject.objects.filter(
        is_active=True
    ).order_by('-id')[:6]

    # Get all unique categories from active projects
    available_categories = (
        PortfolioProject.objects.filter(
            is_active=True
        ).order_by().values_list(
            'category', flat=True
        ).distinct()
    )

    return render(
        request,
        'index.html',
        {
            'projects': projects,
            'available_categories': available_categories,
        },
    )


def about(request):
    return render(request, 'about.html')

def team(request):
    return render(request, 'team.html')

def services(request):
    return render(request, 'services.html')

def pricing(request):
    return render(request, 'pricing.html', {'pricing_services': PRICING_SERVICES})

def mobile_app_development(request):
    return render(request, 'mobile-app-development.html')

def web_development(request):
    return render(request, 'web-development.html')

def software_development(request):
    return render(request, 'software-development.html')

def cloud_services(request):
    return render(request, 'cloud-services.html')

def automation_ai_integration(request):
    return render(request, 'automation-ai-integration.html')

def it_consulting_advisory(request):
    return render(request, 'it-consulting-advisory.html')

def portfolio(request):
    projects = PortfolioProject.objects.filter(is_active=True)
    available_categories = set(
        projects.order_by().values_list('category', flat=True).distinct()
    )
    categories = [
        (value, label)
        for value, label in PortfolioProject.Category.choices
        if value in available_categories
    ]
    return render(
        request,
        'portfolio.html',
        {'projects': projects, 'categories': categories},
    )


def portfolio_detail(request, project_id):
    project = get_object_or_404(
        PortfolioProject,
        pk=project_id,
        is_active=True,
    )
    return render(
        request,
        'portfolio_detail.html',
        {'project': project},
    )


def contact(request):
    return render(request, 'contact.html')

def faq(request):
    return render(request, 'faq.html')

def career(request):
    jobs = JobOpportunity.objects.filter(is_active=True)
    return render(request, 'career.html', {'jobs': jobs})


def apply_job(request, job_id):
    job = get_object_or_404(JobOpportunity, pk=job_id, is_active=True)
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.save()
            messages.success(request, 'Your application has been submitted.')
            return redirect('career')
    else:
        form = JobApplicationForm()

    return render(
        request,
        'job_application.html',
        {'job': job, 'form': form},
    )

def privacy(request):
    return render(request, 'privacy.html')

def terms(request):
    return render(request, 'terms.html')

def page_not_found(request, exception):
    return render(request, '404.html', status=404)


def save_contact(request):

    if request.method == 'POST':

        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        company = request.POST.get('company')
        service = request.POST.get('service')
        message = request.POST.get('message')

        # Save data to database
        models.contact.objects.create(
            name=name,
            email=email,
            phone=phone,
            company=company,
            service=service,
            message=message
        )

        #Send email notification
        subject = f'New Contact Inquiry from {name}'

        email_message = f"""

        Name: {name}
        Email: {email}
        Phone: {phone}
        Company: {company}
        Service: {service}

        Message:
        {message}
        """

        send_mail(
            subject,
            email_message,
            settings.DEFAULT_FROM_EMAIL,
            ['nexavirabd@gmail.com'],
            fail_silently=False,
        )

        return redirect('contact')

    return render(request, 'contact.html')