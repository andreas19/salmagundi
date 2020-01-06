"""Utilities.

.. versionadded:: 0.5.0
"""

import os
import sys
import string
import textwrap

__all__ = ['check_bytes_like', 'check_path_like', 'check_type', 'docopt_helper']


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


def docopt_helper(text, *, name=None, version=None, version_str=None, argv=None,
                  help=True, options_first=False, converters=None, **kwargs):
    """Helper function for `docopt <https://pypi.org/project/docopt/>`_.

    The ``name`` defaults to ``os.path.basename(sys.argv[0])``.

    If ``version`` is a :class:`tuple` it will be converted to a string
    with ``'.'.join(map(str, version))``.

    If ``version_str`` is set it will be printed if called with ``--version``.
    Else if ``version`` is set the resulting string will be
    ``name + ' ' + version``.

    Within the help message string substitution is supported with
    :ref:`template strings <python:template-strings>`. The placeholder
    identifiers ``name``, ``version`` and ``version_str`` are always available;
    more can be added with ``kwargs``.

    If the help message is indented it will be dedented so that the least
    indented lines line up with the left edge of the display.

    .. |docopt_api| replace:: docopt.docopt()
    .. _docopt_api: https://pypi.org/project/docopt/#api

    .. _ref-convs:

    The optional argument ``converters`` is a mapping with the same keys as in
    the dictionary returned by |docopt_api|_. The values are callables which
    take one argument of (an) appropriate type(s) and return a value of the
    desired type. It is not required to provide a converter for every option,
    argument and command. If a value cannot be converted the converter should
    raise a :class:`ValueError`.

    Example (naval_fate.py):

    .. literalinclude:: /_files/docopt_helper_example.py
       :language: python3

    .. literalinclude:: /_files/docopt_helper_example.txt
       :language: none
       :emphasize-lines: 26,29,30

    :param str text: help message
    :param str name: name of program/script
    :param version: version
    :type version: str or tuple
    :param str version_str: version string
    :param argv: see: |docopt_api|_
    :type argv: list(str)
    :param bool option_first: see: |docopt_api|_
    :param bool help: see: |docopt_api|_
    :param dict converters: see :ref:`above <ref-convs>`
    :param kwargs: additional values for substitution in the help message
    :return: result of |docopt_api|_
    :rtype: dict
    :raises SystemExit: if a converter function raises a :class:`ValueError`

    .. versionadded:: 0.10.0
    """
    import docopt

    if name is None:
        name = os.path.basename(sys.argv[0])
    if isinstance(version, tuple):
        version = '.'.join(map(str, version))
    if version_str is None and version:
        version_str = f'{name} {version}'
    mapping = dict(name=name, version=version, version_str=version_str)
    arguments = docopt.docopt(
        string.Template(textwrap.dedent(text)).substitute(mapping, **kwargs),
        version=version_str, argv=argv, help=help,
        options_first=options_first)
    if converters:
        for key, conv in converters.items():
            try:
                arguments[key] = conv(arguments[key])
            except ValueError as ex:
                raise SystemExit(f'error in {key!r}: {ex}')
    return arguments
