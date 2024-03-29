History
-------

**2021-08-04 (0.17.1)**
 - Bugfix in inputs.menu()

**2021-08-04 (0.17.0)**
 - Add parameter default to inputs.menu()

**2021-01-19 (0.16.0)**
 - Change in module inputs (see documentation)
 - Remove dependency on ansictrls

**2020-12-26 (0.15.1)**
 - Bugfix: strings.int2str() now works with negative integers
 - Remove deprecated modules config and crypto (use EaSimpConf and PyGemina instead)
 - Include docopt.py in package and and fix it to silence DeprecationWarnings

**2020-08-17 (0.15.0)**
 - Add parameter noecho to inputs.read()
 - Add functions walign(), wlen(), wshorten() to module strings

**2020-07-30 (0.14.0)**
 - Add parameter maxsplit to strings.str2tuple()
 - Deprecate modules crypto and config

**2020-07-12 (0.13.0)**
 - Add method Config.as_dict() in module config
 - Add exception DuplicateError in module config
 - Options can now be added to sections in module config (renamed parameter name -> key)
 - Add a tag to specification in module config
 - Bugfix: Config.\_\_delitem\_\_() now works even if create_properties=False

**2020-04-21 (0.12.0)**
 - Add function convert_string() to module config
 - Add class StopWatch to module utils

**2020-01-30 (0.11.3)**
 - Add parameter numeric to config.convert_loglevel()

**2020-01-16 (0.11.2)**
 - Change utils.ensure_single_instance(): parameter lockfile -> lockname

**2020-01-11 (0.11.1)**
 - Bugfix: utils.ensure_single_instance()

**2020-01-11 (0.11.0)**
 - Add functions sys_exit() and ensure_single_instance() to module utils
 - Add parameter err_code to utils.docopt_helper()

**2020-01-04 (0.10.0)**
 - Add wildcards in spec for sections and options in module config
 - Add function docopt_helper() in module utils

**2020-01-02 (0.9.4)**
 - Bugfix: microseconds format in strings.format_timedelta()

**2019-10-07 (0.9.2)**
 - Fix documentation for module config
 - Link to overview table for selected module now in sidebar

**2019-10-06 (0.9.1)**
 - Bugfix: files.read_lines() stripped all whitespaces, not only line breaks
 - Improve documentation: add overview table to each module

**2019-10-01 (0.9.0)**
 - Add function slugify() to module strings
 - Add class TranslationTable to module strings
 - Change function strings.insert_separator()
 - Add module validation
 - Add \_\_all\_\_ to all modules

**2019-06-26 (0.8.0)**
 - Longer secret keys in module crypto

**2019-05-12 (0.7.3)**
 - Minor improvements/corrections of the documentation
 - Upgrade dependency: cryptography 2.4.2 -> 2.6.1

**2019-04-15 (0.7.2)**
 - Bugfix: problem with inputs.menu() when cursor is in the last row
   of the terminal

**2019-02-07 (0.7.1)**
 - Add 2 tags in module config

**2019-01-31 (0.7.0)**
 - Add module config
 - Add function int2str() to module strings
 - Bugfix: strings.str2tuple() can now use whitespace as separator

**2019-01-15 (0.6.1)**
 - Bugfix: \*_prefix() functions in module strings now handle negative
   numbers correctly

**2019-01-14 (0.6.0)**
 - Add check\_\*() functions to module inputs
 - Add parameter caption to function menu() in module inputs
 - Add parameter errors to \*_all() and \*_lines() functions in module files
 - Add parameter reverse to function insert_separator() in module strings

**2019-01-07 (0.5.0)**
 - Replace create() with touch() in module files
 - Add functions to module files
 - Add functions to module strings
 - Add module crypto
 - Add module utils

**2018-12-27 (0.4.0)**
 - Add functions to module inputs
 - Rename line() to read() in module inputs

**2018-12-24 (0.3.0)**
 - Add module inputs

**2018-12-23 (0.2.0)**
 - Add functions to module colors
 - Add module strings

**2018-12-17 (0.1.0)**
 - First public release

