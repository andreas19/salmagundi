"""Easy and simple configuration.

.. versionadded:: 0.7.0

.. deprecated:: 0.14.0

.. warning::

   This module has been deprecated. Use `EaSimpConf`_ instead. It has the same
   API; only the imports must be changed from ``salmagundi.config`` to
   ``easimpconf``.

   For now this module imports all public functions/classes of ``easimpconf``
   into its own namespace. It will be removed in one a the next releases without
   further notice.

Documentation: `API reference`_ of ``EaSimpConf``

.. _API reference: https://andreas19.github.io/easimpconf/mod_api.html

.. _EaSimpConf: https://pypi.org/project/easimpconf/
"""

import warnings

from easimpconf import *  # noqa: F401, F403

warnings.warn("deprecated (see documentation)", DeprecationWarning)
