import importlib.metadata
import json
import logging
import os
import re
import sys
from logging.handlers import RotatingFileHandler
from time import sleep
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import typer
from tqdm import tqdm

from graver import (
    Cemetery,
    Driver,
    Memorial,
    MemorialAliasError,
    MemorialMergedException,
    MemorialParseException,
    NotFound,
    ResearchTaskNotFound,
    get_memorial_alias,
    list_memorial_aliases,
    list_research_tasks,
    queue_memorials as queue_memorials_in_database,
    record_failed_task_scrape,
    record_memorial_alias,
    record_merged_task_scrape,
    resolve_memorial_alias,
    retract_memorial_alias,
    save_completed_task_scrape,
    show_research_task,
    update_research_task,
)
from graver.constants import (
    APP_NAME,
    FINDAGRAVE_BASE_URL,
    MEMORIAL_CANONICAL_URL_FORMAT,
)


log = logging.getLogger(__name__)

# Global Driver
cli_driver = Driver()

# Defaults
DEFAULT_DB_FILE_NAME = "graves.db"

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


app = typer.Typer(
    add_completion=False, context_settings={"help_option_names": ["-h", "--help"]}
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
        help="Set logging level, e.g. --log-level=debug",
    ),
):
    pass


# TODO: Add support for output CSV
# TODO: Add init command

# def get_urls_from_gedcom(gedfile: str):
# TODO add gedcom input support
# # read from gedcom
# with open('tree.ged', encoding='utf8') as ged:
#     for line in ged.readlines():
#         num_memorials+=1
#         if '_LINK ' in line and 'findagrave.com' in line:
#             for unit in line.split('&'):
#                 if 'GRid=' in unit:
#                     if unit[5:-1] not in graveids:
#                         graveids.append(unit[5:-1])
#                         #print(graveids[numids])
#                         numids+=1
# return


def print_failed_urls(urls: list):
    if len(urls) > 0:
        text = "\n".join(urls)
        log.info(f"Failed urls were:\n{text}")


def format_url(line: str):
    """
    Creates a properly formed FindAGrave URL from a memorial id (e.g. 1784) or an
    old-style FindAGrave URL (e.g.
    "https://secure.findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=1784")

    @param line: the input string
    @return: a URL in the form "https://www.findagrave.com/memorial/<id>"
    """
    mid: int = -1
    if re.search("^[0-9]+$", line) is not None:  # id only
        mid = int(line)
        line = MEMORIAL_CANONICAL_URL_FORMAT.format(line)
    elif (match := re.search("GRid=([0-9]+)$", line)) is not None:  # id only
        mid = int(match.group(1))
        line = MEMORIAL_CANONICAL_URL_FORMAT.format(match.group(1))
    elif (match := re.search(r"/memorial/([0-9]+)(?:/.*)?$", line)) is not None:
        mid = int(match.group(1))
    return mid, line


def url_validator(uri):
    result = urlparse(uri)
    is_memorial = ("/memorial/" in uri) or ("GRid=" in uri)
    return is_memorial and all(
        [result.scheme in ["file", "http", "https"], result.path]
    )


def collect_and_validate_urls(input_filename) -> Tuple[List[str], List[str]]:
    good = []
    bad = []
    ids = []
    with open(input_filename) as file:
        while line := file.readline().strip():
            memorial_id, line = format_url(line)
            if not url_validator(line):
                log.warning(f"{line} is not a valid URL")
                bad.append(line)
                continue
            else:
                if memorial_id not in ids:
                    ids.append(memorial_id)
                    good.append(line)
    log.info(ids)
    return good, bad


def parse_and_save_memorial(url) -> Memorial:
    try:
        m = Memorial.parse(url).save()
    except MemorialMergedException as ex:
        log.warning(ex)
        m = Memorial.parse(ex.new_url).save()
    return m


@app.command()
def scrape_file(
    input_filename: str,
    db: str = typer.Option(
        DEFAULT_DB_FILE_NAME, "--db", help="Database name (results will be stored here)"
    ),
):
    """Scrape URLs from a file"""
    log.debug(f"Input file: {input_filename}")
    log.debug(f"Database file: {db}")

    urls: List[str]
    failed_urls: List[str]

    # Collect and validate URLs
    try:
        urls, failed_urls = collect_and_validate_urls(input_filename)
        log.info(f"Downloading {len(urls)} memorials")
        log.debug(f"URLS = {urls}")
    except OSError as e:
        log.error(e)
        raise typer.Exit(1)

    # Process URLs
    request_interval_ms = 2000
    scraped = 0
    disable = os.getenv("TQDM_DISABLE")
    os.environ["DATABASE_NAME"] = db
    Memorial.create_table(db)
    # Pass in driver to ensure we reuse the same session
    # driver: Driver = Driver()
    for url in (pbar := tqdm(urls, disable=bool(disable))):
        pbar.set_postfix_str(url)
        try:
            parse_and_save_memorial(url)
            scraped += 1
            pbar.set_postfix_str("")
            sleep(request_interval_ms / 1000)
        except MemorialParseException as ex:
            log.error(ex)
            failed_urls.append(url)

    log.info(f"Successfully scraped {scraped} of {len(urls)}")
    print_failed_urls(failed_urls)


