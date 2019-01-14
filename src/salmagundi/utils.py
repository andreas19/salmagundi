"""Utilities.

.. versionadded:: 0.5.0
"""

import os


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
