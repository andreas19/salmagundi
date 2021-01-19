"""Utilities for working with strings.

.. versionadded:: 0.2.0
"""

import configparser
import math
import re
import string
import unicodedata
from collections import namedtuple
from datetime import timedelta
from functools import lru_cache

from wcwidth import wcswidth

from .utils import check_type

__all__ = ['BINARY_PREFIXES', 'BOOLEAN_STATES', 'DECIMAL_PREFIXES', 'NO_PREFIX',
           'Prefix', 'TranslationTable', 'bin_prefix', 'dec_prefix',
           'find_bin_prefix', 'find_dec_prefix', 'format_bin_prefix',
           'format_dec_prefix', 'format_timedelta', 'insert_separator',
           'int2str', 'is_hexdigit', 'parse_timedelta', 'purge', 'shorten',
           'slugify', 'split_host_port', 'str2bool', 'str2port', 'str2tuple',
           'walign', 'wlen', 'wshorten']

BOOLEAN_STATES = configparser.ConfigParser.BOOLEAN_STATES.copy()
"""Dictionary with mappings from strings to boolean values.

Used by the function :func:`str2bool`.

This dictionary can be modified. The default values are:
    * ``True``: ``'1', 'yes', 'true', 'on'``
    * ``False``: ``'0', 'no', 'false', 'off'``

These are the same as in :attr:`configparser.ConfigParser.BOOLEAN_STATES`.
"""


def str2bool(s):
    """Convert a string to a boolean value.

    The string is converted to lowercase before looked up in
    the :data:`BOOLEAN_STATES` dictionary.

    :param str s: the string
    :return: a boolean value
    :rtype: bool
    :raises ValueError: if the string is not in :data:`BOOLEAN_STATES`
    """
    try:
        return BOOLEAN_STATES[s.lower()]
    except KeyError:
        raise ValueError('not a boolean: %s' % s)


def str2tuple(s, sep=',', converter=None, *, maxsplit=-1):
    """Convert a string to a tuple.

    If ``converter`` is given and not ``None``, it must be a callable that
    takes a string parameter and returns an object of the required type,
    or else a tuple with string elements will be returned.

    >>> str2tuple('1, 2, 3,4', converter=int)
    (1, 2, 3, 4)
    >>> str2tuple('on, off, no, true, YES')
    ('on', 'off', 'no', 'true', 'YES')
    >>> str2tuple('on, off, no, true, YES', converter=str2bool)
    (True, False, False, True, True)
    >>> str2tuple('a, b, , d')
    ('a', 'b', '', 'd')

    :param str s: the string
    :param str sep: the separator (whitespace around ``sep`` will be ignored)
    :param converter: the converter function
    :type converter: callable(str)
    :param int maxsplit: max. number of splits (-1 means no limit)
    :return: tuple with elements of the required type
    :rtype: tuple

    .. versionchanged:: 0.14.0 Add parameter ``maxsplit``
    """
    if s:
        f = converter or str
        return tuple(f(x.strip()) for x in s.split(sep, maxsplit))
    return ()


def str2port(s):
    """Convert a string to a network port number.

    :param str s: the string to convert
    :return: port number
    :rtype: int
    :raises ValueError: if ``s`` cannot be converted to a number in [0..65535]

    .. versionadded:: 0.5.0
    """
    port = int(s)
    if 0 <= port <= 65535:
        return port
    raise ValueError('not a valid port number: %d' % port)


def split_host_port(s, port=None):
    """Split a string into host and port.

    >>> split_host_port('example.com:42', 21)
    ('example.com', 42)
    >>> split_host_port('example.com', 21)
    ('example.com', 21)

    :param str s: the string to split
    :param int port: port that is used if there is none in the string
    :return: host and port number
    :rtype: str, int
    :raises ValueError: if ``port`` or the port number in ``s``
                        are not in [0..65535] or neither of them is given

    .. versionadded:: 0.5.0
    """
    if port is not None and not (0 <= port <= 65535):
        raise ValueError('not a valid port number: %d' % port)
    a = s.split(':', 1)
    if len(a) == 1:
        if port is None:
            raise ValueError('no port in parameter and default port is None')
        return a[0], port
    else:
        return a[0], str2port(a[1])


