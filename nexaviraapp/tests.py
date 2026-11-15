from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import JobApplication, JobOpportunity, PortfolioProject, contact


class ContactSubmissionTests(TestCase):
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    )
    def test_post_saves_contact_and_sends_notification(self):
        response = self.client.post(
            reverse('save_contact'),
            {
                'name': 'Test Person',
                'email': 'person@example.com',
                'phone': '123456789',
                'company': 'Example Co',
                'service': 'Web Development',
                'message': 'I would like to discuss a new project.',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('contact'))
        self.assertEqual(contact.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['nexavirabd@gmail.com'])
        self.assertIn('Test Person', mail.outbox[0].body)


class NotFoundPageTests(TestCase):
    @override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'])
    def test_unknown_url_renders_custom_404_page(self):
        response = self.client.get('/this-page-does-not-exist/')

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')

    @override_settings(DEBUG=True, ALLOWED_HOSTS=['testserver'])
    def test_unknown_url_renders_custom_404_page_during_development(self):
        response = self.client.get('/this-page-does-not-exist/')

        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, 'We can’t find that', status_code=404)


class PublicRouteSmokeTests(TestCase):
    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_public_pages_render_successfully(self):
        for route_name in (
            'home',
            'about',
            'team',
            'services',
            'pricing',
            'portfolio',
            'contact',
            'faq',
            'career',
            'web-development',
            'mobile-app-development',
            'software-development',
            'cloud-services',
            'automation-ai-integration',
            'it-consulting-advisory',
            'privacy',
            'terms',
        ):
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)


class ServicePageTests(TestCase):
    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_discuss_requirements_link_opens_contact_page(self):
        response = self.client.get(reverse('software-development'))

        self.assertContains(
            response,
            'href="/contact/">Discuss your requirements',
        )


class PricingPageTests(TestCase):
    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_pricing_page_includes_all_service_tiers_and_reference_prices(self):
        response = self.client.get(reverse('pricing'))

        self.assertEqual(response.status_code, 200)
        for service in (
            'Web Development',
            'Mobile App Development',
            'Software Development',
            'Cloud Services',
            'Intelligent Automation &amp; AI Integration',
            'IT Consulting &amp; Advisory',
        ):
            self.assertContains(response, service)

        for price in (
            '$150 - $800',
            '$1,000 - $3,500',
            '$2,000 - $6,000',
            '$2,500 - $7,000',
            '$5,000 - $12,000',
            '$15,000+',
            '$1,500 - $4,000',
            '$5,000 - $15,000',
            '$20,000+',
            '$400 - $1,000',
            '$1,500 - $4,500',
            '$5,000+',
            '$300 - $1,500',
            '$4,000 - $10,000+',
            '$100 - $250',
            '$2,000 - $5,000',
        ):
            self.assertContains(response, price)

        for feature in (
            'Elementor page builder',
            'REST API integration',
            'Swift (iOS) + Kotlin (Android)',
            'Subscription billing logic',
            'Zero-downtime deployment',
            'Vector DB &amp; embeddings',
            'Flexible retainer commitment',
        ):
            self.assertContains(response, feature)

        self.assertEqual(
            response.content.decode().count(
                'class="button pricing-card__button" href="/contact/"'
            ),
            18,
        )

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_pricing_is_linked_from_the_shared_site_header(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'href="/pricing/">Pricing')


