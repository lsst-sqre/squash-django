from ast import literal_eval
import pandas as pd
import datetime
import itertools

from django.db import connection

from rest_framework import authentication, permissions,\
    viewsets, filters, response, status

from rest_framework_extensions.cache.mixins import CacheResponseMixin

from .forms import JobFilter
from .models import Job, Metric, Measurement, Job, VersionedPackage
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

    def compute_code_changes(self, queryset):
        """ This method detects differences in the packages between two ci jobs
        - packages present in the current ci job but not present in the
        previous one
        - packages present in the previous job but removed in the current one
        - packages present in both but that have changed according to the git
        commit sha
        """

        # list of unique job id's from the queryset
        ci_ids = []
        for x in queryset:
            if x[0] not in ci_ids:
                ci_ids.append(x[0])

        code_changes = []

        for prev_ci_id, curr_ci_id in self.pairwise(ci_ids):

            # we carry on the pkg name, the git commit sha and the git url
            prev_pkgs = set([(pkg[1], pkg[2], pkg[3])
                             for pkg in queryset if pkg[0] == prev_ci_id])
            curr_pkgs = set([(pkg[1], pkg[2], pkg[3])
                             for pkg in queryset if pkg[0] == curr_ci_id])

            diff_pkgs = curr_pkgs.difference(prev_pkgs)

            if diff_pkgs:
                code_changes.append({'ci_id': curr_ci_id,
                                     'packages': diff_pkgs,
                                     'count': len(diff_pkgs)})
        return code_changes

    def pairwise(self, iterable):
        "s -> (s0,s1), (s1,s2), (s2, s3), ..."
        a, b = itertools.tee(iterable)
        next(b, None)
        return zip(a, b)

    def list(self, request):
        """Return the code changes as a pandas data frame"""

        queryset = Job.objects.prefetch_related('packages')\
            .values_list('ci_id', 'packages__name',
                         'packages__git_commit',
                         'packages__git_url').order_by('date')

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

        period = self.request.query_params.get('period', None)

        if period is not None:
            end = datetime.datetime.today()

            # by default shows last month of data
            start = end - datetime.timedelta(weeks=4)

            if period == "Last year":
                start = end - datetime.timedelta(weeks=48)
            elif period == "Last 6 months":
                start = end - datetime.timedelta(weeks=24)
            elif period == "Last 3 months":
                start = end - datetime.timedelta(weeks=12)

            if period != "All":
                queryset = queryset.filter(job__date__gt=start)

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
        # metrics = Metric.objects.values_list('metric', flat=True)

        # metric = None
        # if metrics.exists():
        #     metric = metrics[0]

        # Temporary workaround for DM-12237

        metric = "AM1"

        # default values for parameters used by the bokeh apps
        snr_cut = '100'

        # default time period to display data
        period = 'Last 6 months'

        return {'ci_id': ci_id, 'ci_dataset': ci_dataset,
                'metric': metric, 'snr_cut': snr_cut, 'period': period}

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

class StatisticsViewSet(DefaultsMixin, viewsets.ViewSet):
    """
    API endpoint for listing statistics shown on the squash
    home page.
    """

    def get_stats(self):

        latest_job = Job.objects.latest('pk')

        number_of_metrics = Metric.objects.count()

        number_of_packages = \
            VersionedPackage.objects.filter(job=latest_job).count()

        number_of_jobs = Job.objects.count()

        number_of_measurements = Measurement.objects.count()

        datasets = Job.objects.values_list('ci_dataset', flat=True).distinct()

        latest_job_date = latest_job.date.strftime("%b %d %Y")

        return { 'number_of_metrics': number_of_metrics,
                'number_of_packages': number_of_packages,
                'number_of_jobs': number_of_jobs,
                'number_of_measurements': number_of_measurements,
                'datasets': ', '.join(datasets),
                'latest_job_date': latest_job_date}

    def list(self, request):
        stats = self.get_stats()
        return response.Response(stats)


