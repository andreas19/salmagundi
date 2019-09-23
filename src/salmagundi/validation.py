"""Data validation.

.. versionadded:: 0.9.0
"""

import itertools
import string

from .strings import TranslationTable


_iban_trans_table = TranslationTable(dict(zip(string.ascii_uppercase,
                                              map(str, range(10, 36)))),
                                     string.digits)


def is_valid_iban(s):
    """Check whether a string is a valid IBAN.

    IBAN = `International Bank Account Number
    <https://en.wikipedia.org/wiki/International_Bank_Account_Number>`_

    The string must not contain any separators;
    only the characters ``A-Z`` and ``0-9`` are allowed.

    :param str s: the string
    :return: ``True`` if the string is a valid IBAN
    :rtype: bool
    :raise ValueError: if a character is not allowed
    """
    return int((s[4:] + s[:4]).translate(_iban_trans_table)) % 97 == 1


def is_valid_ean13(s):
    """Check whether a string is a valid EAN-13.

    EAN = `European Article Number
    <https://en.wikipedia.org/wiki/European_Article_Number>`_

    The string must not contain any separators; only the characters ``0-9``
    are allowed and the length of the string must be 13.

    :param str s: the string
    :return: ``True`` if the string is a valid EAN-13
    :rtype: bool
    :raise ValueError: if a character is not allowed or the length is wrong
    """
    if len(s) != 13:
        raise ValueError('length of string must be 13 not %d' % len(s))
    if not s.isdecimal():
        raise ValueError('only characters 0-9 are allowed')
    return sum(int(c) * w for c, w in zip(s, itertools.cycle((1, 3)))) % 10 == 0


def is_valid_isbn(s):
    """Check whether a string is a valid ISBN.

    ISBN = `International Standard Book Number
    <https://en.wikipedia.org/wiki/International_Standard_Book_Number>`_

    The string must not contain any separators; only the characters ``0-9``
    plus ``X`` for ISBN-10 are allowed and the length of the string must be
    either 10 or 13.

    :param str s: the string
    :return: ``True`` if the string is a valid ISBN
    :rtype: bool
    :raise ValueError: if a character is not allowed or the length is wrong
    """
    if len(s) == 13:
        if s[0:3] not in ('978', '979'):
            raise ValueError('ISBN-13 must start with 978 or 979')
        return is_valid_ean13(s)
    if len(s) not in (10, 13):
        raise ValueError('length of string must be 10 or 13 not %d' % len(s))
    if not (s[:-1].isdecimal() and (s[-1].isdecimal() or s[-1] == 'X')):
        raise ValueError('only characters 0-9 and X are allowed')
    return ((sum(int(c) * w for c, w in zip(s[:-1], range(10, 1, -1))) +
            (10 if s[-1] == 'X' else int(s[-1]))) % 11 == 0)


def is_valid_luhn(s):
    """Check whether a string is valid according to the Luhn algorithm.

    The `Luhn algorithm
    <https://en.wikipedia.org/wiki/Luhn_algorithm>`_ is used to validate
    a variety of identification numbers, e.g. credit card numbers.

    The string must not contain any separators; only the characters ``0-9``
    are allowed.

    :param str s: the string
    :return: ``True`` if the string is valid
    :rtype: bool
    :raise ValueError: if a character is not allowed
    """
    if not s.isdecimal():
        raise ValueError('only characters 0-9 are allowed')
    return sum(sum(divmod(int(c) * w, 10))
               for c, w in zip(s[::-1], itertools.cycle((1, 2)))) % 10 == 0
