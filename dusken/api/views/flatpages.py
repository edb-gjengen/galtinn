from django.contrib.flatpages.models import FlatPage
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny

from dusken.api.serializers.flatpages import FlatPageSerializer


class FlatPageDetailView(RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = FlatPageSerializer
    queryset = FlatPage.objects.all()
    lookup_field = "url"

    def ensure_url_slashes(self):
        """Ensure the requested url have leading and trailing slashes, as FlatPage urls are stored with them"""
        url = self.kwargs["url"]
        if not url.startswith("/"):
            url = "/" + url

        if not url.endswith("/"):
            url = url + "/"

        self.kwargs["url"] = url

    def get_object(self):
        self.ensure_url_slashes()
        return super().get_object()