def insert_separator(s, sep, group_size, reverse=False):
    """Insert separators in a string.

    >>> insert_separator('008041aefd7e', ':', 2)
    00:80:41:ae:fd:7e
    >>> insert_separator('aaabbbcccd', ':', 3)
    'aaa:bbb:ccc:d'
    >>> insert_separator('aaabbbcccd', ':', 3, True)
    'a:aab:bbc:ccd'
    >>> insert_separator('9783161484100', '-', (3, 1, 2, 6))
    '978-3-16-148410-0'

    :param str s: the string
    :param str sep: the separator character(s)
    :param group_size: the size of each group
    :type group_size: int or sequence of ints
    :param bool reverse: if ``True`` group from right to left instead from
                         left to right
    :return: string with separators
    :rtype: str
    :raises ValueError: if ``group_size < 1``

    .. versionadded:: 0.5.0
    .. versionchanged:: 0.6.0
       Add parameter ``reverse``
    .. versionchanged:: 0.9.0
       Groups can be of different sizes
    """
    if reverse:
        s = s[::-1]
    if isinstance(group_size, int):
        if group_size < 1:
            raise ValueError('group_size must be >= 1')
        r = [s[i:i + group_size] for i in range(0, len(s), group_size)]
    else:
        if not all(map(lambda x: x > 0, group_size)):
            raise ValueError('group_size must be >= 1')
        r = []
        idx = 0
        for size in group_size:
            x = s[idx:idx + size]
            if x:
                r.append(x)
            else:
                break
            idx += size
        else:
            if idx < len(s):
                r.append(s[idx:])
    if reverse:
        return sep.join(r)[::-1]
    else:
        return sep.join(r)


def purge(s, chars=None, negate=False):
    """Purge characters from a string.

    Each character in ``chars`` will be eliminated from the string.

    If ``chars=None`` or ``chars=''`` all consecutive whitespace
    are replaced by a single space.

    if ``negate=True`` all characters **not** in chars will be
    purged (only applies when ``chars`` is at least one character)

    >>> purge('00:80:41:ae:fd:7e', ':')
    008041aefd7e

    :param str s: the string
    :param str chars: the characters
    :param bool negate: see above
    :return: the purged string
    :rtype: str

    .. versionadded:: 0.5.0
    """
    if chars:
        if negate:
            return ''.join(c for c in s if c in chars)
        return ''.join(c for c in s if c not in chars)
    return re.sub(r'\s+', ' ', s)


def shorten(text, width=80, placeholder='…', pos='right'):
    """Shorten the text to fit in the given width.

    If ``len(text) <= width`` the ``text`` is returned unchanged.

    >>> text = 'Lorem ipsum dolor sit amet'
    >>> shorten(text, width=15)
    'Lorem ipsum do…'
    >>> shorten(text, width=15, placeholder=' ... ', pos='middle')
    'Lorem ...  amet'
    >>> shorten(text, width=15, pos='left')
    '…dolor sit amet'

    :param str text: the text
    :param int width: the width
    :param str placeholder: the placeholder
    :param str pos: position (``'left', 'middle', 'right'``) of
                    placeholder in text
    :return: the shortened text
    :rtype: str
    :raises ValueError: if ``width < len(placeholder)`` or ``pos`` is unknown
    """
    if width < len(placeholder):
        raise ValueError('width must be >= len(placeholder)')
    if pos not in ('left', 'right', 'middle'):
        raise ValueError('unknown pos: %s' % pos)
    if len(text) <= width:
        return text
    if pos == 'right':
        return text[:width - len(placeholder)] + placeholder
    elif pos == 'left':
        return placeholder + text[len(text) - width + len(placeholder):]
    else:
        p1 = math.ceil((width - len(placeholder)) / 2)
        p2 = width - p1 - len(placeholder)
        return text[:p1] + placeholder + (text[-p2:] if p2 else '')


Prefix = namedtuple('Prefix', 'name, symbol, factor')
Prefix.__doc__ = """\
Class for prefixes with fields ``name, symbol, factor``.

Used by the ``*_prefix()`` functions.
"""

NO_PREFIX = Prefix('', '', 1)  #: No prefix

