from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import JobApplication, JobOpportunity, PortfolioProject


class StaffAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError(
                'This account does not have access to the management panel.',
                code='not_staff',
            )


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ('name', 'email', 'phone', 'resume', 'cover_letter')
        labels = {
            'name': 'Full name',
            'email': 'Email address',
            'phone': 'Phone number',
            'resume': 'Resume',
            'cover_letter': 'Cover letter (optional)',
        }
        help_texts = {
            'resume': 'PDF, DOC, or DOCX; maximum 5 MB.',
        }
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'name'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'phone': forms.TelInput(attrs={'autocomplete': 'tel'}),
            'resume': forms.ClearableFileInput(attrs={'accept': '.pdf,.doc,.docx'}),
            'cover_letter': forms.Textarea(attrs={'rows': 5}),
        }


class JobOpportunityForm(forms.ModelForm):
    class Meta:
        model = JobOpportunity
        fields = (
            'title',
            'description',
            'location',
            'employment_type',
            'workplace_type',
            'is_active',
        )
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Software Engineer'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Dhaka / Remote'}),
        }


class JobApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ('status',)


class PortfolioProjectForm(forms.ModelForm):
    class Meta:
        model = PortfolioProject
        fields = (
            'title',
            'category',
            'description',
            'technologies',
            'image',
            'project_url',
            'is_active',
            'display_order',
        )
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Northline Studio'}),
            'project_url': forms.URLInput(
                attrs={'placeholder': 'https://example.com'}
            ),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }
