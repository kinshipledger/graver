"""
Python library for scraping and storing information from FindAGrave.com
"""

# from .api import MemorialException  # noqa
# noinspection PyUnresolvedReferences
from graver.api import (
    Cemetery,
    Driver,
    Memorial,
    MemorialSummary,
    MemorialException,
    MemorialMergedException,
    MemorialParseException,
    MemorialRemovedException,
    queue_memorials,
)

from .constants import *  # noqa


__all__ = (
    "Cemetery",
    "Driver",
    "Memorial",
    "MemorialSummary",
    "MemorialException",
    "MemorialMergedException",
    "MemorialParseException",
    "MemorialRemovedException",
    "queue_memorials",
)

import logging
from logging import NullHandler


logging.getLogger(__name__).addHandler(NullHandler())

del NullHandler
