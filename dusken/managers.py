from django.contrib.auth.models import UserManager
from django.db.models import Q, QuerySet
from django.utils import timezone


class DuskenUserQuerySet(QuerySet):
    def with_valid_membership(self):
        """ Get all users with valid membership"""
        query = Q(memberships__isnull=False, memberships__end_date__isnull=True) | Q(memberships__end_date__gt=timezone.now().date())
        return self.filter(query)


class DuskenUserManager(UserManager):
    def get_queryset(self):
        return DuskenUserQuerySet(self.model, using=self._db)

    def with_valid_membership(self):
        return self.get_queryset().with_valid_membership()
