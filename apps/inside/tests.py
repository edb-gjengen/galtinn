from unittest import skip

from django.core.management import call_command
from django.db.models import Q
from django.test import TestCase

from django.test.runner import DiscoverRunner
from django.utils import timezone

from apps.common.utils import log_time
from apps.inside.models import InsideUser
from dusken.models import DuskenUser


class NoDbTestRunner(DiscoverRunner):
    """ A test runner to test without database creation """

    def setup_databases(self, **kwargs):
        """ Override the database creation defined in parent class """
        pass

    def teardown_databases(self, old_config, **kwargs):
        """ Override the database teardown defined in parent class """
        pass


class ImportTestCase(TestCase):
    @skip('Uncomment this if you want to test the import script')
    # @log_time("Running import test case...\n")
    def test_import_inside_users(self):
        self.assertEqual(DuskenUser.objects.all().with_valid_membership().count(), 0)
        query = Q(expires__gte=timezone.now().date()) | Q(expires=None)
        valid_inside_memberships = InsideUser.objects.filter(query).count()
        call_command('import_inside_users')
        self.assertGreaterEqual(DuskenUser.objects.all().with_valid_membership().count(), valid_inside_memberships)
