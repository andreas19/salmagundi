"""Functions for terminal input.

The terminal must support `ANSI escape sequences
<https://en.wikipedia.org/wiki/ANSI_escape_code>`_.

.. versionadded:: 0.3.0
"""

import math
from functools import partial

from ansictrls import CS

from .utils import check_type

_cs_print = partial(print, end='', sep='', flush=True)


def read(prompt='', default=None, check=None, exc_on_cancel=False):
    """Read a line of input and check if it is allowed.

    If the input is not allowed the prompt will be shown again. The
    input can be cancelled with EOF (``^D``).

    If the ``check`` parameter is set to ``None`` any input is allowed,
    else it must be a ``callable`` that takes a string as a parameter
    and returns the (converted) input value or raises
    :class:`ValueError` if the input is not allowed.

    >>> read('Number: ', default='42')
    Number: 21
    '21'
    >>> read('Number: ', default='42', check=int)
    Number:
    42

    :param str prompt: the prompt
    :param default: default value that will be used if no input is provided
    :type default: str or None
    :param check: the check parameter (see above)
    :type check: callable(str) or None
    :param bool exc_on_cancel: if set to ``True`` an EOF will cause an Exception
    :return: (converted) input value or ``None`` if input was cancelled and
              ``exc_on_cancel=False``
    :rtype: str or return-type of the ``check`` callable or None
    :raises EOFError: if input was cancelled and ``exc_on_cancel=True``
    :raises TypeError: if ``default`` is not of type ``str``
    """
    default is not None and check_type(default, str, 'default')
    value = None
    _cs_print('\n', CS.CUU, CS.SCP)
    while True:
        try:
            a = input(prompt) or default
        except EOFError:
            print()
            if exc_on_cancel:
                raise
            break
        if a is not None:
            if check:
                try:
                    value = check(a)
                    break
                except ValueError:
                    pass
            else:
                value = a
                break
        _cs_print(CS.RCP, CS.ED)
    return value


def yesno(prompt, yesno, exc_on_cancel=False):
    """Show yes/no input prompt.

    If the typed character (case-insensitive) is not allowed
    (i.e. not in ``yesno``) the prompt will be shown again.
    The input can be cancelled with EOF (``^D``).

    >>> yesno('Exit program?', 'yN')
    Exit program? [yN] Y
    True

    :param str prompt: the prompt
    :param str yesno: the characters for ``yes`` (index 0) and ``no`` (index 1);
                      if one is upper and the other lower case, the upper case
                      character is the default
    :param bool exc_on_cancel: if set to ``True`` an EOF will cause an Exception
    :return: ``True`` for ``yes``, ``False`` for ``no``, ``None`` if cancelled
             and ``exc_on_cancel=False``
    :rtype: bool or None
    :raises EOFError: if input was cancelled and ``exc_on_cancel=True``
    :raises TypeError: if ``yesno`` is not of type ``str``
    :raises ValueError: if ``yesno`` is not of length 2
    """
    check_type(yesno, str, 'yesno argument')
    if len(yesno) != 2:
        raise ValueError('argument yesno must be a string of to 2 characters')
    if yesno[0].isupper() and yesno[1].islower():
        default = yesno[0]
    elif yesno[0].islower() and yesno[1].isupper():
        default = yesno[1]
    else:
        default = None

    def f(s):
        s1 = s.lower()
        s2 = yesno.lower()
        if s1 not in s2:
            raise ValueError
        return s1 == s2[0]

    return read('%s [%s%s] ' % (prompt, *yesno), default=default, check=f,
                exc_on_cancel=exc_on_cancel)


def select(prompt, options, default=None, case_sensitive=False,
           exc_on_cancel=False):
    """Show an input with selectable options.

    If the input is not allowed the prompt will be shown again. The
    input can be cancelled with EOF (``^D``).

    >>> select('Select: [T]op, [B]ottom, [L]eft, [R]ight > ', 'TBLR')
    Select: [T]op, [B]ottom, [L]eft, [R]ight > b
    1

    :param str prompt: the prompt
    :param options: the options; if all options are only 1 character a string
                    can be used, else a tuple of strings
    :type options: str or tuple
    :param default: default value that will be used if no input is provided
    :type default: str or None
    :param bool case_sensitive: if ``False`` case of typed characters will
                                be ignored
    :param bool exc_on_cancel: if set to ``True`` an EOF will cause an Exception
    :return: index of the selected option in ``options`` or None if cancelled
             and ``exc_on_cancel=False``
    :rtype: int or None
    :raises EOFError: if input was cancelled and ``exc_on_cancel=True``
    :raises TypeError: if ``options`` is not str or tuple of strings

    .. versionadded:: 0.4.0
    """
    check_type(options, (str, tuple), 'options')
    if not case_sensitive:
        options = tuple(map(str.lower, options))

    def f(s):
        if not case_sensitive:
            s = s.lower()
        if s not in options:
            raise ValueError
        return options.index(s)

    return read(prompt, default=default, check=f, exc_on_cancel=exc_on_cancel)


def menu(prompt, titles, cols=1, col_by_col=True, exc_on_cancel=False):
    """Show a simple menu.

    If the input is not allowed the prompt will be shown again. The
    input can be cancelled with EOF (``^D``).

    The caller has to take care that the menu will fit in the terminal.

    ::

        def update():
            ...

        def sort(desc=True, duration=True):
            ...

        items = (
            ('Update', update),
            ('Sort duration desc', sort),
            ('Sort duration asc', sort, False),
            ('Sort size desc', sort, True, False),
            ('Sort size asc', sort, False, False),
        )
        i = menu('> ', tuple(x[0] for x in items))
        print()
        if i is not None:
            items[i][1](*items[i][2:])

    .. raw:: html

       <pre style="color:#FFFFFF;background-color:#000000">[1] Update
       [2] Sort duration desc
       [3] Sort duration asc
       [4] Sort size desc
       [5] Sort size asc
       &gt; </pre>

    :param str prompt: the prompt
    :param tuple titles: the titles of the menu options
    :param int cols: number of columns
    :param bool col_by_col: if ``True`` the menu will be filled
                            column-by-column, otherwise row-by-row
    :param bool exc_on_cancel: if set to ``True`` an EOF will cause an Exception
    :return: index of the selected option in ``titles`` or None if cancelled
             and ``exc_on_cancel=False``
    :rtype: int or None
    :raises EOFError: if input was cancelled and ``exc_on_cancel=True``
    :raises TypeError: if ``titles`` is not a tuple

    .. versionadded:: 0.4.0
    """
    check_type(titles, tuple, 'titles')
    rows = math.ceil(len(titles) / cols)
    num_width = len(str(len(titles)))
    title_width = max(map(len, titles))
    if col_by_col:
        indices = (x + rows * y for x in range(rows) for y in range(cols))
    else:
        indices = range(len(titles))
    lines = []
    row = []
    for cnt, idx in enumerate(indices, 1):
        if idx < len(titles):
            row.append(f'[{idx + 1:{num_width}}] {titles[idx]:{title_width}}')
        if cnt % cols == 0:
            lines.append('   '.join(row))
            lines.append('\n')
            row.clear()
    if row:
        lines.append('   '.join(row))
        lines.append('\n')

    def f(s):
        i = int(s)
        if 0 < i <= len(titles):
            return i - 1
        raise ValueError

    return read(''.join(lines) + prompt, check=f, exc_on_cancel=exc_on_cancel)
