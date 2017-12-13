import graphene
from django.db.models import DurationField
from graphene_django.converter import convert_django_field
from graphene_django.types import DjangoObjectType

from dusken.models import MembershipType


@convert_django_field.register(DurationField)
def convert_stream_field_to_string(field, registry=None):
    # This serializes MembershipType.duration as a string
    return graphene.String()


class MembershipTypeType(DjangoObjectType):
    """MembershipType"""
    class Meta:
        model = MembershipType


class DuskenQuery:
    membership_types = graphene.List(MembershipTypeType, is_default=graphene.Boolean())

    def resolve_membership_types(self, info, is_default=None):
        query = {}
        if is_default is not None:
            query['is_default'] = is_default
        return MembershipType.objects.filter(**query)


class Query(DuskenQuery, graphene.ObjectType):
    """This class can inherit from multiple queries if we want add more apps to the project"""
    # TODO: Add opening hours and other static app info from a separate app


schema = graphene.Schema(query=Query)
