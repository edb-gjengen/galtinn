from django.views.generic import TemplateView


class GenericOauth2Callback(TemplateView):
    template_name = "dusken/generic_oauth2_callback.html"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "code": self.request.GET.get("code"),
            "error": self.request.GET.get("error"),
            "error_description": self.request.GET.get("error_description"),
        }
