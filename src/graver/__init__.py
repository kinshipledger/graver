"""Top-level package for graver.

Application clients should import the supported typed API from
:mod:`graver.application`. Parser, persistence, transport, and CLI modules are
implementation details and are intentionally not re-exported here.
"""

__all__: tuple[str, ...] = ()

import logging
from logging import NullHandler

logging.getLogger(__name__).addHandler(NullHandler())

del NullHandler
