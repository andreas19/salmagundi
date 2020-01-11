"""Data validation.

.. versionadded:: 0.9.0

.. _def-validator-function:

In this module a ``validator function`` is a callable that takes
a value as its only argument and returns normally if the value
is considered valid or raises a :exc:`ValueError` otherwise. It
may raise a :exc:`TypeError` if the value is not of the right type.

.. |VF| replace:: :ref:`validator function <def-validator-function>`
"""

import inspect
import itertools
import math
import re
import string
from collections.abc import Container, Sequence, Mapping, Set
from contextlib import suppress

from .strings import TranslationTable
from .utils import check_type

__all__ = ['chain_validator', 'float_validator', 'func2validator',
           'in_validator', 'int_validator', 'interval_validator',
           'is_valid_ean13', 'is_valid_iban', 'is_valid_isbn', 'is_valid_luhn',
           'length_validator', 'mapping_validator', 'object_validator',
           'pattern_validator', 'properties_validator', 'sequence_validator',
           'set_validator']

# https://en.wikipedia.org/wiki/Bookland
_BOOKLAND = ('978', '979')


def _check_validator_callable(validator):
    if not callable(validator):
        raise TypeError(f'{validator!r} is not callable')
    with suppress(ValueError):
        sig = inspect.signature(validator)
        parameters = sig.parameters
        if len(parameters) != 1:
            raise TypeError('validator must take 1 argument,'
                            f' not {len(parameters)}')


def object_validator(*, validator=None, value_type=None, strict_type=False,
                     allow_none=False):
    """Create a function that checks whether an object is valid.

    >>> # validator for values of type str and length 5-10
    >>> len_vf = length_validator(min_len=5, max_len=10)
    >>> vf = object_validator(validator=len_vf, value_type=str)
    >>> vf('abcde')
    >>> vf('abc')
    Traceback (most recent call last):
      ...
    ValueError: invalid object: 'abc' (length must be in [5, 10], got 3)
    >>> vf(b'abcde')
    Traceback (most recent call last):
      ...
    TypeError: value must be of type 'str', got 'bytes'

    :param validator: |VF|
    :type validator: callable or None
    :param value_type: the type of the value (not checked if ``None``)
    :type value_type: type or None
    :param bool strict_type: if ``True`` instances of subclasses of
                             ``value_type`` are not allowed
    :param bool allow_none: if ``True`` ``None`` values are valid even
                            when ``value_type`` is set
    :return: |VF|
    :raises TypeError: if ``validator`` is not callable or
                       ``value_type`` is not a type-object
    """
    if validator:
        _check_validator_callable(validator)
    if value_type:
        check_type(value_type, type,
                   msg='the value_type argument must be a type-object')

    def f(value):
        if allow_none and value is None:
            return
        if (value_type and (strict_type and type(value) is not value_type or
                            not isinstance(value, value_type))):
            raise TypeError(f'value must be of type {value_type.__name__!r},'
                            f' got {value.__class__.__name__!r}')
        if validator:
            try:
                validator(value)
            except ValueError as ex:
                raise ValueError(f'invalid object: {value!r} ({ex})')

    return f


def interval_validator(*, min_value=None, max_value=None,
                       min_incl=True, max_incl=True):
    """Create a function that checks whether a value is in an interval.

    The type of the checked values must at least support the operators
    ``<`` (for ``*_incl=False``) or ``<=`` (for ``*_incl=True``).

    :param min_value: minimum value (``None`` means no limit)
    :param max_value: maximum value (``None`` means no limit)
    :param bool min_incl: if ``True`` ``min_value`` is included
    :param bool max_incl: if ``True`` ``max_value`` is included
    :return: |VF|
    :raises ValueError: if ``min_value > max_value``
    """
    if (min_value is not None and max_value is not None and
            not (min_value <= max_value)):
        raise ValueError('min_value is greater than max_value'
                         f' ({min_value} > {max_value})')

    def f(value):
        in_range = True
        if min_value is not None:
            if min_incl:
                in_range = min_value <= value
            else:
                in_range = min_value < value
        if in_range and max_value is not None:
            if max_incl:
                in_range = value <= max_value
            else:
                in_range = value < max_value
        if not in_range:
            interval = ''.join([
                '[' if min_incl else ']',
                f'{min_value}, {max_value}',
                ']' if max_incl else '['
            ])
            raise ValueError(f'value {value!r} is not in {interval}')

    return f


