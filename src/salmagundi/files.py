"""File utilities.

If a file descriptor is given for the parameter ``file`` it will be closed
after reading from/writing to the file.

For a list of supported encodings see `Standard Encodings in module codec
<https://docs.python.org/3/library/codecs.html#standard-encodings>`_.
The default encoding is platform dependant.

For a list of error handlers see `Error Handlers in module codec
<https://docs.python.org/3/library/codecs.html#error-handlers>`_.
The default error handler is ``'strict'``.
"""

import datetime
import os
import time


def read_all(file, binary=False, encoding=None, errors=None):
    """Read and return the content of the file.

    :param file: path to file or file descriptor
    :type file: :term:`path-like object` or int
    :param bool binary: if ``True`` the content will be returned as ``bytes``
                        else as ``str``
    :param str encoding: name of the encoding (ignored if ``binary=True``)
    :param str errors: error handler (ignored if ``binary=True``)
    :return: the file content
    :rtype: bytes or str
    :raises OSError: on I/O failure

    .. versionchanged:: 0.6.0
       Add parameter ``errors``
    """
    mode, encoding, errors = (('rb', None, None) if binary
                              else ('rt', encoding, errors))
    with open(file, mode=mode, encoding=encoding, errors=errors) as fh:
        return fh.read()


def read_lines(file, predicate=None, encoding=None, errors=None):
    """Read and return the content of the file as a list of lines.

    Line breaks are not included in the resulting list.

    If ``predicate`` is given, it must be a callable that takes a single
    line as its argument and returns a bool. Only the lines for which
    ``True`` is returned are included in the result.

    :param file: path to file or file descriptor
    :type file: :term:`path-like object` or int
    :param predicate: predicate function
    :type predicate: callable(str)
    :param str encoding: name of the encoding
    :param str errors: error handler
    :return: list of lines
    :rtype: list(str)
    :raises OSError: on I/O failure

    .. versionchanged:: 0.6.0
       Add parameter ``errors``
    """
    result = []
    with open(file, encoding=encoding, errors=errors) as fh:
        for line in fh:
            line = line.strip()
            if not predicate or predicate(line):
                result.append(line)
    return result


def write_all(file, content, binary=False, encoding=None, errors=None):
    """Write the content to a file.

    :param file: path to file or file descriptor
    :type file: :term:`path-like object` or int
    :param content: file content
    :type content: bytes or str
    :param bool binary: if ``True`` the content must be ``bytes`` else ``str``
    :param str encoding: name of the encoding (ignored if ``binary=True``)
    :param str errors: error handler (ignored if ``binary=True``)
    :return: number of bytes or characters written
    :rtype: int
    :raises OSError: on I/O failure

    .. versionchanged:: 0.6.0
       Add parameter ``errors``
    """
    mode, encoding, errors = (('wb', None, None) if binary
                              else ('wt', encoding, errors))
    with open(file, mode=mode, encoding=encoding, errors=errors) as fh:
        return fh.write(content)


def write_lines(file, lines, encoding=None, errors=None):
    """Write the lines to a file.

    :param file: path to file or file descriptor
    :type file: :term:`path-like object` or int
    :param list(str) lines: list of strings w/o newline
    :param str encoding: name of the encoding
    :param str errors: error handler
    :return: number of characters written
    :rtype: int
    :raises OSError: on I/O failure

    .. versionchanged:: 0.6.0
       Add parameter ``errors``
    """
    with open(file, 'w', encoding=encoding, errors=errors) as fh:
        cnt = fh.write('\n'.join(lines))
        cnt += fh.write('\n')
        return cnt