BINARY_PREFIXES = [
    Prefix('yobi', 'Yi', 2**80),
    Prefix('zebi', 'Zi', 2**70),
    Prefix('exbi', 'Ei', 2**60),
    Prefix('pebi', 'Pi', 2**50),
    Prefix('tebi', 'Ti', 2**40),
    Prefix('gibi', 'Gi', 2**30),
    Prefix('mebi', 'Mi', 2**20),
    Prefix('kibi', 'Ki', 2**10),
    NO_PREFIX
]
r"""List with binary prefixes.

The entries in this list are of type :class:`Prefix`.

=====  ======  ======
Name   Symbol  Factor
=====  ======  ======
yobi     Yi    2\ :sup:`80`
zebi     Zi    2\ :sup:`70`
exbi     Ei    2\ :sup:`60`
pebi     Pi    2\ :sup:`50`
tebi     Ti    2\ :sup:`40`
gibi     Gi    2\ :sup:`30`
mebi     Mi    2\ :sup:`20`
kibi     Ki    2\ :sup:`10`
\               1
=====  ======  ======
"""

DECIMAL_PREFIXES = [
    Prefix('yotta', 'Y', 10**24),
    Prefix('zetta', 'Z', 10**21),
    Prefix('exa', 'E', 10**18),
    Prefix('peta', 'P', 10**15),
    Prefix('tera', 'T', 10**12),
    Prefix('giga', 'G', 10**9),
    Prefix('mega', 'M', 10**6),
    Prefix('kilo', 'k', 10**3),
    Prefix('hecto', 'h', 10**2),
    Prefix('deca', 'da', 10**1),
    NO_PREFIX,
    Prefix('deci', 'd', 10**-1),
    Prefix('centi', 'c', 10**-2),
    Prefix('milli', 'm', 10**-3),
    Prefix('micro', 'µ', 10**-6),
    Prefix('nano', 'n', 10**-9),
    Prefix('pico', 'p', 10**-12),
    Prefix('femto', 'f', 10**-15),
    Prefix('atto', 'a', 10**-18),
    Prefix('zepto', 'z', 10**-21),
    Prefix('yocto', 'y', 10**-24),
]
r"""List with decimal prefixes.

The entries in this list are of type :class:`Prefix`.

=====  ======  ======
Name   Symbol  Factor
=====  ======  ======
yotta    Y     10\ :sup:`24`
zetta    Z     10\ :sup:`21`
exa      E     10\ :sup:`18`
peta     P     10\ :sup:`15`
tera     T     10\ :sup:`12`
giga     G     10\ :sup:`9`
mega     M     10\ :sup:`6`
kilo     k     10\ :sup:`3`
hecto    h     10\ :sup:`2`
deca     da    10\ :sup:`1`
\               1
deci     d     10\ :sup:`-1`
centi    c     10\ :sup:`-2`
milli    m     10\ :sup:`-3`
micro    µ     10\ :sup:`-6`
nano     n     10\ :sup:`-9`
pico     p     10\ :sup:`-12`
femto    f     10\ :sup:`-15`
atto     a     10\ :sup:`-18`
zepto    z     10\ :sup:`-21`
yocto    y     10\ :sup:`-24`
=====  ======  ======
"""


def bin_prefix(value):
    """Get an appropriate binary prefix for an integer number.

    :param int value: the number
    :return: binary prefix
    :rtype: Prefix
    :raises TypeError: if value is not an integer
    """
    check_type(value, int, 'value')
    if value == 0:
        return NO_PREFIX
    value = abs(value)
    for p in BINARY_PREFIXES:
        if value / p.factor >= 1.0:
            return p


def find_bin_prefix(s):
    """Find binary prefix for name or symbol.

    :param str s: name (case-insensitive) or symbol (case-sensitive)
    :return: binary prefix or ``None`` if not found
    :rtype: Prefix or None
    """
    for p in BINARY_PREFIXES:
        if s.lower() == p.name or s == p.symbol:
            return p


def format_bin_prefix(num_frmt, value, prefix=None):
    """Format a number with a binary prefix.

    >>> format_bin_prefix('.3f', 1024**2+1024)
    '1.001 Mi'
    >>> format_bin_prefix('.3f', 1024**2+1024, prefix='Gi')
    '0.001 Gi'

    :param str num_frmt: number format string as used with :func:`format`
    :param int value: the number
    :param prefix: can be a binary prefix object, name, or symbol
    :type prefix: Prefix or str
    :return: the result of ``value / prefix.factor`` formatted according to
             ``num_frmt`` with a space character and ``prefix.symbol`` appended
    :rtype: str
    :raises TypeError: if value is not an integer
    """
    if prefix:
        check_type(value, int, 'value')
        if not isinstance(prefix, Prefix):
            prefix = find_bin_prefix(prefix) or NO_PREFIX
    else:
        prefix = bin_prefix(value)
    return format(value / prefix.factor, num_frmt) + ' ' + prefix.symbol


