"""Legacy pre-1.0 compatibility imports for graver.

New application clients should import typed services from :mod:`graver.application`.
The names retained here support the current CLI and historical pre-1.0 callers; they
do not define the future 1.0 public façade.
"""

from graver.api import (
    RESEARCH_TASK_STATUSES,
    Cemetery,
    Driver,
    Memorial,
    MemorialAliasError,
    MemorialException,
    MemorialMergedException,
    MemorialParseException,
    MemorialRemovedException,
    MemorialSummary,
    NotFound,
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
    retract_memorial_alias,
    reverse_alias_lookup,
    save_completed_task_scrape,
    show_research_task,
    update_research_task,
)

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
