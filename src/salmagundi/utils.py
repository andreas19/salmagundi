"""Utilities.

.. versionadded:: 0.5.0
"""

import errno
import os
import socket
import sys
import string
import tempfile
import textwrap
from contextlib import contextmanager, suppress

from ._stopwatch import StopWatch, StopWatchError

__all__ = ['AlreadyRunning', 'StopWatch', 'StopWatchError', 'check_bytes_like',
           'check_path_like', 'check_type', 'docopt_helper',
           'ensure_single_instance', 'sys_exit']


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
                  help=True, options_first=False, converters=None, err_code=1,
                  **kwargs):
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
    take one argument of an appropriate type and return a value of the
    desired type. It is not required to provide a converter for every option,
    argument and command. If a value cannot be converted the converter should
    raise a :exc:`ValueError`.

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
    :param int err_code: exit status code if an error occurs
    :param kwargs: additional values for substitution in the help message
    :return: result of |docopt_api|_
    :rtype: dict
    :raises SystemExit: if program was invoked with incorrect arguments or
                        a converter function raised a :exc:`ValueError`

    .. versionadded:: 0.10.0

    .. versionchanged:: 0.11.0
       Add parameter ``err_code``
    """
    from . import _docopt

    if name is None:
        name = os.path.basename(sys.argv[0])
    if isinstance(version, tuple):
        version = '.'.join(map(str, version))
    if version_str is None and version:
        version_str = f'{name} {version}'
    mapping = dict(name=name, version=version, version_str=version_str)
    try:
        arguments = _docopt.docopt(
            string.Template(
                textwrap.dedent(text)).substitute(mapping, **kwargs),
            version=version_str, argv=argv, help=help,
            options_first=options_first)
    except SystemExit as ex:
        sys_exit(ex, err_code)
    if converters:
        for key, conv in converters.items():
            try:
                arguments[key] = conv(arguments[key])
            except ValueError as ex:
                sys_exit(f'error in {key!r}: {ex}', err_code)
    return arguments


def sys_exit(arg=None, code=None, *, logger=None):
    """Exit from Python.

    If ``code`` is not an integer, this function calls :func:`sys.exit` with
    ``arg`` as its argument. Otherwise ``arg`` will be printed to
    :data:`sys.stderr` if it is not ``None`` and :func:`sys.exit`
    will be called with ``code`` as its argument.

    If ``logger`` is set, the message, if any, will be logged with level
    ``CRITICAL`` instead of printing it to :data:`sys.stderr`.

    :param arg: see: :func:`sys.exit`
    :param code: exit code (ignored if not an :class:`int`)
    :type code: int or None
    :param logger: a logger
    :type logger: logging.Logger
    :raises SystemExit:

    .. versionadded:: 0.11.0
    """
    if not isinstance(code, int):
        code = None
    if code is None:
        if logger and arg is not None and not isinstance(arg, int):
            logger.critical(str(arg))
            sys.exit(1)
        else:
            sys.exit(arg)
    elif arg is not None:
        if logger:
            logger.critical(str(arg))
        else:
            print(arg, file=sys.stderr)
    sys.exit(code)


class AlreadyRunning(Exception):
    """Raised by :func:`ensure_single_instance`."""


@contextmanager
def ensure_single_instance(lockname=None, *, lockdir=None,  # noqa: C901
                           extra=None, err_code=1, err_msg=None,
                           use_socket=False):
    """Make sure that only one instance of the program/script is running.

    The result of this function can be used as a context manager in `with`
    statements or as a decorator.

    .. code-block:: python

       def main():
           ...

       if __name__ == '__main__':
           with ensure_single_instance():
               main()

       # is equivalent to:

       @ensure_single_instance()
       def main():
           ...

       if __name__ == '__main__':
           main()

    If ``lockname`` is not set the name will be constructed from
    the absolute path of the program/script and the lock file will be created
    in the ``lockdir`` (which defaults to the temporary directory).

    On Linux ,if ``use_socket=True``, an abstract domain socket will be used
    instead of a lock file and the name of the socket will be the value of
    ``lockname``.

    This function should work on Windows and any platform that supports
    :mod:`fcntl` but it is only tested on Linux. The user running the
    program/script must have the permissions to create and delete the lock file.
    If the program/script will be run by multiple users the single instance
    restriction can be per user or system wide. The temporary directory on
    Windows is normally user specific; on unix-like systems it is normally one
    directory for all users. To create a user specific lock name the ``extra``
    argument can be used:


    .. code-block:: python

       import getpass
       from salmagundi.utils import ensure_single_instance

       with ensure_single_instance(extra=getpass.getuser()):
           ...

    :param str lockname: user defined lock name
    :param lockdir: user defined directory for lock files (must exist and the
                    path must be absolute; ignored if ``use_socket=True``)
    :type lockdir: :term:`path-like object`
    :param str extra: will be appended to lock name
    :param err_code: exit status code if another instance is running (if set to
                     ``None`` :exc:`AlreadyRunning` will be raised instead of
                     :exc:`SystemExit`)
    :type err_code: int or None
    :param err_msg: error message (if ``None`` it defaults to
                    ``f'already running: {sys.argv[0]}'``)
    :type err_msg: str or None
    :param bool use_socket: if true an abstract domain socket is used
                        (**Linux only**)
    :raises SystemExit: if another instance is running and ``err_code``
                        is not None
    :raises AlreadyRunning: if another instance is running and ``err_code``
                            is None
    :raises RuntimeError: if ``lockdir`` is not absolute or ``use_socket=True``
                          and platform is not Linux
    :raises OSError: if the lock file could not be created/deleted

    .. versionadded:: 0.11.0

    .. versionchanged:: 0.11.2
       Rename parameter ``lockfile`` to ``lockname``
    """
    if err_code is not None and not isinstance(err_code, int):
        err_code = 1
    if not lockname:
        lockname = os.path.abspath(
            sys.argv[0]).translate(str.maketrans(r'\/.: ', '-----')).strip('-')
    if extra:
        lockname += '-' + extra
    if use_socket:
        if not sys.platform.startswith('linux'):
            raise RuntimeError(
                'abstract domain sockets only supported on Linux')
        sock = socket.socket(socket.AF_UNIX)
        try:
            sock.bind('\0' + lockname)
            yield
        except OSError as ex:
            if ex.errno == errno.EADDRINUSE:
                _already_running(err_code, err_msg)
            raise
        finally:
            sock.close()
    else:
        if lockdir and not os.path.isabs(lockdir):
            raise RuntimeError('lockdir path must be absolute')
        if not lockdir:
            lockdir = tempfile.gettempdir()
        lockfile = os.path.join(lockdir, lockname + '.lock')
        if sys.platform == 'win32':
            try:
                os.remove(lockfile)
            except FileNotFoundError:
                pass
            except OSError as ex:
                if ex.winerror == 32:  # ERROR_SHARING_VIOLATION
                    _already_running(err_code, err_msg)
                raise
            try:
                fd = os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                try:
                    yield
                finally:
                    os.close(fd)
                    os.remove(lockfile)
            except FileExistsError:  # another process was faster
                _already_running(err_code, err_msg)
        else:
            import fcntl
            if os.path.exists(lockfile):
                flags = os.O_WRONLY
            else:
                flags = os.O_CREAT | os.O_WRONLY
            mask = os.umask(0)
            try:
                fd = os.open(lockfile, flags, 0o222)
            finally:
                os.umask(mask)
            try:
                fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                try:
                    yield
                finally:
                    fcntl.lockf(fd, fcntl.LOCK_UN)
                    os.close(fd)
                    with suppress(PermissionError):
                        os.remove(lockfile)
            except OSError as ex:
                if ex.errno in (errno.EACCES, errno.EAGAIN):
                    _already_running(err_code, err_msg)
                raise


def _already_running(err_code, err_msg):
    if err_msg is None:
        err_msg = f'already running: {sys.argv[0]}'
    if err_code is None:
        raise AlreadyRunning(err_msg) from None
    else:
        sys_exit(err_msg or None, err_code)
