"""Easy and simple configuration.

.. versionadded:: 0.7.0

.. versionchanged:: 0.7.1
   Add tags ``:empty:`` and ``:none:`` to specification

.. _ref-spec:

This module uses a specification when reading a configuration file with a
:class:`ConfigParser` (see module :mod:`configparser` for more information).
Option values will be converted with the specified converter function, it will
be checked whether an option is required or not, default values can be given
for options that are not present in the configuration, and it can be specified
if an option is readonly or not. All this is done by calling :func:`configure`
which returns a :class:`Config` object.

If ``create_properties=True`` in :func:`configure` the name of each property
will be a concatenation of the section name and the option name with an
underscore (``_``) in between. The resulting string must be a valid Python
identifier. If ``create_properties=False`` this restriction does not apply.

The specification itself uses an INI-style configuration in which the
sections and options are described. The separator character, the default
access mode (readonly or not), and the tags which are used in the
specification for each option can be modified in a special section
``[_configspec_]``. The defaults are::

   [_configspec_]
   readonly: yes
   separator: ;
   novalue: :novalue:
   empty: :empty:
   none: :none:
   req_tag: :req:
   ro_tag: :ro:
   rw_tag: :rw:
   raw_tag: :raw:

A specification for an option looks like this::

   opt = conv | :novalue:[; dflt | :req:][; :rw: | :ro:][; :raw:]

The converter ``conv`` must be the name of a callable that takes a string
argument and returns an object of the desired type. The default converters are:
``int``, ``float``, ``str``, and ``bool``. The first three are just the
built-in functions with the same name. For what strings ``bool`` considers
``True`` or ``False`` see: :data:`~salmagundi.strings.BOOLEAN_STATES`.
These converters can be overwritten or more can be added by using a dictionary
where each key is a converter name and each value is a converter callable.
This dictionary must be passed to :func:`configure` as the ``converters``
argument.

The default value ``dflt`` and the required tag ``:req:`` are mutually
exclusive. If an option is not found in the configuration and there is no
default value for it, the option will be set to the value :data:`NOTFOUND`.
An empty string as a default value can be specified by omitting the value
or with the ``:empty:`` tag to make it more obvious: ``opt: str; :empty:``
means the same as ``opt: str;`` (because of the semicolon after the
converter *str*). For ``None`` as a default value the ``:none:`` tag must
be used.

With the readwrite tag ``:rw:`` and the readonly tag ``:ro:`` exceptions
to the global access mode (see above) can be set for each option.

The raw tag ``:raw:`` indicates that for the option value no interpolation
expansion should be done (see: :meth:`configparser.ConfigParser.get`).

For configurations that allow options without values the ``allow_no_value``
parameter for :func:`configure` must be set to ``True`` (this is one of
the keyword arguments that is passed directly the :class:`ConfigParser`
constructor). For such an option the tag ``:novalue:`` must be used instead
of the name of a converter. If the option is present in the configuration
it will be set to the value :data:`NOVALUE`.

If ``spec=None`` no conversion will be done and all options are writeable.

Example:

.. code-block:: ini

   # spec.ini
   [sec]
   greeting: str; Hello %s!; :raw:
   answer: int; :req:
   string: upper
   bar: str; :rw:

   # conf.ini
   [sec]
   answer: 42
   string: abc

>>> convs = {'upper': str.upper}
>>> conf = cfg.configure('conf.ini', 'spec.ini', converters=convs)
>>> conf['sec','greeting']
'Hello %s!'
>>> conf.sec_answer
42
>>> conf.sec_string
'ABC'
>>> ('sec', 'foo') in conf
False
>>> ('sec', 'bar') in conf
True
>>> conf['sec', 'bar']
<NOTFOUND>
>>> conf['sec', 'bar'] = 'quux'
>>> conf['sec', 'bar']
'quux'
>>> conf.sec_string = 'XYZ'
Traceback (most recent call last):
  ...
AttributeError: can't set attribute


.. class:: Config

   Configuration class.

   An instance of this class is returned by the function :func:`configure`.

   If ``create_properties=True`` it will have a property for each configuration
   option named as explained :ref:`above <ref-spec>`. For extra data this is
   just the name given in the :meth:`add` method.

   Options can also be accessed like this: ``config[sec_name, opt_name]``.
   To check if an option exists, the ``in`` operator can be used:
   ``(sec_name, opt_name) in config``.

   For extra data either ``None`` must be used for the section name or only
   the name of the data, i.e. ``config[None, name]`` and ``config[name]`` are
   equivalent as are ``(None, name) in config`` and ``name in config``.

   When a :class:`Config` object is used as an iterator it yields 3-tuples
   for each option: ``(sec_name, opt_name, value)``.

   .. method:: add(name, value, readonly=True)

      Add extra data to configuration object.

      :param str name: the name of the extra data
      :param value: the value of the data
      :param bool readonly: if ``True`` the data cannot be changed
      :raises AttributeError: if an attribute with the same name already exists
      :raises ConfigError: if ``create_properties=True`` and ``name`` is not a
                           valid Python identifier; the data can still be
                           accessed with ``cfg[name]``

   .. method:: sections

      Return section names.

      :return: list with section names
      :rtype: list

   .. method:: options(section)

      Return option names in the specified section.

      :param str section: a section name
      :return: list with option names
      :rtype: list

   .. method:: extras

      Return names of extra data added with :meth:`add`.

      :return: list with names of extra data
      :rtype: list

   .. method:: write(file, space_around_delimiters=True)

      Write a representation of the configuration to the specified file.

      Extra data added with :meth:`add` will be excluded.

      :param file: the file
      :type file: :term:`path-like object` or :term:`text file`
                  opened for writing
      :param bool space_around_delimiters: if ``True``, delimiters between keys
                                           and values are surrounded by spaces

   .. method:: debug_info

      Return an iterator that yields 5-tuples
      ``(sec, opt, name, value, readonly)`` for each option.
"""