class CareerPageTests(TestCase):
    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_career_page_shows_current_status_and_resume_email(self):
        response = self.client.get(reverse('career'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No current openings')
        self.assertContains(response, 'class="career-empty-icon"')
        self.assertContains(response, '<circle')

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_career_page_lists_active_jobs_only(self):
        long_description = (
            'Role overview. '
            + 'Collaborate with teams. ' * 35
            + 'COMPLETE_DESCRIPTION_SHOULD_BE_HIDDEN'
        )
        active_job = JobOpportunity.objects.create(
            title='Django Developer',
            description=long_description,
            location='Dhaka / Remote',
            workplace_type=JobOpportunity.WorkplaceType.REMOTE,
        )
        JobOpportunity.objects.create(
            title='Closed Position',
            description='This role is no longer accepting applications.',
            location='Dhaka',
            is_active=False,
        )

        response = self.client.get(reverse('career'))

        self.assertContains(response, 'Django Developer')
        self.assertContains(response, 'Remote')
        self.assertContains(response, reverse('apply_job', args=[active_job.pk]))
        self.assertNotContains(response, 'Closed Position')
        self.assertNotContains(response, 'COMPLETE_DESCRIPTION_SHOULD_BE_HIDDEN')

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_apply_page_keeps_full_job_description_available(self):
        job = JobOpportunity.objects.create(
            title='Django Developer',
            description='Full responsibility details for the role.',
            location='Dhaka / Remote',
        )

        response = self.client.get(reverse('apply_job', args=[job.pk]))

        self.assertContains(response, 'View full job description')
        self.assertContains(response, 'Full responsibility details for the role.')

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_apply_page_sanitizes_rich_job_description(self):
        job = JobOpportunity.objects.create(
            title='Django Developer',
            description=(
                '<h2>Responsibilities</h2><p>Write <strong>safe</strong> code.</p>'
                '<script>alert(1)</script><a href="javascript:alert(2)">bad link</a>'
            ),
            location='Dhaka',
        )

        response = self.client.get(reverse('apply_job', args=[job.pk]))

        self.assertContains(response, '<h2>Responsibilities</h2>')
        self.assertContains(response, '<strong>safe</strong>')
        self.assertNotContains(response, '<script>')
        self.assertNotContains(response, 'javascript:')

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_staff_job_form_uses_ckeditor_and_work_arrangement_field(self):
        user = get_user_model().objects.create_superuser(
            username='job-admin',
            email='job-admin@example.com',
            password='test-password',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('staff_panel:job_create'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'django_ckeditor_5')
        self.assertContains(response, 'Work arrangement')


class JobApplicationTests(TestCase):
    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_valid_application_saves_resume_and_job(self):
        job = JobOpportunity.objects.create(
            title='Django Developer',
            description='Build and maintain web applications.',
            location='Dhaka / Remote',
        )
        resume = SimpleUploadedFile(
            'resume.pdf',
            b'%PDF-1.4\nResume test data',
            content_type='application/pdf',
        )

        with TemporaryDirectory() as upload_dir:
            with override_settings(MEDIA_ROOT=upload_dir):
                response = self.client.post(
                    reverse('apply_job', args=[job.pk]),
                    {
                        'name': 'Test Applicant',
                        'email': 'applicant@example.com',
                        'phone': '0123456789',
                        'resume': resume,
                        'cover_letter': 'I am interested in this role.',
                    },
                )

        self.assertRedirects(
            response,
            reverse('career'),
            fetch_redirect_response=False,
        )
        application = JobApplication.objects.get()
        self.assertEqual(application.job, job)
        self.assertEqual(application.name, 'Test Applicant')
        self.assertTrue(application.resume.name.endswith('resume.pdf'))
        response = self.client.get(reverse('career'))
        self.assertContains(response, 'Your application has been submitted.')

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_invalid_resume_is_not_accepted(self):
        job = JobOpportunity.objects.create(
            title='Django Developer',
            description='Build and maintain web applications.',
            location='Dhaka / Remote',
        )
        resume = SimpleUploadedFile(
            'resume.txt',
            b'Not a supported resume file',
            content_type='text/plain',
        )

        response = self.client.post(
            reverse('apply_job', args=[job.pk]),
            {
                'name': 'Test Applicant',
                'email': 'applicant@example.com',
                'phone': '0123456789',
                'resume': resume,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(JobApplication.objects.count(), 0)
        self.assertContains(response, 'Upload a valid PDF, DOC, or DOCX resume.')


class StaffPanelTests(TestCase):
    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_dashboard_requires_staff_login(self):
        response = self.client.get(reverse('staff_panel:dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('staff_panel:login'), response.url)

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_non_staff_account_cannot_log_in_to_panel(self):
        user = get_user_model().objects.create_user(
            username='regular-user',
            email='user@example.com',
            password='test-password',
        )

        response = self.client.post(
            reverse('staff_panel:login'),
            {'username': user.username, 'password': 'test-password'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'does not have access')
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_dashboard_shows_permission_aware_website_summary(self):
        user = get_user_model().objects.create_superuser(
            username='dashboard-admin',
            email='dashboard-admin@example.com',
            password='test-password',
        )
        self.client.force_login(user)
        job = JobOpportunity.objects.create(
            title='Django Developer',
            description='Build and maintain web applications.',
            location='Dhaka',
        )
        with TemporaryDirectory() as upload_dir:
            with override_settings(MEDIA_ROOT=upload_dir):
                JobApplication.objects.create(
                    job=job,
                    name='Test Applicant',
                    email='applicant@example.com',
                    phone='0123456789',
                    resume=SimpleUploadedFile(
                        'resume.pdf',
                        b'%PDF-1.4\nResume test data',
                        content_type='application/pdf',
                    ),
                )
        contact.objects.create(
            name='Test Customer',
            email='customer@example.com',
            phone='0123456789',
            company='Example Co',
            service='Web Development',
            message='Please contact me about a project.',
        )

        response = self.client.get(reverse('staff_panel:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'NEXAVIRA / ADMINISTRATION')
        self.assertContains(response, 'Active opportunities')
        self.assertContains(response, 'Contact inquiries')
        self.assertContains(response, 'Test Applicant')
        self.assertContains(response, '<strong>1</strong>')
        self.assertContains(
            response,
            reverse('staff_panel:job_create'),
        )

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_dashboard_hides_metrics_without_model_permissions(self):
        user = get_user_model().objects.create_user(
            username='limited-admin',
            email='limited-admin@example.com',
            password='test-password',
            is_staff=True,
        )
        self.client.force_login(user)
        contact.objects.create(
            name='Private Inquiry',
            email='customer@example.com',
            phone='0123456789',
            company='Example Co',
            service='Web Development',
            message='A private customer message.',
        )

        response = self.client.get(reverse('staff_panel:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome back, limited-admin')
        self.assertNotContains(response, 'Contact inquiries')
        self.assertNotContains(response, 'Private Inquiry')
        self.assertEqual(
            self.client.get(
                reverse('staff_panel:contact_detail', args=[contact.objects.get().pk]),
            ).status_code,
            403,
        )

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_staff_can_create_update_and_delete_database_backed_jobs(self):
        user = get_user_model().objects.create_superuser(
            username='job-creator',
            email='job-creator@example.com',
            password='test-password',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('staff_panel:job_create'),
            {
                'title': 'Product Designer',
                'description': '<p>Design thoughtful products.</p>',
                'location': 'Dhaka / Remote',
                'employment_type': JobOpportunity.EmploymentType.FULL_TIME,
                'workplace_type': JobOpportunity.WorkplaceType.REMOTE,
                'is_active': 'on',
            },
        )

        self.assertRedirects(
            response,
            reverse('staff_panel:job_list'),
            fetch_redirect_response=False,
        )
        job = JobOpportunity.objects.get(title='Product Designer')
        self.assertTrue(job.is_active)
        self.assertEqual(job.workplace_type, JobOpportunity.WorkplaceType.REMOTE)
        career_response = self.client.get(reverse('career'))
        self.assertContains(career_response, 'Product Designer')

        response = self.client.post(
            reverse('staff_panel:job_edit', args=[job.pk]),
            {
                'title': 'Product Designer II',
                'description': '<p>Design thoughtful products.</p>',
                'location': 'Dhaka',
                'employment_type': JobOpportunity.EmploymentType.FULL_TIME,
                'workplace_type': JobOpportunity.WorkplaceType.HYBRID,
            },
        )

        self.assertRedirects(
            response,
            reverse('staff_panel:job_list'),
            fetch_redirect_response=False,
        )
        job.refresh_from_db()
        self.assertEqual(job.title, 'Product Designer II')
        self.assertFalse(job.is_active)
        self.assertEqual(job.workplace_type, JobOpportunity.WorkplaceType.HYBRID)
        self.assertEqual(
            self.client.post(
                reverse('staff_panel:job_delete', args=[job.pk]),
            ).status_code,
            302,
        )
        self.assertFalse(JobOpportunity.objects.filter(pk=job.pk).exists())

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_staff_can_update_application_status_and_job_with_applicant_is_protected(self):
        user = get_user_model().objects.create_superuser(
            username='application-admin',
            email='application-admin@example.com',
            password='test-password',
        )
        self.client.force_login(user)
        with TemporaryDirectory() as upload_dir:
            with override_settings(MEDIA_ROOT=upload_dir):
                job = JobOpportunity.objects.create(
                    title='Django Developer',
                    description='Build and maintain web applications.',
                    location='Dhaka',
                )
                application = JobApplication.objects.create(
                    job=job,
                    name='Test Applicant',
                    email='applicant@example.com',
                    phone='0123456789',
                    resume=SimpleUploadedFile(
                        'resume.pdf',
                        b'%PDF-1.4\nResume test data',
                        content_type='application/pdf',
                    ),
                )

                response = self.client.post(
                    reverse(
                        'staff_panel:application_detail',
                        args=[application.pk],
                    ),
                    {'status': JobApplication.Status.REVIEWING},
                )
                self.assertRedirects(
                    response,
                    reverse(
                        'staff_panel:application_detail',
                        args=[application.pk],
                    ),
                    fetch_redirect_response=False,
                )
                application.refresh_from_db()
                self.assertEqual(application.status, JobApplication.Status.REVIEWING)

                response = self.client.post(
                    reverse('staff_panel:job_delete', args=[job.pk]),
                    follow=True,
                )

        self.assertContains(response, 'cannot be deleted')
        self.assertTrue(JobOpportunity.objects.filter(pk=job.pk).exists())

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_staff_can_read_contact_inquiry_from_database(self):
        user = get_user_model().objects.create_superuser(
            username='contact-admin',
            email='contact-admin@example.com',
            password='test-password',
        )
        inquiry = contact.objects.create(
            name='Test Customer',
            email='customer@example.com',
            phone='0123456789',
            company='Example Co',
            service='Web Development',
            message='Please contact me about my project.',
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse('staff_panel:contact_detail', args=[inquiry.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please contact me about my project.')

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_resume_download_is_restricted_to_authorized_staff(self):
        job = JobOpportunity.objects.create(
            title='Django Developer',
            description='Build and maintain web applications.',
            location='Dhaka / Remote',
        )

        with TemporaryDirectory() as upload_dir:
            with override_settings(MEDIA_ROOT=upload_dir):
                application = JobApplication.objects.create(
                    job=job,
                    name='Test Applicant',
                    email='applicant@example.com',
                    phone='0123456789',
                    resume=SimpleUploadedFile(
                        'resume.pdf',
                        b'%PDF-1.4\nResume test data',
                        content_type='application/pdf',
                    ),
                )
                download_url = reverse(
                    'staff_panel:application_resume',
                    args=[application.pk],
                )
                self.assertEqual(self.client.get(download_url).status_code, 302)

                user = get_user_model().objects.create_superuser(
                    username='career-admin',
                    email='admin@example.com',
                    password='test-password',
                )
                self.client.force_login(user)
                response = self.client.get(download_url)

                self.assertEqual(response.status_code, 200)
                self.assertTrue(response['Content-Disposition'].startswith('attachment;'))
                self.assertEqual(
                    b''.join(response.streaming_content),
                    b'%PDF-1.4\nResume test data',
                )

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_pdf_extension_does_not_allow_invalid_file_content(self):
        job = JobOpportunity.objects.create(
            title='Django Developer',
            description='Build and maintain web applications.',
            location='Dhaka / Remote',
        )

        response = self.client.post(
            reverse('apply_job', args=[job.pk]),
            {
                'name': 'Test Applicant',
                'email': 'applicant@example.com',
                'phone': '0123456789',
                'resume': SimpleUploadedFile(
                    'resume.pdf',
                    b'This is not a PDF',
                    content_type='application/pdf',
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(JobApplication.objects.count(), 0)
        self.assertContains(response, 'Upload a valid PDF, DOC, or DOCX resume.')


class PortfolioManagementTests(TestCase):
    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_staff_can_create_edit_and_delete_projects_shown_on_portfolio(self):
        user = get_user_model().objects.create_superuser(
            username='portfolio-admin',
            email='portfolio-admin@example.com',
            password='test-password',
        )
        self.client.force_login(user)

        form_response = self.client.get(reverse('staff_panel:portfolio_create'))
        self.assertEqual(form_response.status_code, 200)
        self.assertContains(form_response, 'enctype="multipart/form-data"')
        self.assertContains(form_response, 'name="image"')
        self.assertContains(form_response, 'django_ckeditor_5')

        response = self.client.post(
            reverse('staff_panel:portfolio_create'),
            {
                'title': 'Nexavira Storefront',
                'category': PortfolioProject.Category.ECOMMERCE,
                'description': (
                    '<p>An online store built for a <strong>growing retailer</strong>.</p>'
                    '<script>alert(1)</script>'
                ),
                'technologies': 'Django, PostgreSQL, UI/UX',
                'project_url': 'https://example.com/project',
                'display_order': 1,
                'is_active': 'on',
            },
        )
        self.assertRedirects(
            response,
            reverse('staff_panel:portfolio_projects'),
            fetch_redirect_response=False,
        )
        project = PortfolioProject.objects.get(title='Nexavira Storefront')

        public_response = self.client.get(reverse('portfolio'))
        self.assertContains(public_response, 'Nexavira Storefront')
        self.assertNotContains(public_response, '<script>')
        self.assertNotContains(public_response, 'growing retailer')
        self.assertContains(public_response, 'data-filter="ecommerce"')
        self.assertContains(public_response, 'data-category="ecommerce"')
        self.assertContains(
            public_response,
            f'href="{reverse("portfolio_detail", args=[project.pk])}"',
        )

        detail_response = self.client.get(
            reverse('portfolio_detail', args=[project.pk]),
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'About this work')
        self.assertContains(detail_response, 'Project snapshot')
        self.assertContains(detail_response, 'Django')
        self.assertContains(
            detail_response,
            '<p>An online store built for a <strong>growing retailer</strong>.</p>',
        )
        self.assertNotContains(detail_response, '<script>')

        hidden_project = PortfolioProject.objects.create(
            title='Hidden Case Study',
            category=PortfolioProject.Category.WEBSITES,
            description='Not published yet.',
            is_active=False,
        )
        public_response = self.client.get(reverse('portfolio'))
        self.assertNotContains(public_response, 'Hidden Case Study')
        self.assertEqual(
            self.client.get(
                reverse('portfolio_detail', args=[hidden_project.pk]),
            ).status_code,
            404,
        )

        response = self.client.post(
            reverse('staff_panel:portfolio_edit', args=[project.pk]),
            {
                'title': 'Nexavira Storefront 2',
                'category': PortfolioProject.Category.WEBSITES,
                'description': 'Updated project details.',
                'technologies': 'Django',
                'display_order': 2,
                'is_active': 'on',
            },
        )
        self.assertRedirects(
            response,
            reverse('staff_panel:portfolio_projects'),
            fetch_redirect_response=False,
        )
        project.refresh_from_db()
        self.assertEqual(project.category, PortfolioProject.Category.WEBSITES)
        self.assertTrue(project.is_active)

        self.assertEqual(
            self.client.post(
                reverse('staff_panel:portfolio_delete', args=[project.pk]),
            ).status_code,
            302,
        )
        self.assertFalse(PortfolioProject.objects.filter(pk=project.pk).exists())
