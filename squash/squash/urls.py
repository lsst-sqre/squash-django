"""squash URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings

from rest_framework.routers import DefaultRouter
from api import views

admin.site.site_header = 'SQuaSH API'

api_router = DefaultRouter()
api_router.register(r'jobs', views.JobViewSet)
api_router.register(r'metrics', views.MetricViewSet)
api_router.register(r'datasets', views.DatasetViewSet,
                    base_name='datasets')
api_router.register(r'defaults', views.DefaultsViewSet,
                    base_name='defaults')

# endpoints for data consumed by the bokeh apps
api_router.register(r'measurements', views.MeasurementViewSet,
                    base_name='measurements')
api_router.register(r'apps', views.AppViewSet,
                    base_name='apps')

urlpatterns = [
    url(r'^', include(api_router.urls)),
    url(r'^admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [url(r'^__debug__/',
                       include(debug_toolbar.urls)), ] + urlpatterns