def append_all(file, content, binary=False, encoding=None, errors=None):
    """Append the content to a file.

    :param file: path to file or file descriptor
    :type file: :term:`path-like object` or int
    :param content: file content
    :type content: bytes or str
    :param bool binary: if ``True`` the content must be ``bytes`` else ``str``
    :param str encoding: name of the encoding (ignored if ``binary=True``)
    :param str errors: error handler (ignored if ``binary=True``)
    :return: number of bytes or characters written
    :rtype: int
    :raises OSError: on I/O failure

    .. versionchanged:: 0.6.0
       Add parameter ``errors``
    """
    mode, encoding, errors = (('ab', None, None) if binary
                              else ('at', encoding, errors))
    with open(file, mode=mode, encoding=encoding, errors=errors) as fh:
        return fh.write(content)


def append_lines(file, lines, encoding=None, errors=None):
    """Append the lines to a file.

    :param file: path to file or file descriptor
    :type file: :term:`path-like object` or int
    :param list(str) lines: list of strings w/o newline
    :param str encoding: name of the encoding
    :param str errors: error handler
    :return: number of characters written
    :rtype: int
    :raises OSError: on I/O failure

    .. versionchanged:: 0.6.0
       Add parameter ``errors``
    """
    with open(file, 'a', encoding=encoding, errors=errors) as fh:
        cnt = fh.write('\n'.join(lines))
        cnt += fh.write('\n')
        return cnt


def touch(filepath, new_time=None, atime=True, mtime=True, create=True):
    """Change file timestamps.

    The ``new_time`` parameter may be:

    ====================  ===
    ``None``              the current time will be used
    ``int`` or ``float``  seconds since the epoch
    ``datetime``          from module :mod:`datetime`
    ``struct_time``       from module :mod:`time`
    ``path-like object``  path to a file which timestamps should be used
    ====================  ===

    :param filepath: the file for which the timestamps should be changed
    :type filepath: :term:`path-like object`
    :param new_time: the new time (see above for more details)
    :param bool atime: if ``True`` change access time
    :param bool mtime: if ``True`` change modification time
    :param bool create: if ``True`` an empty file will be created if it
                        does not exist
    :raises FileNotFoundError: if ``filepath`` does not exist and
                               ``create=False`` or the reference
                               file for ``new_time`` does not exist
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
    elif isinstance(new_time, (int, float)):
        atime_s = mtime_s = new_time
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
    :type file1: :term:`path-like object` or int
    :param file2: path to file or file descriptor
    :type file2: :term:`path-like object` or int
    :return: ``True`` if both files are on the same device/partition
    :rtype: bool
    """
    stat1 = os.stat(file1)
    stat2 = os.stat(file2)
    return stat1.st_dev == stat2.st_dev


_COPY_CHUNK_SIZE = 16 * 1024


def copyfile(src, dst, callback, cancel_evt):
    r"""Copy a file.

    The progess of a long running copy process can be monitored
    and the process can be cancelled.

    The ``callback`` must be a callable that takes two parameters:

    - number of the copied bytes
    - size of the source file

    ::

        def cb(i, t):
            print('\r%d / %d (%.1f%%)' % (i, t, i / t * 100),
                  end='', flush=True)

        evt = threading.Event()
        print('Start', end='', flush=True)
        try:
            copyfile('/path/to/source/file',
                     '/path/to/destination/file',
                     cb, evt)
            print()
        except KeyboardInterrupt:
            evt.set()
            print('\rAbbruch                           \n')


    :param src: source filepath
    :type src: :term:`path-like object`
    :param dst: destination filepath (not a directory)
    :type dst: :term:`path-like object`
    :param callback: callback function
    :param threading.Event cancel_evt: if set the process will be cancelled
    :raises OSError: if the file could not be copied

    .. versionadded:: 0.5.0
    """
    file_size = os.path.getsize(src)
    copied = 0
    with open(src, 'rb') as ifh, open(dst, 'wb') as ofh:
        while True:
            cnt = ofh.write(ifh.read(_COPY_CHUNK_SIZE))
            if not cnt:
                break
            copied += cnt
            if callback:
                callback(copied, file_size)
            if cancel_evt and cancel_evt.is_set():
                break
