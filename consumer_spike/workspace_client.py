"""Exercise the documented workspace API from an installed graver wheel."""

from __future__ import annotations

import sys
from pathlib import Path

from graver.application import (
    ResearchQueueRequest,
    ResearchTaskQuery,
    create_database,
    open_workspace,
)


def main(database: Path) -> None:
    """Create, open, inspect, and query one disposable workspace database."""
    created = create_database(str(database))
    workspace = open_workspace(created)
    assert workspace.database.inspect().current
    assert workspace.work.list(ResearchTaskQuery(limit=5)) == ()
    assert workspace.work.queue(ResearchQueueRequest()).created == 0
    assert not hasattr(workspace, "connection")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
