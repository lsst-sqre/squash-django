from ast import literal_eval

from rest_framework import authentication, permissions,\
    viewsets, filters, response, status

from rest_framework_extensions.cache.mixins import CacheResponseMixin

from .forms import JobFilter
from .models import Job, Metric, Measurement
from .serializers import JobSerializer, MetricSerializer,\
    RegressionSerializer


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

    paginate_by = 100

    # list of available filter_backends, will enable these for all ViewSets
    filter_backends = (
        filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )


class JobViewSet(DefaultsMixin, CacheResponseMixin, viewsets.ModelViewSet):
    """API endpoint for listing and creating jobs"""

    queryset = Job.objects.\
        prefetch_related('packages', 'measurements').order_by('date')
    serializer_class = JobSerializer
    filter_class = JobFilter
    search_fields = ('ci_id',)
    ordering_fields = ('date',)


class MeasurementViewSet(DefaultsMixin, CacheResponseMixin,
                         viewsets.ModelViewSet):
    """API endpoint for listing data consumed by the squash-bokeh monitor app"""

    queryset = Measurement.objects.\
        prefetch_related('job', 'metric').order_by('job__date')
    serializer_class = RegressionSerializer
    filter_fields = ('job__ci_dataset', 'metric')


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

    search_fields = ('metric', )
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

        # we want to see results for the latest job by default
        jobs = Job.objects.values('ci_id', 'ci_dataset')

        ci_id = None
        ci_dataset = None

        if jobs.exists():
            ci_id, ci_dataset = jobs.latest('pk')

        # we want to see always the same metric by default
        metrics = Metric.objects.values_list('metric', flat=True)

        metric = None
        if metrics.exists():
            metric = metrics[0]

        # these values are arbitrary
        snr_cut = '100'
        window = 'months'

        return {'ci_id': ci_id, 'ci_dataset': ci_dataset,
                'metric': metric, 'snr_cut': snr_cut,
                'window': window}

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
