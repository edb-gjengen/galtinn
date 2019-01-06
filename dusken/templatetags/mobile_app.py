from django import template
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils.translation import get_language
from rest_framework.authtoken.models import Token

register = template.Library()


@register.inclusion_tag('dusken/components/app_download.html', takes_context=True)
def show_app_download(context):
    """ Based on the user agent and selected language, show a download badge, but only on payment success"""
    user_agent = context['request'].META.get('HTTP_USER_AGENT', '')
    language_code = get_language()
    app_resources = {
        'android': {
            'app_url': 'market://details?id=no.neuf.chateau',
            'app_image': static('app/images/google_play_{}_badge_web_generic.png'.format(language_code)),
        },
        'ios': {
            'app_url': 'https://itunes.apple.com/us/app/chateau-neuf/id1262532938?ls=1&mt=8',
            'app_image': static('app/images/app_store_badge_{}.svg'.format(language_code)),
        },
    }
    os = 'unknown'
    if 'Android' in user_agent:
        os = 'android'
        context.update(app_resources[os])
    elif 'iPhone' in user_agent:
        os = 'ios'
        context.update(app_resources[os])
    else:
        # Link to Play Store on web (no deeplink)
        app_resources['android']['app_url'] = 'https://play.google.com/store/apps/details?id=no.neuf.chateau'

    context['user_os'] = os
    context['app_resources'] = app_resources

    has_token = Token.objects.filter(user=context['request'].user).exists()
    if context['request'].GET.get('payment_success') and not has_token:
        context['show_app_download'] = True

    return context
