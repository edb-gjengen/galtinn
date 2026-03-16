from django.utils import timezone
from rest_framework import serializers
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from dusken.api.serializers.memberships import MembershipSerializer
from dusken.api.serializers.users import DuskenUserSerializer
from dusken.apps.neuf_auth.models import AuthProfile
from dusken.models import DuskenUser, Membership


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DuskenUser
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "date_of_birth",
            "place_of_study",
            "street_address",
            "street_address_two",
            "postal_code",
            "city",
            "country",
        )


class SetUsernameSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, min_length=3)

    def validate_username(self, value):
        value = value.lower()
        if DuskenUser.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value


class UpdateCurrentUserView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileUpdateSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(DuskenUserSerializer(self.get_object()).data)


class SetUsernameView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.has_set_username:
            return Response({"detail": "Username can only be set once."}, status=400)

        serializer = SetUsernameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        user.username = username
        user.save()
        ap, _ = AuthProfile.objects.get_or_create(user=user)
        ap.username_updated = timezone.now()
        ap.save()
        user.log(f"Username set to {username}")

        return Response(DuskenUserSerializer(user).data)


class CurrentUserMembershipsView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MembershipSerializer
    pagination_class = None

    def get_queryset(self):
        return Membership.objects.filter(user=self.request.user).order_by("-start_date")