import types
from collections import namedtuple
from configparser import ConfigParser

from .strings import str2bool, str2tuple
from .utils import check_path_like

_NAME = '_configspec_'
_CONVERTERS = {'str': str, 'int': int, 'float': float, 'bool': str2bool}

NOVALUE = type('NoValue', (), {'__repr__': lambda x: '<NOVALUE>'})()
"""Special value for options without a value (see above).

The truth value is ``True``.
"""

NOTFOUND = type('NotFound', (), {'__repr__': lambda x: '<NOTFOUND>',
                                 '__bool__': lambda x: False})()
"""Special value for options that are not found and have no default.

The truth value is ``False``.
"""

_OptSpec = namedtuple('OptSpec', 'name, converter, conv_name,'
                      'required, readonly, raw, default')
_OptData = namedtuple('OptData', 'name, ro, value')


class Error(Exception):
    """Base Exception."""


class ConfigError(Error):
    """Raised if there is a problem with the configuration."""


class SpecError(Error):
    """Raised if there is a problem with the specification."""


class ReadonlyError(Error):
    """Raised on an attempt to set a readonly option."""


def _get_name(sec, opt, create_properties):
    if create_properties:
        name = '%s_%s' % (sec, opt)
        if not name.isidentifier():
            raise SpecError('not a valid name: %s' % name)
    else:
        name = None
    return name


def _spec(spec, create_properties, convs):
    converters = _CONVERTERS.copy()
    converters.update(convs)
    cp = ConfigParser(interpolation=None)
    try:
        check_path_like(spec)
        with open(spec) as fh:
            cp.read_file(fh)
    except TypeError:
        cp.read_file(spec)
    readonly = cp.getboolean(_NAME, 'readonly', fallback=True)
    separator = cp.get(_NAME, 'separator', fallback=';')
    noval_tag = cp.get(_NAME, 'novalue', fallback=':novalue:')
    empty_tag = cp.get(_NAME, 'empty', fallback=':empty:')
    none_tag = cp.get(_NAME, 'none', fallback=':none:')
    req_tag = cp.get(_NAME, 'req_tag', fallback=':req:')
    ro_tag = cp.get(_NAME, 'ro_tag', fallback=':ro:')
    rw_tag = cp.get(_NAME, 'rw_tag', fallback=':rw:')
    raw_tag = cp.get(_NAME, 'raw_tag', fallback=':raw:')
    cp.remove_section(_NAME)
    converters[noval_tag] = None
    spec = {}
    for sec in cp.sections():
        spec[sec] = {}
        for opt in cp.options(sec):
            t = str2tuple(cp.get(sec, opt), sep=separator)
            if not t[0]:
                raise SpecError('missing spec for option %r in section %r' %
                                (opt, sec))
            name = _get_name(sec, opt, create_properties)
            try:
                converter = converters[t[0]]
            except KeyError:
                raise SpecError('unknown converter for option %r in '
                                'section %r: %s' % (opt, sec, t[0]))
            req = req_tag in t
            ro = ro_tag in t
            rw = rw_tag in t
            if ro and rw:
                raise SpecError('option %r in section %r has '
                                'a %r tag and a %r tag (only one allowed)' %
                                (opt, sec, ro_tag, rw_tag))
            raw = raw_tag in t
            for s in t[1:]:
                if s not in (req_tag, ro_tag, rw_tag, raw_tag):
                    if req:
                        raise SpecError('option %r in section %r has '
                                        'a default value and a %r tag '
                                        '(only one allowed)' %
                                        (opt, sec, req_tag))
                    if s == empty_tag:
                        s = ''
                    try:
                        if converter is None:
                            raise SpecError('no default value allowed for '
                                            '%r for option %r in section %r' %
                                            (t[0], opt, sec))
                        if s == none_tag:
                            default = None
                        else:
                            default = converter(s)
                    except Exception as ex:
                        raise SpecError('error converting default value %r '
                                        'for option %r in section %r with '
                                        'converter %r: %s' %
                                        (s, opt, sec, t[0], ex))
                    break
            else:
                default = NOTFOUND
            spec[sec][opt] = _OptSpec(name, converter, t[0], req,
                                      ro or (readonly and not rw),
                                      raw, default)
    return spec


