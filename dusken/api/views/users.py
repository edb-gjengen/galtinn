import django_filters
from django.http import HttpResponseForbidden, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend, FilterSet
from phonenumber_field.modelfields import PhoneNumberField
from rest_framework import filters, permissions, viewsets
from rest_framework.generics import CreateAPIView, RetrieveAPIView

from dusken.api.serializers.users import DuskenUserRegisterSerializer, DuskenUserSerializer
from dusken.authentication import UsernameBasicAuthentication
from dusken.models import DuskenUser


class DuskenUserFilter(FilterSet):
    class Meta:
        model = DuskenUser
        fields = ("username", "email", "phone_number")
        filter_overrides = {PhoneNumberField: {"filter_class": django_filters.CharFilter}}


class DuskenUserViewSet(viewsets.ModelViewSet):
    """DuskenUser API"""

    queryset = DuskenUser.objects.all().order_by("id")
    serializer_class = DuskenUserSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
    )
    filterset_class = DuskenUserFilter
    search_fields = ("first_name", "last_name", "email", "member_cards__card_number", "phone_number")
    lookup_field = "id"

    def get_queryset(self):
        if self.request.user.has_perm("dusken.view_duskenuser"):
            return self.queryset
        return self.queryset.filter(pk=self.request.user.pk)


class CurrentUserView(RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DuskenUserSerializer

    def get_object(self):
        return self.request.user


class RegisterUserView(CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DuskenUserRegisterSerializer
    queryset = DuskenUser.objects.all()


def user_pk_to_uuid(request):
    if not request.user.is_authenticated or not (request.user.is_volunteer or request.user.is_superuser):
        return HttpResponseForbidden()
    user_pk = request.GET.get("user", None)
    user = DuskenUser.objects.get(pk=user_pk)

    data = {"uuid": user.uuid}
    return JsonResponse(data)


class BasicAuthCurrentUserView(CurrentUserView):
    authentication_classes = [UsernameBasicAuthentication]
    # FIXME: Rate limit per custom auth-user-ip header (from galtinn)