def int_validator(*, min_value=None, max_value=None, allow_floats=False):
    """Create a function that checks whether a value is a valid integer.

    If ``allow_floats`` is ``True``, a float value as the argument of the
    returned |VF| will not raise a :exc:`TypeError`. Instead a value that
    represents an integer (such as ``1.0``) and is in the interval
    ``[min_value, max_value]`` will be considered valid. All other cases will
    raise a :exc:`ValueError`.

    :param min_value: minimum value (inclusive, ``None`` means no limit)
    :type min_value: int or None
    :param max_value: maximum value (inclusive, ``None`` means no limit)
    :type max_value: int or None
    :param bool allow_floats: see function description
    :return: |VF|
    :raises ValueError: if ``min_value > max_value``
    :raises TypeError: if ``min_value`` or ``max_value`` are not
                       of type :class:`int`
    """
    if min_value is not None:
        check_type(min_value, int, 'min_value')
    if max_value is not None:
        check_type(max_value, int, 'max_value')
    vf = interval_validator(min_value=min_value, max_value=max_value)

    def f(value):
        if allow_floats and isinstance(value, float):
            if value.is_integer():
                value = int(value)
            else:
                raise ValueError(f'value {value!r} is not in interval')
        else:
            check_type(value, int, 'value')
        vf(value)

    return f


def float_validator(*, min_value=None, max_value=None,
                    min_incl=True, max_incl=True,
                    allow_nan=False, allow_inf=False, allow_ints=False):
    """Create a function that checks whether a value is a valid float.

    :param min_value: minimum value (``None`` means no limit)
    :type min_value: float or None
    :param max_value: maximum value (``None`` means no limit)
    :type max_value: float or None
    :param bool min_incl: if ``True`` ``min_value`` is included
    :param bool max_incl: if ``True`` ``max_value`` is included
    :param bool allow_nan: if ``True`` :data:`math.nan` is allowed as the
                           argument of the returned |VF|
    :param bool allow_inf: if ``True`` :data:`math.inf` is allowed as the
                           argument of the returned |VF|
    :param bool allow_ints: if ``True`` an integer value as the argument of the
                            returned |VF| will not raise a :exc:`TypeError`.
    :return: |VF|
    :raises ValueError: if ``min_value > max_value``
    :raises TypeError: if ``min_value`` or ``max_value`` are not
                       of type :class:`float`
    """
    if min_value is not None:
        check_type(min_value, float, 'min_value')
    if max_value is not None:
        check_type(max_value, float, 'max_value')
    vf = interval_validator(min_value=min_value, max_value=max_value,
                            min_incl=min_incl, max_incl=max_incl)

    def f(value):
        if value is math.nan:
            if allow_nan:
                return
            raise ValueError('value NaN is not allowed')
        if abs(value) == math.inf:
            if allow_inf:
                return
            raise ValueError(
                f'value {"+" if value > 0 else "-"}Inf is not allowed')
        if allow_ints and isinstance(value, int):
            value = float(value)
        else:
            check_type(value, float, 'value')
        vf(value)

    return f


