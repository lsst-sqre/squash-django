from ast import literal_eval
import pandas as pd
from operator import itemgetter
from django.db import connection

from rest_framework import authentication, permissions,\
    viewsets, filters, response, status

from rest_framework_extensions.cache.mixins import CacheResponseMixin

from .forms import JobFilter
from .models import Job, Metric, Measurement, VersionedPackage
from .serializers import JobSerializer, MetricSerializer


class DefaultsMixin(object):
    """
    Default settings for view authentication, permissions,
    filtering and pagination.
    """

    authentication_classes = (
        authentication.BasicAuthentication,
        authentication.TokenAuthentication,
    )

    permission_classes = (
        permissions.IsAuthenticatedOrReadOnly,
    )

    paginate_by = 25

    # list of available filter_backends, will enable these for all ViewSets
    filter_backends = (
        filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )


class JobViewSet(DefaultsMixin, CacheResponseMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating ci jobs"""

    queryset = Job.objects.\
        prefetch_related('packages', 'measurements').order_by('date')
    serializer_class = JobSerializer
    filter_class = JobFilter
    search_fields = ('ci_id',)
    ordering_fields = ('date',)


class CodeChangesViewSet(DefaultsMixin, CacheResponseMixin, viewsets.ViewSet):
    """API endpoint consumed by the Monitor app. It returns the list of packages
    that changed wrt to the previous ci job"""

    def get_packages(self, job):
        queryset = VersionedPackage.objects.\
            filter(job=job).values('name',
                                   'git_commit',
                                   'git_url')

        return set(map(itemgetter('name',
                                  'git_commit',
                                  'git_url'), queryset))

    def compute_code_changes(self, queryset):
        """ This method detects:
        - new packages present in the current job but not present in the
        previous one
        - packages present in the previous job but removed in the current one
        - packages present in both the current and previous jobs that
        changed (according to the git commit sha)
        """
        code_changes = []

        for job in queryset:
            current = self.get_packages(job)
            ci_id = job.ci_id
            try:
                # jobs are sorted by date because ci_id is a char
                previous_job = job.get_previous_by_date()

                # make sure previous is not the current ci_id
                while ci_id == previous_job.ci_id:
                    previous_job = previous_job.get_previous_by_date()
            except:
                # in case we don't have a previous job
                previous_job = job

            previous = self.get_packages(previous_job)
            packages = current.difference(previous)

            if packages:
                code_changes.append({'ci_id': ci_id,
                                     'packages': packages,
                                     'count': len(packages)})
        return code_changes

    def list(self, request):
        """Return list of packages as pandas df"""

        queryset = Job.objects.all().order_by('date')

        ci_dataset = self.request.query_params.get('ci_dataset', None)

        if ci_dataset is not None:
            queryset = queryset.filter(ci_dataset=ci_dataset)

        code_changes = self.compute_code_changes(queryset)

        return response.Response(pd.DataFrame(code_changes))


class MeasurementViewSet(DefaultsMixin, CacheResponseMixin, viewsets.ViewSet):
    """API endpoint consumed by the monitor app. It returns measurements for the
    selected metric and ci_dataset"""

    def to_df(self, queryset):
        """ SQuaSH API optmization using Django querysets with Pandas
            https://www.iwoca.co.uk/blog/2016/09/02/using-pandas-django-faster/
        """
        try:
            query, params = queryset.query.sql_with_params()
        except EmptyResultSet: # noqa
            # Occurs when Django tries to create an expression for a
            # query which will certainly be empty
            # e.g. Book.objects.filter(author__in=[])
            return pd.DataFrame()

        return pd.io.sql.read_sql_query(query, connection, params=params)

    def list(self, request):
        """
        Return a pandas data frame to feed the monitor app

        Optionally constraints the returned measurements
        by filtering against the `metric` query parameter in the URL.
        """
        queryset = Measurement.objects.\
            prefetch_related('metric', 'job').order_by('job__date')

        metric = self.request.query_params.get('metric', None)

        if metric is not None:
            queryset = queryset.filter(metric=metric)

        ci_dataset = self.request.query_params.get('ci_dataset', None)

        if ci_dataset is not None:
            queryset = queryset.filter(job__ci_dataset=ci_dataset)

        df = self.to_df(queryset.values('job__ci_dataset', 'job__ci_id',
                                        'job__date', 'job__ci_url', 'value',
                                        'metric'))

        return response.Response(df)


class MetricViewSet(DefaultsMixin, CacheResponseMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating metrics"""

    queryset = Metric.objects.order_by('metric')
    serializer_class = MetricSerializer

    def create(self, request, *args, **kwargs):
        # many=True for adding multiple items at once
        serializer = self.get_serializer(data=request.data,
                                         many=isinstance(request.data, list))
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data,
                                 status=status.HTTP_201_CREATED)

    search_fields = ('metric',)
    ordering_fields = ('metric',)


