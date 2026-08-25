import importlib.metadata
import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

import typer

from graver import config as graver_config
from graver.api import (
    Driver,
    Memorial,
    MemorialAliasError,
    NotFound,
    ResearchTaskNotFound,
    get_memorial_alias,
    list_memorial_aliases,
    record_memorial_alias,
    retract_memorial_alias,
)
from graver.application import (
    ApplicationError,
    MemorialSummarySearchRequest,
    open_workspace,
)
from graver.cli_json import result_envelope
from graver.constants import (
    APP_NAME,
)
from graver.database import (
    DatabaseInitializationError,
    DatabaseLifecycleError,
    DatabaseUpgradeError,
    create_database,
    upgrade_database,
)
from graver.research import (
    EnrichmentAliasBlocked,
    EnrichmentFailed,
    EnrichmentNotApproved,
    EnrichmentRedirected,
    EnrichmentRedirectInvalid,
    ResearchEnrichmentRequest,
    ResearchQueueRequest,
    ResearchService,
    ResearchTaskQuery,
)

log = logging.getLogger(__name__)

# Global Driver
cli_driver = Driver()

# Logging setup
DEFAULT_LOG_FILENAME = "graver.log"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = (
    "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s"
)
DEFAULT_LOG_DATE_FORMAT = "%H:%M:%S"


# set up logging to console and file
logging.root.handlers = []
console = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter("%(message)s")
console.setFormatter(console_formatter)
logging.basicConfig(
    level=DEFAULT_LOG_LEVEL,
    format=DEFAULT_LOG_FORMAT,
    datefmt=DEFAULT_LOG_DATE_FORMAT,
    handlers=[
        RotatingFileHandler(
            DEFAULT_LOG_FILENAME,
            mode="a",
            maxBytes=5 * 1024 * 1024,
            backupCount=2,
            encoding="utf8",
        ),
        console,
    ],
)


def version_callback(value: bool):
    """Return version of graver application"""
    if value:
        metadata = importlib.metadata.metadata(APP_NAME)
        name_str = metadata["Name"]
        version_str = metadata["Version"]
        log.info("{} v{}".format(name_str, version_str))
        raise typer.Exit()


# FIXME clean up logging initialization
def logging_callback(log_level: str):
    """Set log level for graver application"""
    if log_level:
        logging.getLogger().setLevel(log_level.upper())
        log.debug("Log level is " + str(log_level.upper()))


def database_callback(value: Optional[str]) -> str:
    """Resolve all CLI database options through the same precedence rules."""
    try:
        return graver_config.resolve_database(value).path
    except graver_config.GraverConfigurationError as ex:
        raise typer.BadParameter(str(ex))


def database_option(help_text: str):
    return typer.Option(
        None,
        "--db",
        callback=database_callback,
        help=f"{help_text} Overrides GRAVER_DB and the saved default.",
    )


app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Acquire Find a Grave records and manage person-by-person research.",
)
work_app = typer.Typer(help="Choose, review, and advance people in the research queue.")
admin_app = typer.Typer(help="Perform advanced maintenance and diagnostics.")
aliases_app = typer.Typer(help="Review and maintain Find a Grave redirects.")
database_app = typer.Typer(help="Maintain research database schemas and backups.")
app.add_typer(work_app, name="work")
app.add_typer(admin_app, name="admin")
admin_app.add_typer(aliases_app, name="aliases")
admin_app.add_typer(database_app, name="database")


@database_app.command("upgrade")
def admin_database_upgrade(
    database: str = typer.Argument(
        ..., help="Existing Graver database to back up and upgrade."
    ),
):
    """Back up and upgrade an older research database to the current schema."""
    try:
        result = upgrade_database(database)
    except DatabaseUpgradeError as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(1)
    if not result.changed:
        typer.echo(
            f"Research database is already current at schema version "
            f"{result.version}: {result.path}"
        )
        return
    typer.echo(
        f"Upgraded {result.source.source_label} to schema version {result.version}: "
        f"{result.path}\nVerified backup: {result.backup_path}"
    )


