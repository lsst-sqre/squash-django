from rest_framework import serializers
from rest_framework.reverse import reverse
from .models import Job, Metric, Measurement, VersionedPackage
from django.db import transaction


class MetricSerializer(serializers.ModelSerializer):
    """Serializer for `models.Metric` objects.
    """

    links = serializers.SerializerMethodField()

    class Meta:
        model = Metric
        fields = ('metric', 'unit', 'description', 'operator',
                  'parameters', 'specs', 'reference', 'links',)

    def get_links(self, obj):

        request = self.context['request']
        metric = reverse('metric-detail', kwargs={'pk': obj.pk},
                         request=request)

        data = {
            'self': metric,
        }
        return data


class MeasurementSerializer(serializers.ModelSerializer):
    """Serializer for `models.Measurement` objects.

    This serializer is intended to be nested inside the JobSerializer's
    `measurements` field.
    """

    class Meta:
        model = Measurement
        fields = ('metric', 'value', 'metadata',)


class VersionedPackageSerializer(serializers.ModelSerializer):
    """Serializer for `models.VersionedPackage` objects.

    This serializer is intended to be nested inside the JobSerializer; the
    `packages` in Jobs includes a list of VersionedPackages for all packages
    used in a Job.
    """

    class Meta:
        model = VersionedPackage
        fields = ('name', 'git_url', 'git_commit', 'git_branch',
                  'build_version')


class JobSerializer(serializers.ModelSerializer):

    links = serializers.SerializerMethodField()

    measurements = MeasurementSerializer(many=True)
    packages = VersionedPackageSerializer(many=True)

    class Meta:
        model = Job
        fields = ('ci_id', 'ci_name', 'ci_dataset', 'ci_label', 'date',
                  'ci_url', 'status', 'blobs', 'measurements', 'packages',
                  'links')

    # Override the create method to create nested objects from request data
    def create(self, data):
        measurements = data.pop('measurements')
        packages = data.pop('packages')

        # Use transactions, so that if one of the measurement objects isn't
        # valid that we will rollback even the parent Job object creation
        with transaction.atomic():
            job = Job.objects.create(**data)
            for measurement in measurements:
                Measurement.objects.create(job=job, **measurement)
            for package in packages:
                VersionedPackage.objects.create(job=job, **package)

        return job

    def get_links(self, obj):

        request = self.context['request']
        return {
            'self': reverse('job-detail', kwargs={'pk': obj.pk},
                            request=request),
        }
