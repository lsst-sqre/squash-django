import graphene

from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from squash.api.models import Metric, Measurement


class Metrics(DjangoObjectType):
    class Meta:
        model = Metric

class Measurements(DjangoObjectType):
    class Meta:
        model = Measurement
        interfaces = (graphene.Node, )
        filter_fields = {
            'metric': ['exact'],
            'job__ci_dataset': ['exact'],
        }

class Query(graphene.AbstractType):
    metrics = graphene.List(Metrics)

    @graphene.resolve_only_args
    def resolve_metrics(self):
        return Metric.objects.all()

    measurements = DjangoFilterConnectionField(Measurements, description="Metric measurements")

