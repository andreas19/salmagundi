"""File utilities.

The argument ``file`` in the functions in this module can either be a path-like
object or an integer file descriptor of a previously opened file. The argument
``encoding`` should only be used in text mode (``binary=False``) if necessary.

.. seealso:: built-in function :func:`open`
"""

import os


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

    If a predicate function is given, it must take a single line as
    its argument and return a bool. Only the lines for which ``True``
    is returned are included in the result.

    :param file: path to file or file descriptor
    :type file: path-like object or int
    :param predicate: predicate function
    :type predicate: func(line)
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


def create(file, exclusive=False, truncate=True):
    """Create a file.

    If the file exists and ``exclusive=False`` the modification
    time will be set to the current time.

    :param file: path to file or file descriptor
    :type file: path-like object or int
    :param bool exclusive: if ``True`` the file will be created in
                           exclusive mode
    :param bool truncate: if ``True`` and the file exists it will
                          be truncated
    :raises OSError: on I/O failure
    :raises FileExistsError: if ``exclusive=True`` and the file exists
    """
    mode = 'x' if exclusive else ('w' if truncate else 'a')
    with open(file, mode=mode):
        pass
    if not truncate:
        os.utime(file)


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
