"""Utilities.

.. versionadded:: 0.5.0
"""

import os
import string


def check_type(obj, classinfo, name='object', msg=None):
    """Check the type of an object.

    >>> utils.check_type(1, str, 'num')
    Traceback (most recent call last):
      ...
    TypeError: the type of 'num' must be 'str', got 'int'
    >>> utils.check_type(1, (str, float), 'num')
    Traceback (most recent call last):
      ...
    TypeError: the type of 'num' must be one of 'str, float', got 'int'
    >>> utils.check_type(1, str, msg='wrong type for num')
    Traceback (most recent call last):
      ...
    TypeError: wrong type for num

    :param object obj: the object
    :param classinfo: see :func:`isinstance`
    :param str name: name shown in the exception message
    :param str msg: message for the exception
    :raises TypeError: if the check fails
    """
    if not isinstance(obj, classinfo):
        if not msg:
            if isinstance(classinfo, tuple):
                msg = ('the type of %r must be one of %r, got %r' %
                       (name, ', '.join(map(lambda x: x.__name__, classinfo)),
                        obj.__class__.__name__))
            else:
                msg = ('the type of %r must be %r, got %r' %
                       (name, classinfo.__name__, obj.__class__.__name__))
        raise TypeError(msg)


def check_path_like(obj, name='object', msg=None):
    """Check if an object is a :term:`path-like object`.

    :param object obj: the object
    :param str name: name shown in the exception message
    :param str msg: alternative message
    :raises TypeError: if the check fails
    """
    if not msg:
        msg = ('%r must be a path-like object, got %r' %
               (name, obj.__class__.__name__))
    check_type(obj, (str, bytes, os.PathLike), None, msg)


def check_bytes_like(obj, name='object', msg=None):
    """Check if an object is a :term:`bytes-like object`.

    :param object obj: the object
    :param str name: name shown in the exception message
    :param str msg: alternative message
    :raises TypeError: if the check fails
    """
    if not msg:
        msg = ('%r must be a bytes-like object, got %r' %
               (name, obj.__class__.__name__))
    try:
        memoryview(obj)
    except TypeError:
        raise TypeError(msg) from None


def validate_iban(iban):
    """Validate an IBAN.

    IBAN = International Bank Account Number

    The IBAN must not contain any separators;
    only the characters ``A-Z`` and ``0-9`` are allowed.

    :param str iban: the IBAN
    :return: ``True`` if the IBAN is valid
    :rtype: bool

    .. versionadded:: 0.9.0
    """
    allowed = string.digits + string.ascii_uppercase
    s = []
    for c in iban[4:] + iban[:4]:
        if c not in allowed:
            return False
        if c in string.digits:
            s.append(c)
        else:
            s.append(str(ord(c) - 55))
    return int(''.join(s)) % 97 == 1