@app.command()
def scrape_url(
    url: str,
    db: str = typer.Option(
        DEFAULT_DB_FILE_NAME, "--db", help="Database name (results will be stored here)"
    ),
):
    """Scrape a specific memorial URL"""
    if not url_validator(url):
        log.error(f"Invalid or non-memorial URL: [{url}]")
        raise typer.Exit(1)
    Memorial.create_table(db)
    try:
        m: Memorial = parse_and_save_memorial(url)
    except MemorialParseException as ex:
        log.error(ex)
        raise typer.Exit(1)
    log.info(m.to_json())


@app.command()
def queue_memorials(
    db: str = typer.Option(
        DEFAULT_DB_FILE_NAME, "--db", help="Database containing memorials to queue"
    ),
    cemetery_id: int = typer.Option(
        None, "--cemetery-id", help="Only queue memorials from this cemetery"
    ),
    priority: int = typer.Option(0, "--priority", help="Priority for new tasks"),
):
    """Create durable research tasks for memorials already in the database."""
    created, existing = queue_memorials_in_database(
        db, cemetery_id=cemetery_id, priority=priority
    )
    typer.echo(f"Created {created} research tasks; {existing} already present.")


def _json_output(value) -> None:
    typer.echo(json.dumps(value, ensure_ascii=False, sort_keys=True))


@app.command("list-aliases")
def list_aliases(
    db: str = typer.Option(DEFAULT_DB_FILE_NAME, "--db"),
    status: Optional[str] = typer.Option(None, "--status"),
    target_id: Optional[int] = typer.Option(None, "--target-id"),
    limit: int = typer.Option(20, "--limit", min=1),
    json_output: bool = typer.Option(False, "--json"),
):
    """List current memorial alias mappings without network access."""
    try:
        aliases = list_memorial_aliases(db, status, target_id, limit)
    except MemorialAliasError as ex:
        raise typer.BadParameter(str(ex))
    if json_output:
        _json_output(aliases)
        return
    for alias in aliases:
        typer.echo(
            f"{alias['source_memorial_id']} ({alias['source_name'] or '-'}) -> "
            f"{alias['target_memorial_id']} ({alias['target_name'] or '-'}) | "
            f"{alias['alias_type']} | {alias['status']} | "
            f"{alias['first_observed_at']} | {alias['last_observed_at']}"
        )


