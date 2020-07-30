"""Cryptography module.

.. versionadded:: 0.5.0

.. deprecated:: 0.14.0

.. warning::

   This module has been deprecated. Use `PyGemina`_ instead. It has the same
   API; only the imports must be changed from ``salmagundi.crypto`` to
   ``gemina``.

   For now this module imports all public functions/classes of ``gemina`` into
   its own namespace. It will be removed in one a the next releases without
   further notice.

Documentation: `API reference`_ of ``PyGemina``

.. _API reference: https://andreas19.github.io/pygemina/mod_api.html

.. _PyGemina: https://pypi.org/project/pygemina/
"""

import warnings

from gemina import *  # noqa: F401, F403

warnings.warn("deprecated (see documentation)", DeprecationWarning)
