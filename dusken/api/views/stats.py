from itertools import groupby

from collections import defaultdict
from django.http import JsonResponse
from django.utils.dateparse import parse_date

from dusken.models import Membership


def membership_stats(request):
    start_date = request.GET.get('start_date', None)

    # FIXME: Remove these filters and show life long and trial memberships in front end
    memberships = Membership.objects.exclude(membership_type__slug='trial', order__isnull=True).select_related('order')
    if start_date:
        memberships = memberships.filter(order__created__gte=parse_date(start_date))

    memberships = memberships.order_by('-order__created')
    memberships_grouped = defaultdict(list)
    for key, values in groupby(memberships, key=lambda x: '{}{}'.format(x.order.payment_method, x.order.created.date())):
        sales = list(values)
        method = sales[0].order.payment_method
        memberships_grouped[method].append({
            'sales': len(sales),
            'date': str(sales[0].order.created.date()),
            'payment_method': sales[0].order.payment_method
        })

    data = {
        'memberships': memberships_grouped,
        'payment_methods': list(set(memberships.values_list('order__payment_method', flat=True)))
    }

    return JsonResponse(data)
