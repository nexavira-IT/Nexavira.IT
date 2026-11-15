from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.urls import path, reverse
from django.utils.html import format_html

from . import models


@admin.register(models.contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'company', 'service')
    list_filter = ('service',)
    search_fields = ('name', 'email', 'company', 'phone', 'message')


@admin.register(models.JobOpportunity)
class JobOpportunityAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'employment_type',
        'workplace_type',
        'location',
        'is_active',
        'created_at',
    )
    list_filter = ('is_active', 'employment_type', 'workplace_type', 'location')
    search_fields = ('title', 'description', 'location')
    list_editable = ('is_active',)


@admin.register(models.JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'job', 'email', 'status', 'submitted_at')
    list_filter = ('status', 'job', 'submitted_at')
    search_fields = ('name', 'email', 'phone', 'job__title')
    fields = (
        'job',
        'name',
        'email',
        'phone',
        'resume_download',
        'cover_letter',
        'status',
        'submitted_at',
    )
    readonly_fields = (
        'job',
        'name',
        'email',
        'phone',
        'resume_download',
        'cover_letter',
        'submitted_at',
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/download-resume/',
                self.admin_site.admin_view(self.download_resume),
                name='nexaviraapp_jobapplication_download_resume',
            ),
        ]
        return custom_urls + urls

    def resume_download(self, obj):
        if not obj.resume:
            return 'No resume uploaded'
        url = reverse(
            'staff_panel:application_resume',
            args=(obj.pk,),
        )
        return format_html('<a href="{}">Download resume</a>', url)

    resume_download.short_description = 'Resume'

    def download_resume(self, request, object_id):
        application = self.get_object(request, object_id)
        if application is None or not application.resume:
            raise Http404
        if not self.has_view_or_change_permission(request, application):
            raise PermissionDenied
        return FileResponse(
            application.resume.open('rb'),
            as_attachment=True,
            filename=application.resume.name.rsplit('/', 1)[-1],
        )

    def has_add_permission(self, request):
        return False