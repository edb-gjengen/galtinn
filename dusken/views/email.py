from django.views.generic import TemplateView


class EmailSubscriptions(TemplateView):
    template_name = 'dusken/email_subscriptions.html'

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(),

        }