@app.command("show-alias")
def show_alias(
    memorial_id: int,
    db: str = typer.Option(DEFAULT_DB_FILE_NAME, "--db"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Show current alias resolution and immutable history."""
    try:
        result = get_memorial_alias(db, memorial_id)
    except (NotFound, MemorialAliasError) as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(1)
    if json_output:
        _json_output(result)
        return
    typer.echo(f"Alias {memorial_id}: {' -> '.join(map(str, result['path']))}")
    typer.echo(f"Canonical memorial: {result['canonical_memorial_id']}")
    for item in result["history"]:
        typer.echo(
            f"  {item['observed_at']} | {item['event_type']} | "
            f"{item['source_memorial_id']} -> {item['target_memorial_id']}"
        )


@app.command("record-alias")
def record_alias(
    source_id: int,
    target_id: int,
    db: str = typer.Option(DEFAULT_DB_FILE_NAME, "--db"),
    alias_type: str = typer.Option(..., "--type"),
    source_url: Optional[str] = typer.Option(None, "--source-url"),
    target_url: Optional[str] = typer.Option(None, "--target-url"),
    reason: Optional[str] = typer.Option(None, "--reason"),
):
    """Record a reviewed memorial alias without scraping."""
    try:
        result = record_memorial_alias(
            db, source_id, target_id, alias_type, source_url, target_url, reason
        )
    except (NotFound, MemorialAliasError) as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(1)
    _json_output(result)


@app.command("retract-alias")
def retract_alias(
    source_id: int,
    db: str = typer.Option(DEFAULT_DB_FILE_NAME, "--db"),
    reason: str = typer.Option(..., "--reason"),
):
    """Explicitly retract an active memorial alias."""
    try:
        result = retract_memorial_alias(db, source_id, reason)
    except MemorialAliasError as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(1)
    _json_output(result)


@app.command("list-tasks")
def list_tasks(
    db: str = typer.Option(
        DEFAULT_DB_FILE_NAME, "--db", help="Database containing research tasks"
    ),
    status: Optional[str] = typer.Option(None, "--status"),
    cemetery_id: Optional[int] = typer.Option(None, "--cemetery-id"),
    limit: int = typer.Option(20, "--limit", min=1),
    json_output: bool = typer.Option(False, "--json"),
):
    """List queued memorial research tasks without making network requests."""
    try:
        tasks = list_research_tasks(db, status, cemetery_id, limit)
    except ValueError as ex:
        raise typer.BadParameter(str(ex))
    if json_output:
        _json_output(tasks)
        return
    for task in tasks:
        alias_marker = (
            f" | alias->{task['alias_target_id']}"
            if task.get("alias_status") == "active"
            else ""
        )
        typer.echo(
            "{memorial_id} | {name} | {birth}–{death} | cemetery {cemetery_id} | "
            "{detail_level} | {status} | priority {priority} | {owner} | "
            "{last_activity_at}".format(
                **{
                    key: ("-" if value is None else value)
                    for key, value in task.items()
                }
            )
            + alias_marker
        )


@app.command("show-task")
def show_task(
    memorial_id: int,
    db: str = typer.Option(
        DEFAULT_DB_FILE_NAME, "--db", help="Database containing the research task"
    ),
    json_output: bool = typer.Option(False, "--json"),
):
    """Show one task, its current source record, and observation history."""
    try:
        result = show_research_task(db, memorial_id)
    except (NotFound, ResearchTaskNotFound) as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(1)
    if json_output:
        _json_output(result)
        return
    task = result["task"]
    grave = result["grave"]
    typer.echo(
        f"Task {memorial_id}: {task['status']} (priority {task['priority']}, "
        f"owner {task['owner'] or '-'})"
    )
    typer.echo(
        f"Memorial: {grave['name'] or '-'} | {grave['birth'] or '-'}–"
        f"{grave['death'] or '-'} | cemetery {grave['cemetery_id'] or '-'} | "
        f"{grave['detail_level'] or '-'}"
    )
    if result["cemetery"] is not None:
        cemetery = result["cemetery"]
        typer.echo(
            f"Cemetery: {cemetery['name'] or '-'} | "
            f"{cemetery['location'] or '-'} | {cemetery['url'] or '-'}"
        )
    alias = result["alias"]
    if alias["is_active_source"] or alias["other_active_sources"]:
        typer.echo(
            f"Alias: {' -> '.join(map(str, alias['path']))} | "
            f"target local {alias['canonical_target_exists']} | "
            f"target task {alias['canonical_target_has_task']} | "
            f"other sources {alias['other_active_sources']}"
        )
    typer.echo(f"Observations: {len(result['observations'])}")
    for observation in result["observations"]:
        typer.echo(
            f"  {observation['observed_at']} | {observation['acquisition_level']} | "
            f"{observation['fetch_outcome']} | {observation['parser_version']} | "
            f"{json.dumps(observation['payload'], ensure_ascii=False, sort_keys=True)}"
        )


@app.command("update-task")
def update_task(
    memorial_id: int,
    db: str = typer.Option(
        DEFAULT_DB_FILE_NAME, "--db", help="Database containing the research task"
    ),
    status: Optional[str] = typer.Option(None, "--status"),
    priority: Optional[int] = typer.Option(None, "--priority"),
    owner: Optional[str] = typer.Option(None, "--owner"),
    review_note: Optional[str] = typer.Option(None, "--review-note"),
):
    """Explicitly update selected fields on one research task."""
    try:
        task = update_research_task(
            db, memorial_id, status, priority, owner, review_note
        )
    except ValueError as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(2)
    except ResearchTaskNotFound as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(1)
    _json_output(task)


@app.command("scrape-task")
def scrape_task(
    memorial_id: int,
    db: str = typer.Option(
        DEFAULT_DB_FILE_NAME, "--db", help="Database containing the approved task"
    ),
):
    """Scrape exactly one task already approved for full-page enrichment."""
    try:
        current = show_research_task(db, memorial_id)
    except (NotFound, ResearchTaskNotFound) as ex:
        typer.echo(str(ex), err=True)
        raise typer.Exit(1)
    if current["task"]["status"] != "ready_for_full_scrape":
        typer.echo(f"Task {memorial_id} is not ready_for_full_scrape", err=True)
        raise typer.Exit(1)
    resolution = resolve_memorial_alias(db, memorial_id)
    if len(resolution["path"]) > 1:
        typer.echo(
            f"Memorial {memorial_id} is an active alias; canonical target "
            f"{resolution['canonical_memorial_id']} via "
            f"{' -> '.join(map(str, resolution['path']))}",
            err=True,
        )
        raise typer.Exit(1)
    attempted_url = current["grave"]["findagrave_url"] or (
        MEMORIAL_CANONICAL_URL_FORMAT.format(memorial_id)
    )
    try:
        memorial = Memorial.parse(attempted_url)
        result = save_completed_task_scrape(db, memorial_id, memorial)
    except MemorialMergedException as merged:
        source_id, _ = format_url(merged.old_url)
        target_id, _ = format_url(merged.new_url)
        if source_id != memorial_id or target_id < 0:
            record_failed_task_scrape(db, memorial_id, attempted_url, merged)
            typer.echo(
                "Merged-memorial response did not contain the expected source "
                "and target IDs",
                err=True,
            )
            raise typer.Exit(1)
        record_merged_task_scrape(
            db, memorial_id, target_id, merged.old_url, merged.new_url, merged
        )
        typer.echo(
            f"Memorial {memorial_id} redirects to {target_id}; alias recorded for review",
            err=True,
        )
        raise typer.Exit(1)
    except Exception as ex:
        record_failed_task_scrape(db, memorial_id, attempted_url, ex)
        typer.echo(f"Full scrape failed for memorial {memorial_id}: {ex}", err=True)
        raise typer.Exit(1)
    _json_output(result)


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


def name_filter_callback(ctx: typer.Context, value: str):
    # TODO: Use a context and require a name (any combo of first, middle, last)
    #  in order to use these filters
    if (
        "firstname" not in ctx.params
        and "middlename" not in ctx.params
        and "lastname" not in ctx.params
    ):
        raise typer.BadParameter(
            "A name must be specified in order to use name filters"
        )
    return value


@app.command()
def search(
    db: str = typer.Option(
        DEFAULT_DB_FILE_NAME, "--db", help="Database name (results will be stored here)"
    ),
    cemetery_id: int = typer.Option(
        None,
        "--cid",
        "--cemetery-id",
        help="The numeric ID of a FindAGrave cemetery/monument to search within",
    ),
    firstname: str = typer.Option("", "--firstname"),
    middlename: str = typer.Option("", "--middlename"),
    lastname: str = typer.Option("", "--lastname"),
    fulltext: str = typer.Option(
        "", "--fulltext", help="Search names, dates, locations, and keywords"
    ),
    birthyear: int = typer.Option(None, "--birthyear"),
    birthyearfilter: str = typer.Option(
        "",
        "--birthyearfilter",
        callback=year_filter_callback,
        help="exact, before, after, unknown, or a supported +/- year range",
    ),
    deathyear: int = typer.Option(None, "--deathyear"),
    deathyearfilter: str = typer.Option(
        "",
        "--deathyearfilter",
        callback=year_filter_callback,
        help="exact, before, after, unknown, or a supported +/- year range",
    ),
    location: str = typer.Option(
        "",
        "--location",
        help="A location name, e.g. 'Albemarle County, Virginia, USA'. "
        "FindAGrave requires you to also supply locationId.",
    ),
    location_id: str = typer.Option(
        "",
        "--locationId",
        help="A lookup code used by FindAGrave to uniquely identify place-names in its "
        "database.",
    ),
    memorial_id: int = typer.Option(
        None,
        "--id",
        "--memorialid",
        help="The memorial ID. "
        "If supplied, this will supersede all other search terms",
    ),
    mcid: int = typer.Option(
        None, "--mcid", help="The memorial contributor's FindAGrave ID"
    ),
    bio: str = typer.Option(
        "", "--bio", help="Keywords to find in memorial biographies"
    ),
    linkedtoname: str = typer.Option(
        "",
        "--linkedToName",
        help="The name(s), full or partial, of relatives linked to the memorial, "
        "e.g. 'Mary Jefferson' or 'Steve Mike Barry'.",
    ),
    datefilter: int = typer.Option(
        None,
        "--datefilter",
        callback=date_filter_callback,
        help="Date added: 1, 7, 30, or 90 days ago; -90 means older than 90 days",
    ),
    orderby: str = typer.Option(
        "r",
        "--orderby",
        callback=orderby_callback,
        help="Order results by: relevance(r), name(n/n-), birth year(b/b-), "
        "death year(d/d-), cemetery(c/c-), date created(dc), date modified(dm), "
        "plot(pl)",
    ),
    plot: str = typer.Option("", "--plot"),
    no_cemetery: bool = typer.Option(
        None,
        "--noCemetery",
        help="Limit search to memorials not associated with a cemetery (e.g. cremation,"
        " lost at sea, unknown, etc)",
    ),
    famous: bool = typer.Option(
        None,
        "--famous",
        is_flag=False,
        help="Limit search to people designated as Famous by FindAGrave (note: this is "
        "mutually exclusive with --sponsored)",
    ),
    sponsored: bool = typer.Option(
        None,
        "--sponsored",
        is_flag=False,
        help="Limit search to memorials that have been sponsored on FindAGrave (note: "
        "this is mutually exclusive with --famous)",
    ),
    cenotaph: bool = typer.Option(None, "--cenotaph", is_flag=False),
    monument: bool = typer.Option(None, "--monument", is_flag=False),
    veteran: bool = typer.Option(None, "--isVeteran", is_flag=False),
    tags: str = typer.Option(
        "",
        "--tags",
        callback=tags_callback,
        help="Memorial tag (currently: 'american revolutionary war')",
    ),
    include_nickname: bool = typer.Option(
        None, "--includeNickName", callback=name_filter_callback
    ),
    include_maiden_name: bool = typer.Option(
        None, "--includeMaidenName", callback=name_filter_callback
    ),
    include_titles: bool = typer.Option(
        None, "--includeTitles", callback=name_filter_callback
    ),
    exact_name: bool = typer.Option(None, "--exactName", callback=name_filter_callback),
    fuzzy_names: bool = typer.Option(
        None, "--fuzzyNames", callback=name_filter_callback
    ),
    photo_filter: str = typer.Option(
        None, "--photofilter", callback=photofilter_callback
    ),
    gps_filter: str = typer.Option(None, "--gpsfilter", callback=gpsfilter_callback),
    flowers: bool = typer.Option(None, "--flowers", is_flag=False),
    has_plot: bool = typer.Option(None, "--hasPlot", is_flag=False),
    page: int = typer.Option(None, "--page"),
    max_results: int = typer.Option(
        0,
        "--max",
        "--max-results",
        help="The maximum number of results to process (0 == no limit)",
    ),
):
    """Scrape memorial search results with specified search parameters"""
    os.environ["DATABASE_NAME"] = db
    Memorial.create_table(db)

    search_terms: dict = {
        "max_results": max_results,
        "firstname": firstname,
        "middlename": middlename,
        "lastname": lastname,
        "fulltext": fulltext,
        "birthyear": str(birthyear) if birthyear is not None else "",
        "birthyearfilter": birthyearfilter,
        "deathyear": str(deathyear) if deathyear is not None else "",
        "deathyearfilter": deathyearfilter,
        "location": location,
        "locationId": location_id,
        "memorialid": str(memorial_id) if memorial_id is not None else "",
        "mcid": str(mcid) if mcid is not None else "",
        "bio": bio,
        "linkedToName": linkedtoname,
        "datefilter": datefilter if datefilter is not None else "",
        "orderby": orderby,
        "plot": plot,
        "tags": tags,
    }
    optional_terms: dict = {
        "noCemetery": no_cemetery,
        "famous": famous,
        "sponsored": sponsored,
        "cenotaph": cenotaph,
        "monument": monument,
        "isVeteran": veteran,
        "includeNickName": include_nickname,
        "includeMaidenName": include_maiden_name,
        "includeTitles": include_titles,
        "exactName": exact_name,
        "fuzzyNames": fuzzy_names,
        "photofilter": photo_filter,
        "gpsfilter": gps_filter,
        "flowers": flowers,
        "hasPlot": has_plot,
        "page": page,
    }

    for key in optional_terms.keys():
        if optional_terms[key] is not None:
            search_terms[key] = optional_terms[key]

    log.debug(f"Search terms = {search_terms}")

    cem = None
    if cemetery_id is not None:
        cem = Cemetery(f"{FINDAGRAVE_BASE_URL}/cemetery/{cemetery_id}")
        cem.save(db)

    results = Memorial.search(cem, **search_terms)
    log.debug(f"Num results = {len(results)}")
    if len(results) > 0:
        for idx, m in enumerate(results):
            m.save()
            if log.isEnabledFor(logging.DEBUG):
                if idx == 0:
                    log.debug("[" + m.to_json() + ",")
                elif idx == len(results) - 1:
                    log.debug(m.to_json() + "]")
                else:
                    log.debug(m.to_json() + ",")


if __name__ == "__main__":  # pragma: no cover
    typer.run(app)