@app.callback()
def graver(
    version: bool = typer.Option(
        None,
        "-V",
        "--version",
        case_sensitive=True,
        callback=version_callback,
        help=f"Return version of {APP_NAME} application.",
    ),
    loglevel: str = typer.Option(
        DEFAULT_LOG_LEVEL,
        "-l",
        "--log",
        "--logging",
        callback=logging_callback,
        help="Set message detail: debug, info, warning, error, or critical.",
    ),
):
    pass


@app.command()
def init(
    database: Optional[str] = typer.Argument(
        None,
        help="New research database to create; omit to create ./graves.db.",
    ),
):
    """Create and select a new database; omit DATABASE to create ./graves.db."""
    try:
        initialized = create_database(database)
    except DatabaseInitializationError as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(1)
    try:
        selected = graver_config.select_default_database(str(initialized))
    except graver_config.GraverConfigurationError as ex:
        typer.echo(
            f"Database was initialized at {initialized}, but it could not be "
            f"selected: {ex}",
            err=True,
        )
        raise typer.Exit(1)
    typer.echo(f"Initialized and selected research database: {selected}")


@app.command()
def use(
    database: Optional[str] = typer.Argument(
        None, help="Existing Graver database to use by default."
    ),
    show: bool = typer.Option(
        False, "--show", help="Show the currently selected default database."
    ),
    clear: bool = typer.Option(
        False, "--clear", help="Forget the selected default without deleting it."
    ),
):
    """Select the database Graver should use by default."""
    action_count = int(database is not None) + int(show) + int(clear)
    if action_count != 1:
        raise typer.BadParameter(
            "Choose exactly one action: provide DATABASE, use --show, or use --clear."
        )
    try:
        if database is not None:
            selected = graver_config.select_default_database(database)
            typer.echo(f"Default research database: {selected}")
        elif show:
            selected = graver_config.configured_default_database()
            if selected is None:
                typer.echo(
                    "No default research database is selected. "
                    "Run `graver use DATABASE` to select one."
                )
            else:
                typer.echo(f"Default research database: {selected}")
        else:
            graver_config.clear_default_database()
            typer.echo(
                "The saved default database was cleared. No database was deleted."
            )
    except graver_config.GraverConfigurationError as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(1)


