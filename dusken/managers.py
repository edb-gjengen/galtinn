from django.contrib.auth.models import UserManager
from django.db.models import Q, QuerySet
from django.utils import timezone


class DuskenUserQuerySet(QuerySet):
    def get_membership_query(self):
        return Q(memberships__isnull=False, memberships__end_date__isnull=True) | Q(memberships__end_date__gt=timezone.now().date())

    def with_valid_membership(self):
        """ Users with a valid membership"""
        return self.filter(self.get_membership_query())

    def no_valid_membership(self):
        """ Users with NO valid membership"""
        return self.exclude(self.get_membership_query())

    def by_membership_end_date(self):
        return self.order_by('-memberships__end_date')

class DuskenUserManager(UserManager):
    def get_queryset(self):
        return DuskenUserQuerySet(self.model, using=self._db)

    def with_valid_membership(self):
        return self.get_queryset().with_valid_membership()

    def no_valid_membership(self):
        return self.get_queryset().no_valid_membership()

    def by_membership_end_date(self):
        return self.get_queryset().by_membership_end_date()