def _key(key):
    if isinstance(key, str):
        key = (None, key)
    return key


class _BaseConfig:
    def __init__(self, options, create_props, kwargs):
        self._options = {k: (v.name, v.ro) for k, v in options.items()}
        self._values = {k: v.value for k, v in options.items()}
        self._create_props = create_props
        self._kwargs = kwargs

    def __iter__(self):
        return ((sec, opt, self._values[sec, opt])
                for (sec, opt) in self._options)

    def __contains__(self, item):
        return _key(item) in self._options

    def __getitem__(self, key):
        return self._values[_key(key)]

    def __setitem__(self, key, value):
        key = _key(key)
        if self._options[key][1]:
            raise ReadonlyError('cannot set option %r in section %r' %
                                (key[1], key[0]))
        self._values[key] = value

    def __delitem__(self, key):
        key = _key(key)
        name = self._options[key][0]
        del self._options[key]
        del self._values[key]
        if hasattr(self.__class__, name):
            delattr(self.__class__, name)

    def add(self, name, value, readonly=True):
        key = (None, name)
        self._options[key] = (name if self._create_props else None, readonly)
        self._values[key] = value
        if self._create_props:
            if not name.isidentifier():
                raise ConfigError('not a valid name: %s' % name)
            if hasattr(self.__class__, name):
                raise AttributeError('attribute %r already exists' % name)
            setattr(self.__class__, name, property(_getter(key),
                    None if readonly else _setter(key), _deleter(key)))

    def sections(self):
        lst = []
        seen = set()
        for sec, _ in self._options:
            if sec is None:
                continue
            if sec not in seen:
                lst.append(sec)
                seen.add(sec)
        return lst

    def options(self, sec):
        return list(opt for (s, opt) in self._options
                    if s == sec and sec is not None)

    def extras(self):
        return list(opt for (sec, opt) in self._options if sec is None)

    def write(self, file, space_around_delimiters=True):
        d = {}
        for (sec, opt) in self._options:
            if sec is None:
                continue
            if sec not in d:
                d[sec] = {}
            value = self._values[sec, opt]
            if value is NOVALUE:
                d[sec][opt] = None
            elif value is not NOTFOUND:
                d[sec][opt] = str(value)
        self._kwargs['interpolation'] = None
        cp = ConfigParser(**self._kwargs)
        cp.read_dict(d)
        try:
            check_path_like(file)
            with open(file, 'w') as fh:
                cp.write(fh, space_around_delimiters=space_around_delimiters)
        except TypeError:
            cp.write(file, space_around_delimiters=space_around_delimiters)

    def debug_info(self):
        for key, (name, readonly) in self._options.items():
            yield (*key, name, self._values[key], readonly)


def _getter(key):
    def f(self):
        return self._values[key]
    return f


def _setter(key):
    def f(self, value):
        self._values[key] = value
    return f


def _deleter(key):
    def f(self):
        del self[key]
    return f


def _with_spec(cp, opt_specs, kwargs):
    options = {}
    for sec, opt in [(sec, opt) for sec in opt_specs for opt in opt_specs[sec]]:
        opt_spec = opt_specs[sec][opt]
        has_option = cp.has_option(sec, opt)
        if opt_spec.required and not has_option:
            raise ConfigError('missing required option %r in section %r' %
                              (opt, sec))
        if has_option:
            value = cp.get(sec, opt, raw=opt_spec.raw)
            if value is None and kwargs.get('allow_no_value', False):
                value = NOVALUE
            else:
                try:
                    value = opt_spec.converter(value)
                except Exception as ex:
                    raise ConfigError('error converting value %r '
                                      'for option %r in section %r with '
                                      'converter %r: %s' %
                                      (value, opt, sec, opt_spec.conv_name, ex))
        else:
            value = opt_spec.default
        options[(sec, opt)] = _OptData(opt_spec.name, opt_spec.readonly, value)
    return options


