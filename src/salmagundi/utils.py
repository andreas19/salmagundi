"""Utilities.

.. versionadded:: 0.5.0
"""

import os


def check_type(obj, classinfo, name='object', alt_msg=None):
    """Check the type of an object.

    >>> utils.check_type(1, str, 'num')
    Traceback (most recent call last):
      ...
    TypeError: the type of 'num' must be 'str', got 'int'
    >>> utils.check_type(1, (str, float), 'num')
    Traceback (most recent call last):
      ...
    TypeError: the type of 'num' must be one of 'str, float', got 'int'
    >>> utils.check_type(1, str, 'num', 'wrong type for num')
    Traceback (most recent call last):
      ...
    TypeError: wrong type for num

    :param object obj: the object
    :param classinfo: see :func:`isinstance`
    :param str name: name shown in the exception message
    :param str alt_msg: alternative message
    :raises TypeError: if the check fails
    """
    if not isinstance(obj, classinfo):
        if alt_msg:
            msg = alt_msg
        elif isinstance(classinfo, tuple):
            msg = ('the type of %r must be one of %r, got %r' %
                   (name, ', '.join(map(lambda x: x.__name__, classinfo)),
                    obj.__class__.__name__))
        else:
            msg = ('the type of %r must be %r, got %r' %
                   (name, classinfo.__name__, obj.__class__.__name__))
        raise TypeError(msg)


def check_path_like(obj, name='object', alt_msg=None):
    """Check if an object is path-like.

    :param object obj: the object
    :param str name: name shown in the exception message
    :param str alt_msg: alternative message
    :raises TypeError: if the check fails
    """
    if alt_msg:
        msg = alt_msg
    else:
        msg = ('%r must be a path-like object, got %r' %
               (name, obj.__class__.__name__))
    check_type(obj, (str, bytes, os.PathLike), None, msg)