def dec_prefix(value, restricted=True):
    """Get an appropriate decimal prefix for a number.

    :param value: the number
    :type value: int or float
    :param bool restricted: if ``True`` only integer powers of 1000 are used,
                            i.e. *hecto, deca, deci, centi* are skipped
    :return: decimal prefix
    :rtype: Prefix
    :raises TypeError: if value is not of type int or float
    """
    check_type(value, (int, float), 'value')
    if value == 0:
        return NO_PREFIX
    value = abs(value)
    for p in DECIMAL_PREFIXES:
        if restricted and p.name in ('hecto', 'deca', 'deci', 'centi'):
            continue
        if value / p.factor >= 1.0:
            return p
    return p


def find_dec_prefix(s):
    """Find decimal prefix for name or symbol.

    :param str s: name (case-insensitive) or symbol (case-sensitive);
                  instead of the symbol ``µ`` the letter ``u`` can be used
    :return: decimal prefix or ``None`` if not found
    :rtype: Prefix or None
    """
    if s == 'u':
        s = 'µ'
    for p in DECIMAL_PREFIXES:
        if s.lower() == p.name or s == p.symbol:
            return p


def format_dec_prefix(num_frmt, value, prefix=None, restricted=True):
    """Format a number with a decimal prefix.

    >>> format_dec_prefix('.1f', 0.012)
    '12.0 m'
    >>> format_dec_prefix('.1f', 0.012, restricted=False)
    '1.2 c'

    :param str num_frmt: number format string as used with :func:`format`
    :param value: the number
    :type value: int or float
    :param prefix: can be a decimal prefix object, name, or symbol;
                   instead of the symbol ``µ`` the letter ``u`` can be used
    :type prefix: Prefix or str
    :param bool restricted: if ``True`` only integer powers of 1000 are used,
                            i.e. *hecto, deca, deci, centi* are skipped.
                            Ignored if ``prefix`` is set.
    :return: the result of ``value / prefix.factor`` formatted according to
             ``num_frmt`` with a space character and ``prefix.symbol`` appended
    :rtype: str
    :raises TypeError: if value is not of type int or float
    """
    if prefix:
        check_type(value, (int, float), 'value')
        if not isinstance(prefix, Prefix):
            prefix = find_dec_prefix(prefix) or NO_PREFIX
    else:
        prefix = dec_prefix(value, restricted)
    return format(value / prefix.factor, num_frmt) + ' ' + prefix.symbol


_TIMEDELTA_FRMT_RE = re.compile(
    r'%(?P<flag>[0 ]?)(?P<width>\d*)(?P<code>[DHMSs])')

_TdFmtTuple = namedtuple('TdFmtTuple', 'text, flag, width, code')


@lru_cache(maxsize=32)
def _timedelta_format(fmt_str):
    replacements = [('%X', '%02H:%02M:%02S'),
                    ('%Y', '%02H:%02M'),
                    ('%Z', '%02M:%02S')]
    for s, r in replacements:
        fmt_str = fmt_str.replace(s, r)
    lst = []
    pos = 0
    units = ('s', 'S', 'M', 'H', 'D')
    max_unit = 's'
    for m in _TIMEDELTA_FRMT_RE.finditer(fmt_str):
        if m['width'] and int(m['width']) < 1:
            raise ValueError('width must be > 0')
        lst.append(_TdFmtTuple(fmt_str[pos:m.start()], m['flag'],
                               m['width'], m['code']))
        pos = m.end()
        max_unit = units[max(units.index(max_unit), units.index(m['code']))]
    lst.append(fmt_str[pos:])
    return lst, max_unit