def _json_output(command: str, value) -> None:
    """Write a deterministic, versioned command-result envelope."""
    typer.echo(
        json.dumps(
            result_envelope(command, value),
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def _list_aliases(
    db: str,
    status: Optional[str],
    target_id: Optional[int],
    limit: int,
    json_output: bool,
) -> None:
    """List current memorial alias mappings without network access."""
    try:
        aliases = list_memorial_aliases(db, status, target_id, limit)
    except MemorialAliasError as ex:
        raise typer.BadParameter(str(ex))
    if json_output:
        _json_output("admin.aliases.list", aliases)
        return
    for alias in aliases:
        typer.echo(
            f"{alias['source_memorial_id']} ({alias['source_name'] or '-'}) -> "
            f"{alias['target_memorial_id']} ({alias['target_name'] or '-'}) | "
            f"{alias['alias_type']} | {alias['status']} | "
            f"{alias['first_observed_at']} | {alias['last_observed_at']}"
        )


def _show_alias(memorial_id: int, db: str, json_output: bool) -> None:
    """Show current alias resolution and immutable history."""
    try:
        result = get_memorial_alias(db, memorial_id)
    except (NotFound, MemorialAliasError) as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(1)
    if json_output:
        _json_output("admin.aliases.show", result)
        return
    typer.echo(f"Alias {memorial_id}: {' -> '.join(map(str, result['path']))}")
    typer.echo(f"Canonical memorial: {result['canonical_memorial_id']}")
    for item in result["history"]:
        typer.echo(
            f"  {item['observed_at']} | {item['event_type']} | "
            f"{item['source_memorial_id']} -> {item['target_memorial_id']}"
        )


def _record_alias(
    source_id: int,
    target_id: int,
    db: str,
    alias_type: str,
    source_url: Optional[str],
    target_url: Optional[str],
    reason: Optional[str],
) -> None:
    """Record a reviewed memorial alias without scraping."""
    try:
        result = record_memorial_alias(
            db, source_id, target_id, alias_type, source_url, target_url, reason
        )
    except (NotFound, MemorialAliasError) as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(1)
    _json_output("admin.aliases.record", result)


def _retract_alias(source_id: int, db: str, reason: str) -> None:
    """Explicitly retract an active memorial alias."""
    try:
        result = retract_memorial_alias(db, source_id, reason)
    except MemorialAliasError as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(1)
    _json_output("admin.aliases.retract", result)


def _enrich_task(
    memorial_id: int, db: str, researcher_output: bool, json_output: bool
) -> None:
    service = ResearchService(db)
    try:
        result = service.enrich_memorial(ResearchEnrichmentRequest(memorial_id))
    except (NotFound, ResearchTaskNotFound, DatabaseLifecycleError) as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(1)
    except EnrichmentNotApproved:
        message = (
            "This person is not approved for enrichment."
            if researcher_output
            else f"Task {memorial_id} is not ready_for_full_scrape"
        )
        typer.echo(message, err=True)
        raise typer.Exit(1)
    except EnrichmentAliasBlocked as blocked:
        if researcher_output:
            typer.echo(
                f"Find a Grave redirects this memorial to "
                f"{blocked.canonical_id}. No retrieval was made.",
                err=True,
            )
        else:
            typer.echo(
                f"Memorial {memorial_id} is an active alias; canonical target "
                f"{blocked.canonical_id} via "
                f"{' -> '.join(map(str, blocked.path))}",
                err=True,
            )
        raise typer.Exit(1)
    except EnrichmentRedirectInvalid:
        typer.echo(
            "Merged-memorial response did not contain the expected source "
            "and target IDs",
            err=True,
        )
        raise typer.Exit(1)
    except EnrichmentRedirected as redirected:
        message = (
            f"Find a Grave redirects this memorial to "
            f"{redirected.target_memorial_id}; "
            "the redirect was recorded for review."
            if researcher_output
            else f"Memorial {memorial_id} redirects to "
            f"{redirected.target_memorial_id}; "
            "alias recorded for review"
        )
        typer.echo(message, err=True)
        raise typer.Exit(1)
    except EnrichmentFailed as ex:
        message = (
            "Retrieval failed; the task remains ready for review. " + str(ex)
            if researcher_output
            else f"Full scrape failed for memorial {memorial_id}: {ex}"
        )
        typer.echo(message, err=True)
        raise typer.Exit(1)
    if json_output:
        _json_output("work.enrich", result.to_compatibility_dict())
    else:
        typer.echo(
            f"The full memorial was retrieved. Person {memorial_id} is now "
            f"{result.status}."
        )


def _display_work_list(tasks: list) -> None:
    for task in tasks:
        detail = {
            "full": "fully enriched",
            "summary": "summary-only",
        }.get(task["detail_level"], "acquisition level unknown")
        action = (
            " | Redirect requires review"
            if task.get("alias_status") == "active"
            else ""
        )
        typer.echo(
            f"{task['memorial_id']} | {task['name'] or 'Unknown person'} | "
            f"{task['birth'] or '?'}–{task['death'] or '?'} | "
            f"{task['status']} | priority {task['priority']} | {detail}{action}"
        )


def _load_task_or_exit(db: str, memorial_id: int) -> dict:
    try:
        return ResearchService(db).get_task(memorial_id).to_compatibility_dict()
    except (NotFound, ResearchTaskNotFound, DatabaseLifecycleError) as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(1)


def _display_work_task(result: dict, history: bool = False) -> None:
    task, grave = result["task"], result["grave"]
    typer.echo(
        f"Person: {grave['name'] or 'Unknown'} "
        f"({grave['birth'] or '?'}–{grave['death'] or '?'})"
    )
    typer.echo(
        f"Research: {task['status']} | priority {task['priority']} | "
        f"owner {task['owner'] or 'unassigned'}"
    )
    typer.echo(
        f"Find a Grave: memorial {grave['memorial_id']} | "
        f"{grave['detail_level'] or 'legacy/unclassified'} | "
        f"cemetery {grave['cemetery_id'] or 'unknown'}"
    )
    alias = result["alias"]
    if alias["is_active_source"]:
        typer.echo(
            f"Important: Find a Grave redirects this memorial to "
            f"{alias['canonical_memorial_id']}. Redirect requires review."
        )
        typer.echo(
            f"Next action: review with `graver admin aliases show "
            f"{grave['memorial_id']}`."
        )
    elif task["status"] == "unprocessed":
        typer.echo(
            "Next action: begin research or mark this person ready for enrichment."
        )
    elif task["status"] == "ready_for_full_scrape":
        typer.echo(f"Next action: run `graver work enrich {grave['memorial_id']}`.")
    else:
        typer.echo(
            "Next action: review the current research state and choose a status."
        )
    typer.echo(f"Provenance: {len(result['observations'])} acquisition observations.")
    if history:
        typer.echo("Detailed provenance:")
        for observation in result["observations"]:
            typer.echo(
                f"  {observation['observed_at']} | "
                f"{observation['acquisition_level']} | "
                f"{observation['fetch_outcome']} | "
                f"{observation['parser_version']} | "
                f"{json.dumps(observation['payload'], ensure_ascii=False, sort_keys=True)}"
            )
        if alias["is_active_source"]:
            typer.echo(f"Alias path: {' -> '.join(map(str, alias['path']))}")


@work_app.command("list")
def work_list(
    db: str = database_option("Research database to read."),
    status: Optional[str] = typer.Option(
        None, "--status", help="Filter by research status."
    ),
    cemetery_id: Optional[int] = typer.Option(
        None, "--cemetery-id", help="Show only people from this cemetery ID."
    ),
    limit: int = typer.Option(20, "--limit", min=1, help="Maximum people to show."),
    json_output: bool = typer.Option(
        False, "--json", help="Return complete machine-readable JSON."
    ),
):
    """List people in the research queue and what needs attention."""
    try:
        tasks = [
            task.to_compatibility_dict()
            for task in ResearchService(db).query_tasks(
                ResearchTaskQuery(status, cemetery_id, limit)
            )
        ]
    except ValueError as ex:
        raise typer.BadParameter(str(ex))
    if json_output:
        _json_output("work.list", tasks)
    else:
        _display_work_list(tasks)


@work_app.command("next")
def work_next(
    db: str = database_option("Research database to read."),
    status: Optional[str] = typer.Option(
        "unprocessed", "--status", help="Research status to select."
    ),
    cemetery_id: Optional[int] = typer.Option(
        None, "--cemetery-id", help="Select only people from this cemetery ID."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Return complete machine-readable JSON."
    ),
):
    """Show the next person needing research."""
    try:
        tasks = ResearchService(db).query_tasks(
            ResearchTaskQuery(status, cemetery_id, 1)
        )
    except ValueError as ex:
        raise typer.BadParameter(str(ex))
    if not tasks:
        typer.echo("No people match the requested research queue filters.")
        return
    result = _load_task_or_exit(db, tasks[0].memorial_id)
    if json_output:
        _json_output("work.next", result)
    else:
        _display_work_task(result)


@work_app.command("show")
def work_show(
    memorial_id: int = typer.Argument(
        ..., help="Find a Grave memorial ID for the person to review."
    ),
    db: str = database_option("Research database to read."),
    history: bool = typer.Option(
        False, "--history", help="Include detailed acquisition and redirect history."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Return complete machine-readable JSON."
    ),
):
    """Review one person's current research state."""
    result = _load_task_or_exit(db, memorial_id)
    if json_output:
        _json_output("work.show", result)
    else:
        _display_work_task(result, history)


@work_app.command("mark")
def work_mark(
    memorial_id: int = typer.Argument(
        ..., help="Find a Grave memorial ID for the person to update."
    ),
    db: str = database_option("Research database to update."),
    status: Optional[str] = typer.Option(
        None, "--status", help="New research status for this person."
    ),
    priority: Optional[int] = typer.Option(
        None, "--priority", help="New queue priority; higher numbers are shown first."
    ),
    owner: Optional[str] = typer.Option(
        None, "--owner", help="Researcher responsible for this person."
    ),
    note: Optional[str] = typer.Option(
        None, "--note", help="Review note to retain with this research task."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Return the updated task as machine-readable JSON."
    ),
):
    """Record a research decision or assignment for one person."""
    before = _load_task_or_exit(db, memorial_id)["task"]
    try:
        task = ResearchService(db).update_task(
            memorial_id, status, priority, owner, note
        )
    except ValueError as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(2)
    if json_output:
        _json_output("work.mark", task)
        return
    labels = {
        "status": "status",
        "priority": "priority",
        "owner": "owner",
        "review_note": "note",
    }
    changed = [label for key, label in labels.items() if before[key] != task[key]]
    if changed:
        typer.echo(f"Updated {', '.join(changed)} for person {memorial_id}.")
    else:
        typer.echo(f"No changes were needed for person {memorial_id}.")


@work_app.command("enrich")
def work_enrich(
    memorial_id: int = typer.Argument(
        ..., help="Find a Grave memorial ID approved for full retrieval."
    ),
    db: str = database_option("Research database to update."),
    json_output: bool = typer.Option(
        False, "--json", help="Return the result as machine-readable JSON."
    ),
):
    """Retrieve the full Find a Grave memorial for an approved person."""
    _enrich_task(memorial_id, db, researcher_output=True, json_output=json_output)


@work_app.command("queue")
def work_queue(
    db: str = database_option("Database containing acquired memorials."),
    cemetery_id: Optional[int] = typer.Option(
        None, "--cemetery-id", help="Queue only people from this cemetery ID."
    ),
    priority: int = typer.Option(
        0, "--priority", help="Initial priority assigned only to newly queued people."
    ),
):
    """Add people already acquired to the research queue."""
    result = ResearchService(db).queue_research(
        ResearchQueueRequest(cemetery_id, priority)
    )
    created, existing = result.created, result.existing
    created_label = "person" if created == 1 else "people"
    existing_label = "person was" if existing == 1 else "people were"
    typer.echo(
        f"Added {created} {created_label} to the research queue; "
        f"{existing} {existing_label} already present."
    )


@aliases_app.command("list")
def admin_aliases_list(
    db: str = database_option("Research database to inspect."),
    status: Optional[str] = typer.Option(
        None, "--status", help="Show only active or retracted redirects."
    ),
    target_id: Optional[int] = typer.Option(
        None, "--target-id", help="Show redirects pointing to this memorial ID."
    ),
    limit: int = typer.Option(
        20, "--limit", min=1, help="Maximum number of redirects to show."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Return complete machine-readable JSON."
    ),
):
    """List reviewed Find a Grave redirect mappings."""
    _list_aliases(db, status, target_id, limit, json_output)


@aliases_app.command("show")
def admin_aliases_show(
    memorial_id: int = typer.Argument(
        ..., help="Source memorial ID whose redirect history should be shown."
    ),
    db: str = database_option("Research database to inspect."),
    json_output: bool = typer.Option(
        False, "--json", help="Return complete machine-readable JSON."
    ),
):
    """Inspect one redirect and its immutable history."""
    _show_alias(memorial_id, db, json_output)


@aliases_app.command("record")
def admin_aliases_record(
    source_id: int = typer.Argument(..., help="Memorial ID that redirects elsewhere."),
    target_id: int = typer.Argument(
        ..., help="Memorial ID that is the redirect target."
    ),
    db: str = database_option("Research database to update."),
    alias_type: str = typer.Option(
        ..., "--type", help="Redirect type: merged or redirected."
    ),
    source_url: Optional[str] = typer.Option(
        None, "--source-url", help="Observed URL for the source memorial."
    ),
    target_url: Optional[str] = typer.Option(
        None, "--target-url", help="Observed URL for the target memorial."
    ),
    reason: Optional[str] = typer.Option(
        None, "--reason", help="Research note explaining this reviewed mapping."
    ),
):
    """Record a reviewed Find a Grave redirect or merge."""
    _record_alias(source_id, target_id, db, alias_type, source_url, target_url, reason)


@aliases_app.command("retract")
def admin_aliases_retract(
    source_id: int = typer.Argument(
        ..., help="Source memorial ID whose active redirect should be retracted."
    ),
    db: str = database_option("Research database to update."),
    reason: str = typer.Option(
        ..., "--reason", help="Required explanation for retracting the redirect."
    ),
):
    """Retract an active redirect while preserving its history."""
    _retract_alias(source_id, db, reason)


def gpsfilter_callback(value: str):
    if value is not None:
        if value not in ["gps", "nogps"]:
            raise typer.BadParameter("Only 'gps' or 'nogps' is allowed")
    return value


def photofilter_callback(value: str):
    if value is not None:
        if value not in ["photos", "nophotos"]:
            raise typer.BadParameter("Only 'photos' or 'nophotos' is allowed")
    return value


def year_filter_callback(value: str):
    if value is not None and value != "":
        allowed = [
            "exact",
            "before",
            "after",
            "1",
            "3",
            "5",
            "10",
            "25",
            "unknown",
        ]
        if value not in allowed:
            raise typer.BadParameter(f"Only {', '.join(allowed)} is allowed")
    return value


def date_filter_callback(value: int):
    if value is not None and value not in [1, 7, 30, 90, -90]:
        raise typer.BadParameter("Only 1, 7, 30, 90, or -90 is allowed")
    return value


def orderby_callback(value: str):
    allowed = ["r", "n", "n-", "b", "b-", "d", "d-", "c", "c-", "dc", "dm", "pl"]
    if value not in allowed:
        raise typer.BadParameter(f"Only {', '.join(allowed)} is allowed")
    return value


def tags_callback(value: str):
    if value not in ["", "american revolutionary war"]:
        raise typer.BadParameter("Only 'american revolutionary war' is allowed")
    return value


def name_filter_callback(ctx: typer.Context, value: Optional[bool]):
    if value and (
        not ctx.params.get("first_name")
        and not ctx.params.get("middle_name")
        and not ctx.params.get("last_name")
    ):
        raise typer.BadParameter(
            "A name must be specified in order to use name filters"
        )
    return value


@app.command()
def search(
    db: str = database_option("Database where results will be stored."),
    cemetery_id: int = typer.Option(
        None,
        "--cemetery-id",
        help="Find a Grave cemetery or monument ID to search within.",
    ),
    first_name: str = typer.Option(
        "", "--first-name", help="First name to search for."
    ),
    middle_name: str = typer.Option(
        "", "--middle-name", help="Middle name to search for."
    ),
    last_name: str = typer.Option("", "--last-name", help="Last name to search for."),
    full_text: str = typer.Option(
        "", "--full-text", help="Search names, dates, locations, and keywords."
    ),
    birth_year: int = typer.Option(
        None, "--birth-year", help="Birth year used with --birth-year-filter."
    ),
    birth_year_filter: str = typer.Option(
        "",
        "--birth-year-filter",
        callback=year_filter_callback,
        help="Exact, before, after, unknown, or a supported +/- year range.",
    ),
    death_year: int = typer.Option(
        None, "--death-year", help="Death year used with --death-year-filter."
    ),
    death_year_filter: str = typer.Option(
        "",
        "--death-year-filter",
        callback=year_filter_callback,
        help="Exact, before, after, unknown, or a supported +/- year range.",
    ),
    location: str = typer.Option(
        "",
        "--location",
        help="A location name, e.g. 'Albemarle County, Virginia, USA'. "
        "Find a Grave also requires --location-id.",
    ),
    location_id: str = typer.Option(
        "",
        "--location-id",
        help="A Find a Grave lookup code that uniquely identifies a place in its "
        "database.",
    ),
    memorial_id: int = typer.Option(
        None,
        "--memorial-id",
        help="Find a Grave memorial ID; supersedes all other search terms.",
    ),
    contributor_id: int = typer.Option(
        None, "--contributor-id", help="Find a Grave memorial contributor ID."
    ),
    biography: str = typer.Option(
        "", "--biography", help="Keywords to find in memorial biographies."
    ),
    linked_to_name: str = typer.Option(
        "",
        "--linked-to-name",
        help="The name(s), full or partial, of relatives linked to the memorial, "
        "e.g. 'Mary Jefferson' or 'Steve Mike Barry'.",
    ),
    date_filter: int = typer.Option(
        None,
        "--date-filter",
        callback=date_filter_callback,
        help="Date added: 1, 7, 30, or 90 days ago; -90 means older than 90 days",
    ),
    order_by: str = typer.Option(
        "r",
        "--order-by",
        callback=orderby_callback,
        help="Order results by: relevance(r), name(n/n-), birth year(b/b-), "
        "death year(d/d-), cemetery(c/c-), date created(dc), date modified(dm), "
        "plot(pl)",
    ),
    plot: str = typer.Option("", "--plot", help="Text to match in the burial plot."),
    no_cemetery: Optional[bool] = typer.Option(
        None,
        "--no-cemetery",
        help="Limit search to memorials not associated with a cemetery (e.g. cremation,"
        " lost at sea, unknown, etc)",
    ),
    famous: Optional[bool] = typer.Option(
        None,
        "--famous/--not-famous",
        help="Limit search to people designated as Famous by FindAGrave (note: this is "
        "mutually exclusive with --sponsored)",
    ),
    sponsored: Optional[bool] = typer.Option(
        None,
        "--sponsored/--not-sponsored",
        help="Limit search to memorials that have been sponsored on FindAGrave (note: "
        "this is mutually exclusive with --famous)",
    ),
    cenotaph: Optional[bool] = typer.Option(
        None,
        "--cenotaph/--not-cenotaph",
        help="Include or exclude cenotaph records.",
    ),
    monument: Optional[bool] = typer.Option(
        None,
        "--monument/--not-monument",
        help="Include or exclude monument records.",
    ),
    veteran: Optional[bool] = typer.Option(
        None,
        "--veteran/--not-veteran",
        help="Include or exclude veteran records.",
    ),
    tags: str = typer.Option(
        "",
        "--tags",
        callback=tags_callback,
        help="Memorial tag (currently: 'american revolutionary war')",
    ),
    include_nickname: Optional[bool] = typer.Option(
        None,
        "--include-nickname",
        callback=name_filter_callback,
        help="Include nicknames when matching the supplied name.",
    ),
    include_maiden_name: Optional[bool] = typer.Option(
        None,
        "--include-maiden-name",
        callback=name_filter_callback,
        help="Include maiden names when matching the supplied name.",
    ),
    include_titles: Optional[bool] = typer.Option(
        None,
        "--include-titles",
        callback=name_filter_callback,
        help="Include titles and prefixes when matching the supplied name.",
    ),
    exact_name: Optional[bool] = typer.Option(
        None,
        "--exact-name",
        callback=name_filter_callback,
        help="Require an exact match for the supplied name fields.",
    ),
    fuzzy_names: Optional[bool] = typer.Option(
        None,
        "--fuzzy-names",
        callback=name_filter_callback,
        help="Allow similar spellings for the supplied name fields.",
    ),
    photo_filter: str = typer.Option(
        None,
        "--photo-filter",
        callback=photofilter_callback,
        help="Filter by photo availability: photos or nophotos.",
    ),
    gps_filter: str = typer.Option(
        None,
        "--gps-filter",
        callback=gpsfilter_callback,
        help="Filter by grave coordinates: gps or nogps.",
    ),
    flowers: Optional[bool] = typer.Option(
        None,
        "--flowers/--no-flowers",
        help="Include or exclude memorials that have virtual flowers.",
    ),
    has_plot: Optional[bool] = typer.Option(
        None,
        "--has-plot/--no-plot",
        help="Include or exclude memorials that have burial plot information.",
    ),
    page: int = typer.Option(
        None, "--page", help="Retrieve one specific search-results page."
    ),
    max_results: int = typer.Option(
        0,
        "--max-results",
        help="The maximum number of results to process (0 == no limit)",
    ),
):
    """Find memorial summaries and save them to the research database."""
    try:
        Memorial.create_table(db)
        receipt = open_workspace(db).acquisition.search(
            MemorialSummarySearchRequest(
                cemetery_id=cemetery_id,
                firstname=first_name,
                middlename=middle_name,
                lastname=last_name,
                fulltext=full_text,
                birth_year=birth_year,
                birth_year_filter=birth_year_filter,
                death_year=death_year,
                death_year_filter=death_year_filter,
                location=location,
                location_id=location_id,
                memorial_id=memorial_id,
                contributor_id=contributor_id,
                biography=biography,
                linked_to_name=linked_to_name,
                date_filter=date_filter,
                order_by=order_by,
                plot=plot,
                no_cemetery=no_cemetery,
                famous=famous,
                sponsored=sponsored,
                cenotaph=cenotaph,
                monument=monument,
                veteran=veteran,
                tags=tags,
                include_nickname=include_nickname,
                include_maiden_name=include_maiden_name,
                include_titles=include_titles,
                exact_name=exact_name,
                fuzzy_names=fuzzy_names,
                photo_filter=photo_filter,
                gps_filter=gps_filter,
                flowers=flowers,
                has_plot=has_plot,
                page=page,
                max_results=max_results,
            )
        )
    except ApplicationError as ex:
        log.error(ex)
        raise typer.Exit(1)
    summary_label = (
        "memorial summary"
        if receipt.observations_appended == 1
        else "memorial summaries"
    )
    snapshot_label = (
        "dated snapshot" if receipt.observations_appended == 1 else "dated snapshots"
    )
    typer.echo(
        f"Observed {receipt.observations_appended} {summary_label}: "
        f"{receipt.memorials_created} new, {receipt.memorials_existing} existing."
    )
    typer.echo(
        f"Retained {receipt.observations_appended} {snapshot_label} without replacing "
        "earlier snapshots."
    )
    if receipt.changed_memorials:
        memorial_label = "memorial" if receipt.changed_memorials == 1 else "memorials"
        field_label = "field" if len(receipt.changes) == 1 else "fields"
        typer.echo(
            f"Changed the current display for {receipt.changed_memorials} existing "
            f"{memorial_label} ({len(receipt.changes)} {field_label}):"
        )
        for change in receipt.changes:
            typer.echo(
                f"  {change.memorial_id} | {change.field}: "
                f"{change.previous!r} -> {change.current!r}"
            )
