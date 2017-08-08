from django import template

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group):
    if group is None:
        return False

    return user.has_group(group)


@register.filter(name='has_admin_group')
def has_admin_group(user, group):
    if user.is_superuser:
        return True

    if group is None:
        return False

    return user.has_group(group)