def format_timedelta(fmt_str, delta):
    """Format a time delta.

    The time delta is the difference between two points in time,
    e.g. a duration.

    The delta can be given in seconds as a :class:`int` or :class:`float`,
    or as a :class:`datetime.timedelta`. It must be >= 0.

    .. _ref-timedelta-format-specifiers:

    A format specifier starts with a ``'%'`` character followed by a flag
    (optional) and a number for the minimum field width (optional)
    followed by a format code.

    Supported flag:

    =======  =======
    Flag     Meaning
    =======  =======
    ``'0'``  zero-padded
    ``' '``  space-padded (default except for ``'s'``)
    =======  =======

    Supported format codes:

    =======  =======
    Code     Meaning
    =======  =======
    ``'D'``  days as a decimal number
    ``'H'``  hours as a decimal number
    ``'M'``  minutes as a decimal number
    ``'S'``  seconds as a decimal number
    ``'s'``  microseconds as a decimal number
    ``'X'``  equal to ``%02H:%02M:%02S``
    ``'Y'``  equal to ``%02H:%02M``
    ``'Z'``  equal to ``%02M:%02S``
    =======  =======

    The codes ``'X', 'Y', 'Z'`` cannot be used with flags and field widths.

    If the field width for microseconds (code ``'s'``) is less than 6 it will
    be counted from the left. So ``'%3s'`` will get milliseconds.

    >>> format_timedelta('%03H:%M:%S.%06s', 90078.012345678)
    '025:1:18.012346'
    >>> format_timedelta('%03H:%M:%S.%05s', 90078.012345678)
    '025:1:18.01235'
    >>> format_timedelta('%03H:%M:%S.%04s', 90078.012345678)
    '025:1:18.0123'
    >>> format_timedelta('%Z.%03s', 3678.0123)
    '61:18.012'
    >>> format_timedelta('%M min %S sec %3s ms', 3678.0123)
    '61 min 18 sec 12 ms'

    :param str fmt_str: the format string
    :param delta: the time delta
    :type delta: int or float or datetime.timedelta
    :return: the formatted time delta
    :rtype: str
    :raises TypeError: if the given ``delta`` is not ``int, float or timedelta``
    :raises ValueError: if the given ``delta`` is negative or ``width`` < 1
    """
    if isinstance(delta, (int, float)):
        delta = timedelta(seconds=delta)
    else:
        check_type(delta, timedelta,
                   msg='delta must be int, float or datetime.timedelta')
    if delta.total_seconds() < 0:
        raise ValueError('delta < 0')
    fmt, max_unit = _timedelta_format(fmt_str)
    args = {'s': 0, 'S': 0, 'M': 0, 'H': 0, 'D': 0}
    if max_unit == 's':
        args['s'] = ((delta.days * 86_400 + delta.seconds) *
                     1_000_000 + delta.microseconds)
    else:
        args['s'] = delta.microseconds
        delta_rest = delta.seconds
        if max_unit == 'S':
            args['S'] = delta.days * 86_400 + delta_rest
        else:
            delta_rest, args['S'] = divmod(delta_rest, 60)
            if max_unit == 'M':
                args['M'] = delta.days * 1440 + delta_rest
            else:
                delta_rest, args['M'] = divmod(delta_rest, 60)
                if max_unit == 'H':
                    args['H'] = delta.days * 24 + delta_rest
                else:
                    args['H'] = delta_rest
                    if max_unit == 'D':
                        args['D'] = delta.days
    fmt_lst = []
    for x in fmt:
        if isinstance(x, tuple):
            if x.code == 's' and max_unit != 's':
                e = (6 - int(x.width)) if x.width else 0
                v = round(float(args['s']) / 10 ** e)
                if x.flag:
                    v = f'%{x.flag}{x.width}d' % v
                s = f'{x.text}{v}'
            else:
                s = f'{x.text}%({x.code}){x.flag}{x.width}d' % args
        else:
            s = x
        fmt_lst.append(s)
    return ''.join(fmt_lst)


