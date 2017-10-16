import graphene
import squash.api.schema

from graphene_django.debug import DjangoDebug


class Query(squash.api.schema.Query, graphene.ObjectType):
    debug = graphene.Field(DjangoDebug, name='__debug')

schema = graphene.Schema(query=Query)
