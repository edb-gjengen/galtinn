from unittest import skip

from django.core.management import call_command
from django.test import TestCase

from django.test.runner import DiscoverRunner


class NoDbTestRunner(DiscoverRunner):
    """ A test runner to test without database creation """

    def setup_databases(self, **kwargs):
        """ Override the database creation defined in parent class """
        pass

    def teardown_databases(self, old_config, **kwargs):
        """ Override the database teardown defined in parent class """
        pass


class ImportTestCase(TestCase):
    # @skip('Uncomment this if you want to test the import script')
    def test_import_inside_users(self):
        call_command('import_inside_users')
        # self.assertEquals(out, 'OK')