def parse_timedelta(string, fmt_str):
    """Parse a string as a time delta according to a format.

    The time delta is the difference between two points in time,
    e.g. a duration.

    .. note::
       The :ref:`format specifier <ref-timedelta-format-specifiers>`
       ``'%s'`` for microseconds can only be used for strings that are the
       fractional part of a second. The string ``'1'`` is ``100000 µs``;
       but ``'000001'`` is ``1 µs``.

    >>> parse_timedelta('03:21.001', '%M:%02S.%s')
    datetime.timedelta(seconds=201, microseconds=1000)
    >>> str(_)
    '0:03:21.001000'

    :param str s: the string
    :param str fmt_str: string with
                    :ref:`format specifiers <ref-timedelta-format-specifiers>`
    :return: timedelta object
    :rtype: datetime.timedelta
    :raises ValueError: if the string cannot be parsed
    """
    fmt, _ = _timedelta_format(fmt_str)
    lst = []
    for x in fmt:
        if isinstance(x, tuple):
            s = '%(text)s'
            if x.width and int(x.width) > 1:
                s += r'(?P<%(code)s>[ \d]{' + x.width + '})'
            else:
                s += r'(?P<%(code)s>\d+)'
            lst.append(s % x._asdict())
        else:
            lst.append(x)
    m = re.fullmatch(''.join(lst), string)
    if m:
        args = {'s': 0, 'S': 0, 'M': 0, 'H': 0, 'D': 0}
        for k, v in m.groupdict().items():
            if k == 's':
                s = v.lstrip()
                args[k] = round(int(s) * 10**(6 - len(s)))
            else:
                args[k] = int(v)
        return timedelta(days=args['D'], hours=args['H'], minutes=args['M'],
                         seconds=args['S'], microseconds=args['s'])
    else:
        raise ValueError('time data %r does not match format %r' %
                         (string, fmt_str))


def is_hexdigit(s):
    """Check if all characters are hexadecimal digits.

    :param str s: the string
    :return: ``True`` if all characters in the string are hexadecimal digits
             and there is at least one character
    :rtype: bool

    .. versionadded:: 0.5.0
    """
    return bool(s) and all(x in string.hexdigits for x in s)


_DIGITS = tuple(map(str, range(10))) + tuple(string.ascii_lowercase)


def int2str(n, base):
    """Convert an integer to a string.

    For ``base > 10`` lower case letters are used for digits.

    See also the built-in functions :func:`bin`, :func:`oct`, :func:`hex`.

    :param int n: the integer
    :param int base: the base (``2 <= base <= 36``)
    :return: converted integer
    :rtype: str
    :raises TypeError: if ``n`` or ``base`` are not integers
    :raises ValueError: if ``base`` is outside the allowed range

    .. versionadded:: 0.7.0
    """
    check_type(n, int, 'n')
    check_type(base, int, 'base')
    if base < 2 or base > 36:
        raise ValueError('base must be >= 2 and <= 36')
    if base == 10:
        return str(n)
    s = ''
    if not n:
        return '0'
    sign = '-' if n < 0 else ''
    n = abs(n)
    while n > 0:
        n, r = divmod(n, base)
        s = _DIGITS[r] + s
    return sign + s


_SLUGIFY_CHAR_MAP = str.maketrans({' ': '-', '\t': '-', '\n': '-', "'": '-',
                                   'ß': 'ss', 'æ': 'ae', 'œ': 'oe', 'ø': 'o',
                                   'þ': 'th', 'ð': 'd'})


def slugify(s):
    """Slugify a string.

    In the created `slug
    <https://en.wikipedia.org/wiki/Clean_URL#Slug>`_ white space
    characters are replaced by dashes (``-``) and all consecutive
    dashes but one are eliminated.

    :param str s: the string
    :return: slugified string
    :rtype: str

    .. versionadded:: 0.9.0
    """
    s = s.lower().translate(_SLUGIFY_CHAR_MAP)
    s = unicodedata.normalize('NFD', s)
    s = re.sub(b'[^a-zA-Z0-9-]', b'', s.encode()).decode()
    s = re.sub('-+', '-', s).strip('-')
    return s


class TranslationTable:
    """TranslationTable class.

    This class is for use with :meth:`str.translate`. If a character is not
    in ``mapped_chars``, ``unmapped_chars``, or ``delete_chars``
    a :exc:`ValueError` will be raised. See also: :meth:`str.maketrans`.

    :param mapped_chars: mapping from character to replacement string
    :type mapped_chars: dict(str, str)
    :param str unmapped_chars: string with characters that will not be replaced
    :param str delete_chars: string with characters that will be deleted
    :return: the resulting string
    :rtype: str
    :raises ValueError: if a character is not allowed

    .. versionadded:: 0.9.0
    """

    def __init__(self, mapped_chars, unmapped_chars='', delete_chars=''):
        self._mapped_chars = {ord(k): v for k, v in mapped_chars.items()}
        self._unmapped_chars = [ord(ch) for ch in unmapped_chars]
        self._delete_chars = [ord(ch) for ch in delete_chars]

    def __getitem__(self, n):
        if n in self._mapped_chars:
            return self._mapped_chars[n]
        if n in self._unmapped_chars:
            raise LookupError
        if n in self._delete_chars:
            return None
        raise ValueError('character "%s" (%d) is not allowed' % (chr(n), n))


