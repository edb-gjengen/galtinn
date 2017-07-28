from django.contrib.auth.hashers import Argon2PasswordHasher
from passlib.handlers.mysql import mysql41


def mysql_create(raw_password):
    return mysql41.encrypt(raw_password)


class Argon2WrappedMSQL41Hasher(Argon2PasswordHasher):
    """ This hasher is to support legacy MySQL 4.1 passwords"""
    # TODO: https://docs.djangoproject.com/en/1.11/topics/auth/passwords/#password-upgrading-without-requiring-a-login
    # TODO: Write a data migration taking all passwords not containing a $ and starting with * and double hash them
    # TODO: Test this
    algorithm = 'argon2_wrapped_unsalted_sha1sha1'

    def encode_sha1_sha1_hash(self, sha1sha1_hash, salt):
        return super().encode(sha1sha1_hash, salt)

    def encode(self, password, salt):
        sha1sha1_hash = mysql_create(password)
        return self.encode_sha1_sha1_hash(sha1sha1_hash, salt)

