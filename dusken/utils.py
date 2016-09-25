import random


def generate_username(first_name, last_name):
    """ Generate a fairly unique username based on first and last name.
        Example: nikolakr1234
    """
    first_name = first_name.encode('ascii', 'ignore').lower()[:6].decode('utf-8')
    last_name = last_name.encode('ascii', 'ignore').lower()[:2].decode('utf-8')
    random_number = random.randint(1, 9999)
    username = '{}{}{:04d}'.format(first_name, last_name, random_number)

    return username


class InlineClass(object):
    def __init__(self, dictionary):
        self.__dict__ = dictionary