def wlen(text):
    r"""Determine the number of columns a string actually occupies in a terminal.

    Though most characters need just one column there are characters that use
    zero (e.g. NULL) or two (e.g. Japanese) columns. The :func:`len` function
    counts the number of characters in a string.

    Examples::

        >>> s1 = 'a\0b'
        >>> s2 = 'は日本'
        >>> len(s1)
        3
        >>> len(s2)
        3
        >>> print(s1)
        ab
        >>> print(s2)
        は日本
        >>> wlen(s1)
        2
        >>> wlen(s2)
        6

    :param str text: the string
    :return: number of columns
    :rtype: int
    :raises ValueError: if length could not be determined

    .. versionadded:: 0.15.0
    """
    w = wcswidth(text)
    if w == -1:
        raise ValueError('length could not be determined')
    return w


def walign(text, width, fill=' ', align='center'):
    """Align a string even if not all characters occupy only one column\
    in a terminal.

    The string methods :meth:`~str.center`, :meth:`~str.ljust`,
    and :meth:`~str.rjust` only consider the number of characters when
    aligning a string. If a string contains characters that occupy
    zero or two columns (see :func:`wlen`) the result is wrong when
    displayed in a terminal::

       s = 'abcde'
       w = 'は日本競馬'
       wlen(s) -> 5
       wlen(w) -> 10
       s.center(12, '.') -> 12 columns (correct)
       w.center(12, '.') -> 17 columns (wrong)
       walign(s, 12, '.', 'center') -> 12 columns (correct)
       walign(w, 12, '.', 'center') -> 12 columns (correct)

    :param str text: the string
    :param int width: number of columns wherein to align the string
    :param str fill: fill character
    :param str align: alignment (one of ``'center', 'left', 'right``)
    :return: aligned string (if ``wlen(text) >= width`` the original
             string is returned)
    :raises ValueError: if length could not be determined,
                        ``align`` is unknown or ``wlen(fill) != 1``

    .. versionadded:: 0.15.0
    """
    if wcswidth(fill) != 1:
        raise ValueError('wlen(fill) must be 1')
    if align not in ('center', 'left', 'right'):
        raise ValueError(f'unknown alignment {align!r}')
    w = wlen(text)
    if w >= width:
        return text
    d = width - w
    if align == 'center':
        return d // 2 * fill + text + (width - w - d // 2) * fill
    if align == 'left':
        return text + (width - w) * fill
    if align == 'right':
        return (width - w) * fill + text


def wshorten(text, width=80, placeholder='…', pos='right'):
    """Shorten the text to fit in the given width even if not all characters\
    occupy only one column in a terminal.

    :param str text: the text
    :param int width: the width
    :param str placeholder: the placeholder
    :param str pos: position (``'left', 'middle', 'right'``) of
                    placeholder in text
    :return: the shortened text (may be one character less then ``width``)
    :rtype: str
    :raises ValueError: if length could not be determined,
                        ``width < wlen(placeholder)`` or ``pos`` is unknown

    .. versionadded:: 0.15.0
    """
    w = wlen(placeholder)
    if width < w:
        raise ValueError('width must be >= wlen(placeholder)')
    if pos not in ('left', 'right', 'middle'):
        raise ValueError(f'unknown pos: {pos}')
    if wlen(text) <= width:
        return text
    if pos == 'right':
        result = _slice(text, width - w) + placeholder
    elif pos == 'left':
        result = placeholder + _slice(text, -width + w)
    else:
        result = _slice(text, math.ceil((width - w) / 2)) + placeholder
        result += _slice(text, -width + wlen(result))
    return result


def _slice(string, length):
    if not length:
        return ''
    if abs(length) >= wlen(string):
        return string
    if length < 0:
        s = list(reversed(string))
        l = abs(length)
    else:
        s = string
        l = length
    for i, _ in enumerate(s, 1):
        if wlen(s[:i]) > l:
            result = s[:i - 1]
            break
        elif wlen(s[:i]) == l:
            result = s[:i]
            break
    if length < 0:
        return ''.join(reversed(result))
    return result
