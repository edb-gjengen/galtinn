from django.contrib.auth.hashers import Argon2PasswordHasher
from passlib.handlers.mysql import mysql41


def mysql_create_password(raw_password):
    return mysql41.encrypt(raw_password)


class Argon2WrappedMySQL41PasswordHasher(Argon2PasswordHasher):
    """ This hasher is to support legacy MySQL 4.1 passwords"""
    algorithm = 'argon2_wrapped_sha1sha1'

    def encode_sha1_sha1_hash(self, sha1sha1_hash, salt):
        return super().encode(sha1sha1_hash, salt)

    def verify(self, password, salt):
        sha1sha1_hash = mysql_create_password(password)
        return super().verify(sha1sha1_hash, salt)

    def encode(self, password, salt):
        sha1sha1_hash = mysql_create_password(password)
        return self.encode_sha1_sha1_hash(sha1sha1_hash, salt)

