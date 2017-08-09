from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def google_analytics_tag():
    ga_script_tag = """<script>
        (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
        (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
        m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
        })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');

        ga('create', '%s', 'auto');
        ga('send', 'pageview');
    </script>"""

    property_id = settings.GOOGLE_ANALYTICS_PROPERTY_ID
    if not property_id:
        return ''

    return mark_safe(ga_script_tag % property_id)
