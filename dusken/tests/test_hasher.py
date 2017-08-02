from django.test import TestCase
from django.utils.crypto import get_random_string

from dusken.hashers import Argon2WrappedMySQL41PasswordHasher


class HasherTestCase(TestCase):
    def test_hash_password(self):
        raw_password = 'yoloyolo'
        salt = get_random_string()
        wrapped_hasher = Argon2WrappedMySQL41PasswordHasher()

        encoded = wrapped_hasher.encode(raw_password, salt)
        self.assertTrue(wrapped_hasher.verify(raw_password, encoded))
