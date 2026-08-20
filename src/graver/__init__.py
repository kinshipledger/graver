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
    NotFound,
    RESEARCH_TASK_STATUSES,
    ResearchTaskNotFound,
    list_research_tasks,
    queue_memorials,
    record_failed_task_scrape,
    save_completed_task_scrape,
    show_research_task,
    update_research_task,
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
    "NotFound",
    "RESEARCH_TASK_STATUSES",
    "ResearchTaskNotFound",
    "list_research_tasks",
    "queue_memorials",
    "record_failed_task_scrape",
    "save_completed_task_scrape",
    "show_research_task",
    "update_research_task",
)

import logging
from logging import NullHandler


logging.getLogger(__name__).addHandler(NullHandler())

del NullHandler
