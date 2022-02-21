from django.contrib.auth.models import UserManager
from django.db.models import Manager, Q, QuerySet
from django.utils import timezone


class DuskenUserQuerySet(QuerySet):
    def get_membership_query(self):
        return Q(memberships__isnull=False, memberships__end_date__isnull=True) | Q(
            memberships__end_date__gt=timezone.now().date()
        )

    def with_valid_membership(self):
        """Users with a valid membership"""
        return self.filter(self.get_membership_query())

    def no_valid_membership(self):
        """Users with NO valid membership"""
        return self.exclude(self.get_membership_query())

    def by_membership_end_date(self):
        return self.order_by("-memberships__end_date")


class DuskenUserManager(UserManager):
    def get_queryset(self):
        return DuskenUserQuerySet(self.model, using=self._db)

    def with_valid_membership(self):
        return self.get_queryset().with_valid_membership()

    def no_valid_membership(self):
        return self.get_queryset().no_valid_membership()

    def by_membership_end_date(self):
        return self.get_queryset().by_membership_end_date()


class OrderQuerySet(QuerySet):
    def unclaimed(self, phone_number=None, member_card=None):
        return self.filter(
            Q(user__isnull=True)
            & (
                Q(phone_number__isnull=False, phone_number=phone_number)
                | Q(member_card__isnull=False, member_card=member_card)
            )
        ).order_by("-created")


class OrderManager(Manager):
    def get_queryset(self):
        return OrderQuerySet(self.model, using=self._db)

    def unclaimed(self, phone_number=None, member_card=None):
        return self.get_queryset().unclaimed(phone_number, member_card)


class MembershipQuerySet(QuerySet):
    def valid(self):
        from dusken.models import MembershipType

        is_lifelong = Q(membership_type__expiry_type=MembershipType.EXPIRY_NEVER, end_date__isnull=True)
        is_valid_duration = Q(
            membership_type__expiry_type=MembershipType.EXPIRY_DURATION, end_date__gte=timezone.now().date()
        )
        query = is_lifelong | is_valid_duration
        return self.filter(query)


class MembershipManager(Manager):
    def get_queryset(self):
        return MembershipQuerySet(self.model, using=self._db)

    def valid(self):
        return self.get_queryset().valid()