def pattern_validator(pattern):
    """Create a function that checks a value with a pattern.

    The type of the argument for the returned |VF| can be either
    :class:`str` or :class:`bytes`. It must be the same type that
    is used for the pattern.

    The check is done by using :meth:`re.Pattern.search`.

    >>> # validator for values of type str and length 5-10
    >>> vf = pattern_validator(r'^.{5,10}$')
    >>> vf('abcde')
    >>> vf('abc')
    Traceback (most recent call last):
      ...
    ValueError: invalid value: 'abc'
    >>> vf(b'abcde')
    Traceback (most recent call last):
      ...
    TypeError: the type of 'value' must be 'str', got 'bytes'

    :param pattern: regular expression pattern (see: module :mod:`re`)
    :type pattern: bytes or str or compiled pattern
    :raises TypeError: if ``pattern`` has the wrong type
    """
    check_type(pattern, (bytes, str, re.Pattern), 'pattern')
    if not isinstance(pattern, re.Pattern):
        pattern = re.compile(pattern)
    value_type = type(pattern.pattern)

    def f(value):
        check_type(value, value_type, 'value')
        if not pattern.search(value):
            raise ValueError(f'invalid value: {value!r}')

    return f


def sequence_validator(validator):
    """Create a function that checks a sequence.

    The check is done by applying the ``validator`` to
    each item in the sequence.

    >>> vf = sequence_validator(func2validator(str.isupper))
    >>> vf('ABC')
    >>> vf('AbC')
    Traceback (most recent call last):
      ...
    ValueError: error at sequence index 1: invalid value: 'b'

    :param validator: |VF|
    :return: |VF|
    :raises TypeError: if ``validator`` is not callable
    """
    _check_validator_callable(validator)

    def f(value):
        check_type(value, Sequence, 'value')
        for i, item in enumerate(value):
            try:
                validator(item)
            except ValueError as ex:
                raise ValueError(f'error at sequence index {i}: {ex}')

    return f


def set_validator(validator):
    """Create a function that checks a set.

    The check is done by applying the ``validator`` to
    each element in the set.

    :param validator: |VF|
    :return: |VF|
    :raises TypeError: if ``validator`` is not callable
    """
    _check_validator_callable(validator)

    def f(value):
        check_type(value, Set, 'value')
        for elem in value:
            try:
                validator(elem)
            except ValueError as ex:
                raise ValueError(f'error in set: {ex}')

    return f


def mapping_validator(validator, what='values'):
    """Create a function that checks a mapping.

    The check is done by applying the ``validator`` to each key
    (if ``what='keys'``), value (if ``what='values'``) or
    (key, value)-tuple (if ``what='items'``).

    :param validator: |VF|
    :param str what: see function description
    :return: |VF|
    :raises TypeError: if ``validator`` is not callable
    """
    _check_validator_callable(validator)
    check_type(what, str, 'what')
    if what not in ('keys', 'values', 'items'):
        raise ValueError("what must be one of 'keys', 'values', 'items'")

    def f(value):
        check_type(value, Mapping, 'value')
        for key, value in value.items():
            if what == 'keys':
                try:
                    validator(key)
                except ValueError as ex:
                    raise ValueError(f'error in mapping key: {ex}')
            elif what == 'values':
                try:
                    validator(value)
                except ValueError as ex:
                    raise ValueError('error in mapping: value for key'
                                     f' {key!r}: {ex}')
            else:
                try:
                    validator((key, value))
                except ValueError as ex:
                    raise ValueError(f'error in mapping item: {ex}')

    return f


_str_object = object_validator(value_type=str)


def properties_validator(validators, mapping=False):
    """Create a function that checks the properties of an object.

    The ``validators`` argument must be a mapping from a property name
    to a |VF| or ``None`` if only the existence of a property should be
    checked. If the argument value for the returned
    |VF| is missing a property, the value is considered invalid (no
    :exc:`AttributeError` will be raised).

    If ``mapping`` is ``True`` the value must be a mapping with string keys
    that are used as properties.

    >>> validators = dict(a=func2validator(str.isupper), b=None)
    >>> vf = properties_validator(validators, True)
    >>> vf({'a': 'ABC', 'b': 1})
    >>> vf({'a': 'ABC'})
    Traceback (most recent call last):
      ...
    ValueError: missing property 'b'
    >>> vf({'a': 'abc', 'b': 1})
    Traceback (most recent call last):
      ...
    ValueError: invalid property 'a': invalid value: 'abc'

    :param dict validators: |VF| for each property
    :param bool mapping: if ``True`` the value must be a mapping
    :raises TypeError: if ``validators`` is not a mapping or keys are not
                       strings or values are not callable or ``None``
    """
    check_type(validators, Mapping, 'validators')
    mapping_validator(_str_object, 'keys')(validators)
    for validator in validators.values():
        validator is None or _check_validator_callable(validator)

    def f(value):
        for name, validator in validators.items():
            try:
                if mapping:
                    p = value[name]
                else:
                    p = getattr(value, name)
                try:
                    if validator:
                        validator(p)
                except ValueError as ex:
                    raise ValueError(f'invalid property {name!r}: {ex}')
            except (AttributeError, KeyError):
                raise ValueError(f'missing property {name!r}')

    return f


