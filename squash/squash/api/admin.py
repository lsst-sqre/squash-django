from django.contrib import admin
from squash.api.models import Job, Metric, Measurement, VersionedPackage

admin.site.register(Job)
admin.site.register(Metric)
admin.site.register(Measurement)
admin.site.register(VersionedPackage)