def _without_spec(cp, create_properties, kwargs):
    options = {}
    for sec, opt in [(sec, opt)
                     for sec in cp.sections()
                     for opt in cp.options(sec)]:
        name = _get_name(sec, opt, create_properties)
        value = cp.get(sec, opt)
        if value is None and kwargs.get('allow_no_value', False):
            value = NOVALUE
        options[(sec, opt)] = _OptData(name, False, value)
    return options


def configure(conf, spec, *, create_properties=True, converters=None, **kwargs):
    """For an explanation see :ref:`above <ref-spec>`.

    :param conf: the configuration
    :type conf: :term:`path-like object` or :term:`text file` opened for reading
                or :class:`~configparser.ConfigParser` object
    :param spec: the specification
    :type spec: :term:`path-like object` or :term:`text file` opened for reading
                or ``None``
    :param bool create_properties: if ``True`` properties will be created, else
                                   only item access with [sec,opt] can be used
    :param dict converters: same as the ``converters`` argument of
                            :class:`~configparser.ConfigParser`
                            but used directly by this function
    :param kwargs: arguments for the :class:`~configparser.ConfigParser`
                   (ignored if ``conf`` is a :class:`~configparser.ConfigParser`
                   object)
    :return: configuration object
    :rtype: Config
    :raises SpecError: if there is a problem with the specification
    :raises ConfigError: if there is a problem with the configuration
    :raises configparser.Error: from :class:`~configparser.ConfigParser`
    """
    if spec is not None:
        opt_specs = _spec(spec, create_properties,
                          converters if converters else {})
    if isinstance(conf, ConfigParser):
        cp = conf
    else:
        cp = ConfigParser(**kwargs)
        try:
            check_path_like(conf)
            with open(conf) as fh:
                cp.read_file(fh)
        except TypeError:
            cp.read_file(conf)
    if spec is None:
        options = _without_spec(cp, create_properties, kwargs)
    else:
        options = _with_spec(cp, opt_specs, kwargs)

    def cls_cb(ns):
        ns['__module__'] = __name__
        if create_properties:
            for key, data in options.items():
                ns[data.name] = property(_getter(key),
                                         None if data.ro else _setter(key),
                                         _deleter(key))

    Config = types.new_class('Config', (_BaseConfig,), {}, cls_cb)
    return Config(options, create_properties, kwargs)


def convert_choice(choices, *, converter=None, default=None):
    """Return a function that can be used as a converter.

    For an example see the source code of :func:`convert_loglevel`.

    :param choices: any container type that supports the ``in`` operator
                    with acceptable values
    :param converter: a callable that takes one string argument and returns
                      an object of the desired type; ``None`` means no
                      conversion
    :param default: a default value of the desired type or a subclass
                    of :exc:`Exception` which will be raised
    """
    def f(s):
        x = converter(s) if converter else s
        if x in choices:
            return x
        if isinstance(default, type) and issubclass(default, Exception):
            raise default('invalid choice: %s' % s)
        return default
    return f


def convert_loglevel(default_level=None):
    """Return a converter function for logging levels.

    Valid values are the logging levels as defined in the :mod:`logging` module.

    :param str default_level: the default logging level
    :raises ValueError: if not a valid logging level and ``default_level=None``
    """
    choices = ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    converter = str.upper
    default = default_level or ValueError
    return convert_choice(choices, converter=converter, default=default)


def convert_predicate(predicate, *, converter=None, default=None):
    """Return a converter function with a predicate.

    >>> positive_float = convert_predicate(lambda x: x > 0.0,
    ... converter=float, default=0.0)
    >>> positive_float('1.2')
    1.2
    >>> positive_float('-1.2')
    0.0

    :param predicate: a callable that takes one argument of the desired type
                      and returns ``True`` if it is acceptable
    :param converter: a callable that takes one string argument and returns
                      an object of the desired type; ``None`` means no
                      conversion
    :param default: a default value of the desired type or a subclass
                    of :exc:`Exception` which will be raised instead
    """
    def f(s):
        x = converter(s) if converter else s
        if predicate(x):
            return x
        if isinstance(default, type) and issubclass(default, Exception):
            raise default('invalid value: %s' % s)
        return default
    return f