_positive_int = int_validator(min_value=0)


def length_validator(min_len=0, max_len=None):
    """Create a function that checks the length.

    The type of the checked values must support the
    :func:`len` function.

    :param int min_len: the minimum length
    :param max_len: the maximum length (``None`` means no limit)
    :type max_len: int or None
    :raises ValueError: if ``min_len`` or ``max_len`` are negative integers
                        or ``min_len`` > ``max_len``
    :raises TypeError: if ``min_len`` or ``max_len`` are not
                       of type :class:`int`
    """
    check_type(min_len, int, 'min_len')
    _positive_int(min_len)
    if max_len is not None:
        check_type(max_len, int, 'max_len')
        _positive_int(max_len)
    vf = int_validator(min_value=min_len, max_value=max_len)

    def f(value):
        try:
            vf(len(value))
        except ValueError:
            raise ValueError(
                f'length must be in [{min_len}, {max_len}], got {len(value)}')

    return f


def in_validator(container, negate=False):
    """Create a function that checks for membership.

    :param container: container object (must support the ``in`` operator)
    :param bool negate: if ``True`` the value is valid if it is  ``not in``
                        the container.
    :return: |VF|
    :raises TypeError: if ``container`` does not support the ``in`` operator
    """
    if not isinstance(container, Container):
        iter(container)

    def f(value):
        if (negate and value in container or
                not negate and value not in container):
            raise ValueError(f'invalid value: {value!r}')

    return f


def func2validator(func, err_result=False):
    """Convert a function to a |VF|.

    The returned |VF| raises a :exc:`ValueError` if ``func()`` returns
    ``err_result``.

    >>> vf = func2validator(str.isupper)
    >>> vf('A')
    >>> vf('a')
    Traceback (most recent call last):
      ...
    ValueError: invalid value: 'a'

    :param func: callable that takes a value as its only argument
    :param bool err_result: the result, that will raise the ValueError
    :return: |VF|
    """
    def f(value):
        if func(value) == err_result:
            raise ValueError(f'invalid value: {value!r}')

    return f


def chain_validator(*validators):
    """Chain some validators.

    >>> str_vf = object_validator(value_type=str)
    >>> len_vf = length_validator(min_len=5, max_len=10)
    >>> # validator for values of type str and length 5-10
    >>> vf = chain_validator(str_vf, len_vf)
    >>> vf('abcde')
    >>> vf('abc')
    Traceback (most recent call last):
      ...
    ValueError: length must in [5, 10], got 3
    >>> vf(b'abcde')
    Traceback (most recent call last):
      ...
    TypeError: value must be of type 'str', got 'bytes'

    :param validators: validator functions
    :return: |VF|
    :raises TypeError: if one of the ``validators`` is not callable
    """
    for validator in validators:
        _check_validator_callable(validator)

    def f(value):
        for validator in validators:
            validator(value)

    return f


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
        raise ValueError(f'length of string must be 13 not {len(s)}')
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
        if s[0:3] not in _BOOKLAND:
            raise ValueError(
                f'ISBN-13 must start with {" or ".join(_BOOKLAND)}')
        return is_valid_ean13(s)
    if len(s) not in (10, 13):
        raise ValueError(f'length of string must be 10 or 13 not {len(s)}')
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
