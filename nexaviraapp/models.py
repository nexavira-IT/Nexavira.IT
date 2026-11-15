from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

# Create your models here.
class contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    company = models.CharField(max_length=100)
    service = models.CharField(max_length=100)
    message = models.TextField()

    def __str__(self):
        return self.name


def validate_resume_file(file):
    if file.size > 5 * 1024 * 1024:
        raise ValidationError('Resume files must be 5 MB or smaller.')

    extension = file.name.rsplit('.', 1)[-1].lower()
    file.seek(0)
    signature = file.read(8)
    file.seek(0)

    valid_signatures = {
        'pdf': signature.startswith(b'%PDF-'),
        'doc': signature.startswith(bytes.fromhex('D0CF11E0A1B11AE1')),
        'docx': signature.startswith(b'PK\x03\x04'),
    }
    if not valid_signatures.get(extension, False):
        raise ValidationError('Upload a valid PDF, DOC, or DOCX resume.')


class JobOpportunity(models.Model):
    class EmploymentType(models.TextChoices):
        FULL_TIME = 'full_time', 'Full-time'
        PART_TIME = 'part_time', 'Part-time'
        CONTRACT = 'contract', 'Contract'
        INTERNSHIP = 'internship', 'Internship'

    class WorkplaceType(models.TextChoices):
        REMOTE = 'remote', 'Remote'
        HYBRID = 'hybrid', 'Hybrid'
        ON_SITE = 'on_site', 'On-site'

    title = models.CharField(max_length=150)
    description = CKEditor5Field('Description', config_name='default')
    location = models.CharField(max_length=120)
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    workplace_type = models.CharField(
        max_length=10,
        choices=WorkplaceType.choices,
        default=WorkplaceType.ON_SITE,
        verbose_name='Work arrangement',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Show on Career page',
        help_text='Uncheck this to hide the job from public visitors.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name_plural = 'Job opportunities'

    def __str__(self):
        return self.title


class JobApplication(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        REVIEWING = 'reviewing', 'Reviewing'
        SHORTLISTED = 'shortlisted', 'Shortlisted'
        REJECTED = 'rejected', 'Rejected'
        HIRED = 'hired', 'Hired'

    job = models.ForeignKey(
        JobOpportunity,
        on_delete=models.PROTECT,
        related_name='applications',
    )
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    resume = models.FileField(
        upload_to='job-applications/resumes/',
        validators=[validate_resume_file],
    )
    cover_letter = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-submitted_at',)

    def __str__(self):
        return f'{self.name} — {self.job.title}'


@deconstructible
class PortfolioImageStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(
            location=settings.PORTFOLIO_IMAGE_ROOT,
            base_url=settings.PORTFOLIO_IMAGE_URL,
        )


class PortfolioProject(models.Model):
    class Category(models.TextChoices):
        WEBSITES = 'websites', 'Websites'
        ECOMMERCE = 'ecommerce', 'E-commerce'
        WEB_APPLICATIONS = 'web-applications', 'Web applications'
        WORDPRESS = 'wordpress', 'WordPress'

    title = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=Category.choices)
    description = CKEditor5Field('Description', config_name='default')
    technologies = models.CharField(
        max_length=250,
        blank=True,
        help_text='Separate technologies with commas.',
    )
    image = models.ImageField(
        upload_to='',
        storage=PortfolioImageStorage(),
        blank=True,
    )
    project_url = models.URLField(blank=True, verbose_name='Project URL')
    is_active = models.BooleanField(
        default=True,
        verbose_name='Show on Portfolio page',
    )
    display_order = models.PositiveIntegerField(
        default=0,
        help_text='Lower numbers appear first.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('display_order', '-created_at')
        verbose_name = 'Portfolio project'
        verbose_name_plural = 'Portfolio projects'

    def __str__(self):
        return self.title

    @property
    def technology_list(self):
        return [
            technology.strip()
            for technology in self.technologies.split(',')
            if technology.strip()
        ]