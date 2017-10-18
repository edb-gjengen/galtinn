from itertools import groupby

from django.http import JsonResponse
from django.utils.dateparse import parse_date

from dusken.models import Membership


def membership_stats(request):
    start_date = request.GET.get('start_date', None)

    memberships = Membership.objects.exclude(membership_type__slug='trial')
    if start_date:
        memberships = memberships.filter(start_date__gte=parse_date(start_date))

    memberships = memberships.order_by('-start_date')
    memberships_grouped = []
    for key, values in groupby(memberships, key=lambda x: '{}{}'.format(x.order.payment_method, x.start_date)):
        sales = list(values)
        memberships_grouped.append({
            'sales': len(sales),
            'start_date': str(sales[0].start_date),
            'payment_method': sales[0].order.payment_method
        })

    data = {
        'memberships': memberships_grouped,
        'payment_methods': list(set(memberships.values_list('order__payment_method', flat=True)))
    }

    return JsonResponse(data)
