"""
Python library for scraping and storing information from FindAGrave.com
"""

# from .api import MemorialException  # noqa
# noinspection PyUnresolvedReferences
from graver.api import (
    Cemetery,
    Driver,
    Memorial,
    MemorialAliasError,
    MemorialSummary,
    MemorialException,
    MemorialMergedException,
    MemorialParseException,
    MemorialRemovedException,
    NotFound,
    RESEARCH_TASK_STATUSES,
    ResearchTaskNotFound,
    alias_history,
    get_memorial_alias,
    list_memorial_aliases,
    list_research_tasks,
    queue_memorials,
    record_failed_task_scrape,
    record_memorial_alias,
    record_merged_task_scrape,
    resolve_memorial_alias,
    reverse_alias_lookup,
    retract_memorial_alias,
    save_completed_task_scrape,
    show_research_task,
    update_research_task,
)

from .constants import *  # noqa


__all__ = (
    "Cemetery",
    "Driver",
    "Memorial",
    "MemorialAliasError",
    "MemorialSummary",
    "MemorialException",
    "MemorialMergedException",
    "MemorialParseException",
    "MemorialRemovedException",
    "NotFound",
    "RESEARCH_TASK_STATUSES",
    "ResearchTaskNotFound",
    "alias_history",
    "get_memorial_alias",
    "list_memorial_aliases",
    "list_research_tasks",
    "queue_memorials",
    "record_failed_task_scrape",
    "record_memorial_alias",
    "record_merged_task_scrape",
    "resolve_memorial_alias",
    "reverse_alias_lookup",
    "retract_memorial_alias",
    "save_completed_task_scrape",
    "show_research_task",
    "update_research_task",
)

import logging
from logging import NullHandler


logging.getLogger(__name__).addHandler(NullHandler())

del NullHandler
