"""Functions for terminal input.

The terminal must support `ANSI escape sequences
<https://en.wikipedia.org/wiki/ANSI_escape_code>`_.

.. versionadded:: 0.3.0
"""

from ansictrls import erase, EraseMode, save_pos, move


def line(prompt='', default=None, check=None, exc_on_cancel=False):
    """Get a line of input and check if it is allowed.

    If the input is not allowed the prompt will be shown again. The
    input can be cancelled with EOF (``^D``).

    If the ``check`` parameter is set to ``None`` any input is allowed,
    else it must be a ``callable`` that takes a string as a parameter
    and returns the (converted) input value or raises
    :class:`ValueError` if the input is not allowed.

    >>> line('Number: ', default='42')
    Number: 21
    '21'
    >>> line('Number: ', default='42', check=int)
    Number:
    42

    :param str prompt: the prompt
    :param default: default value that will be used if no input is provided
    :type default: str or None
    :param check: the check parameter
    :type check: callable(str) or None
    :param bool exc_on_cancel: if set to ``True`` an EOF will cause an Exception
    :return: (converted) input value or ``None`` if input was cancelled and
              ``exc_on_cancel=False``
    :rtype: str or return-type of the ``check`` callable or None
    :raises EOFError: if input was cancelled and ``exc_on_cancel=True``
    :raises TypeError: if ``default`` is not of type ``str``

    .. versionadded:: 0.3.0
    """
    if default is not None and not isinstance(default, str):
        raise TypeError('default value %r not of type str' % default)
    value = None
    print()
    move(-1)
    while True:
        try:
            with save_pos():
                a = input(prompt) or default
        except EOFError:
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
        erase(EraseMode.SCRN_END)
    print()
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

    .. versionadded:: 0.3.0
    """
    if not isinstance(yesno, str):
        raise TypeError('yesno argument %r not of type str' % yesno)
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
            raise ValueError()
        return s1 == s2[0]

    return line('%s [%s%s] ' % (prompt, *yesno), default=default, check=f,
                exc_on_cancel=exc_on_cancel)
