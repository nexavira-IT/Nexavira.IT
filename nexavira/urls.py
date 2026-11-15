"""
URL configuration for nexavira project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('nexa-it/', include('nexaviraapp.admin_urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('', include('nexaviraapp.urls')),
]

urlpatterns += static(
    settings.PORTFOLIO_IMAGE_URL,
    document_root=settings.PORTFOLIO_IMAGE_ROOT,
)

handler404 = 'nexaviraapp.views.page_not_found'