class DatasetViewSet(DefaultsMixin, viewsets.ViewSet):
    """API endpoint for listing datasets"""

    def list(self, request):
        datasets = Job.objects.values_list('ci_dataset', flat=True).distinct()
        return response.Response(datasets)


class DefaultsViewSet(DefaultsMixin, viewsets.ViewSet):
    """
    API endpoint for listing default values used by
    the squash-bokeh apps
    """

    def get_defaults(self):

        ci_id = None
        ci_dataset = None

        # by default user wants to see results for the latest job
        job = Job.objects.values('ci_id', 'ci_dataset').order_by('-id')

        if job.exists():
            ci_id = job[0]['ci_id']
            ci_dataset = job[0]['ci_dataset']

        # user wants to see always the same metric, pick the first
        metrics = Metric.objects.values_list('metric', flat=True)

        metric = None
        if metrics.exists():
            metric = metrics[0]

        # default values for parameters used by the bokeh apps
        snr_cut = '100'

        return {'ci_id': ci_id, 'ci_dataset': ci_dataset,
                'metric': metric, 'snr_cut': snr_cut}

    def list(self, request):
        defaults = self.get_defaults()
        return response.Response(defaults)


class AppViewSet(DefaultsMixin, viewsets.ViewSet):
    """API endpoint for listing data consumed by the squash-bokeh apps"""

    def get_app_data(self, ci_id, ci_dataset, metric):

        data = {}
        blobs = Job.objects.filter(ci_id=ci_id,
                                   ci_dataset=ci_dataset).values('blobs')
        metadata = Measurement.\
            objects.filter(metric=metric, job__ci_id=ci_id,
                           job__ci_dataset=ci_dataset).values('metadata')

        if metadata.exists():
            # workaround for getting item from queryset
            metadata = metadata[0]['metadata']
            if metadata:
                metadata = literal_eval(literal_eval(metadata))
                blob_id = metadata.pop('blobs')
                data['metadata'] = metadata

                if blobs.exists():
                    # workaround for getting item from queryset
                    blobs = blobs[0]['blobs']
                    if blobs:
                        blobs = literal_eval(literal_eval(blobs))
                        for blob in blobs:
                            # Look up for data blobs
                            if blob['identifier'] == blob_id['matchedDataset']:
                                data['matchedDataset'] = blob['data']

                            elif blob['identifier'] == blob_id['photomModel']:
                                data['photomModel'] = blob['data']

                            elif blob['identifier'] == blob_id['astromModel']:
                                data['astromModel'] = blob['data']
        return data

    def list(self, request):

        defaults = DefaultsViewSet().get_defaults()

        ci_id = self.request.query_params.get('ci_id',
                                              defaults['ci_id'])
        ci_dataset = self.request.query_params.get('ci_dataset',
                                                   defaults['ci_dataset'])
        metric = self.request.query_params.get('metric',
                                               defaults['metric'])
        data = self.get_app_data(ci_id, ci_dataset, metric)

        return response.Response(data)
