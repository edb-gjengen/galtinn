# coding: utf-8
import datetime
import phonenumbers


def format_phone_number(number):
    if len(number) == 0:
        return number

    try:
        p = phonenumbers.parse(number, region='NO')
    except phonenumbers.NumberParseException:
        return number

    if not phonenumbers.is_valid_number(p):
        return number

    return phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)


def is_autumn():
    today = datetime.date.today()
    _min = datetime.date(year=today.year, month=8, day=1)
    _max = datetime.date(year=today.year + 1, month=1, day=1)
    return _min <= today < _max
