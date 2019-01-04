"""File utilities.

The argument ``file`` in the functions in this module can either be a path-like
object or an integer file descriptor of a previously opened file. The argument
``encoding`` should only be used in text mode (``binary=False``) if necessary.

.. seealso::
   - built-in function :func:`open`
   - `path-like object <https://docs.python.org/3/glossary.html#term-path-like-object>`_
"""  # noqa: E501

import datetime
import os
import time


def read_all(file, binary=False, encoding=None):
    """Read and return the content of the file.

    :param file: path to file or file descriptor
    :type file: path-like object or int
    :param bool binary: if ``True`` the content will be returned as ``bytes``
                        else as ``str``
    :param str encoding: name of the encoding
    :return: the file content
    :rtype: bytes or str
    :raises OSError: on I/O failure
    """
    mode = 'rb' if binary else 'rt'
    with open(file, mode=mode, encoding=encoding) as fh:
        return fh.read()


def read_lines(file, predicate=None, encoding=None):
    """Read and return the content of the file as a list of lines.

    Line breaks are not included in the resulting list.

    If ``predicate`` is given, it must be a callable that takes a single
    line as its argument and returns a bool. Only the lines for which
    ``True`` is returned are included in the result.

    :param file: path to file or file descriptor
    :type file: path-like object or int
    :param predicate: predicate function
    :type predicate: callable(str)
    :param str encoding: name of the encoding
    :return: list of lines
    :rtype: list(str)
    :raises OSError: on I/O failure
    """
    result = []
    with open(file, encoding=encoding) as fh:
        for line in fh:
            line = line.strip()
            if not predicate or predicate(line):
                result.append(line)
    return result


def write_all(file, content, binary=False, encoding=None):
    """Write the content to a file.

    :param file: path to file or file descriptor
    :type file: path-like object or int
    :param content: file content
    :type content: bytes or str
    :param bool binary: if ``True`` the content must be ``bytes`` else ``str``
    :param str encoding: name of the encoding
    :return: number of bytes or characters written
    :rtype: int
    :raises OSError: on I/O failure
    """
    mode = 'wb' if binary else 'wt'
    with open(file, mode=mode, encoding=encoding) as fh:
        return fh.write(content)


def write_lines(file, lines, encoding=None):
    """Write the lines to a file.

    :param file: path to file or file descriptor
    :type file: path-like object or int
    :param list(str) lines: list of strings w/o newline
    :param str encoding: name of the encoding
    :return: number of characters written
    :rtype: int
    :raises OSError: on I/O failure
    """
    with open(file, 'w', encoding=encoding) as fh:
        cnt = fh.write('\n'.join(lines))
        cnt += fh.write('\n')
        return cnt


def append_all(file, content, binary=False, encoding=None):
    """Append the content to a file.

    :param file: path to file or file descriptor
    :type file: path-like object or int
    :param content: file content
    :type content: bytes or str
    :param bool binary: if ``True`` the content must be ``bytes`` else ``str``
    :param str encoding: name of the encoding
    :return: number of bytes or characters written
    :rtype: int
    :raises OSError: on I/O failure
    """
    mode = 'ab' if binary else 'at'
    with open(file, mode=mode, encoding=encoding) as fh:
        return fh.write(content)


def append_lines(file, lines, encoding=None):
    """Append the lines to a file.

    :param file: path to file or file descriptor
    :type file: path-like object or int
    :param list(str) lines: list of strings w/o newline
    :param str encoding: name of the encoding
    :return: number of characters written
    :rtype: int
    :raises OSError: on I/O failure
    """
    with open(file, 'a', encoding=encoding) as fh:
        cnt = fh.write('\n'.join(lines))
        cnt += fh.write('\n')
        return cnt


def touch(filepath, new_time=None, atime=True, mtime=True, create=True):
    """Change file timestamps.

    The ``new_time`` parameter may be:

    ====================  ===
    ``None``              the current time will be used
    ``datetime``          from module :mod:`datetime`
    ``struct_time``       from module :mod:`time`
    ``path-like object``  path to a file which timestamps should be used
    ====================  ===

    :param filepath: the file for which the timestamps should be changed
    :type filepath: path-like object
    :param new_time: the new time (see above for more details)
    :param bool atime: if ``True`` change access time
    :param bool mtime: if ``True`` change modification time
    :param bool create: if ``True`` an empty file will be created if it
                        does not exist
    :raises FileNotFoundError: if file does not exist and ``create=False`` or
                               the reference file for ``new_time``
                               does not exist
    :raises TypeError: if ``new_time`` is of wrong type

    .. versionadded:: 0.5.0
    """
    if not os.path.exists(filepath) and create:
        with open(filepath, 'w'):
            pass
    file_atime = os.path.getatime(filepath)
    file_mtime = os.path.getmtime(filepath)
    if new_time is None:
        atime_s = mtime_s = time.time()
    elif isinstance(new_time, datetime.datetime):
        atime_s = mtime_s = new_time.timestamp()
    elif isinstance(new_time, time.struct_time):
        atime_s = mtime_s = time.mktime(new_time)
    elif isinstance(new_time, (str, bytes, os.PathLike)):
        atime_s = os.path.getatime(new_time)
        mtime_s = os.path.getmtime(new_time)
    else:
        raise TypeError('wrong type for argument new_time')
    os.utime(filepath, (atime_s if atime else file_atime,
                        mtime_s if mtime else file_mtime))


def on_same_dev(file1, file2):
    """Return ``True`` if both files are on the same device/partition.

    ``file1, file2`` may also refer to directories.

    :param file1: path to file or file descriptor
    :type file1: path-like object or int
    :param file2: path to file or file descriptor
    :type file2: path-like object or int
    :return: ``True`` if both files are on the same device/partition,
             ``False`` otherwise
    :rtype: bool
    """
    stat1 = os.stat(file1)
    stat2 = os.stat(file2)
    return stat1.st_dev == stat2.st_dev
