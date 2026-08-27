import importlib.metadata
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict

import pytest
from click import unstyle
from click.testing import Result

import graver.api
import graver.cli as graver_cli_module
from graver._sqlite import connect_database
from graver.api import (
    Driver,
    Memorial,
    MemorialMergedException,
    MemorialParseException,
    MemorialSummary,
)
from graver.application import (
    AcquisitionReceipt,
    ResearchEnrichmentFieldChange,
    ResearchEnrichmentResult,
    WorkspaceAcquisition,
)
from graver.constants import APP_NAME, DISTRIBUTION_NAME
from graver.transport import TransportAccessBlocked

from .test import Test

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


@pytest.mark.usefixtures("api_mock", "faker")
class TestCli(Test):
    memorials_by_url: Dict[str, Memorial] = {}
    memorials_by_id: Dict[int, Memorial] = {}

    @staticmethod
    def cache(memorial: Memorial):
        if memorial.findagrave_url not in TestCli.memorials_by_url.keys():
            TestCli.memorials_by_url[memorial.findagrave_url] = memorial
        if memorial.memorial_id not in TestCli.memorials_by_id:
            TestCli.memorials_by_id[memorial.memorial_id] = memorial

    def test_alias_commands_are_deterministic_and_offline(
        self, database, helpers, monkeypatch
    ):
        source = MemorialSummary.from_dict(
            Test.load_memorial_from_json("andrew-jackson")
        ).save()
        monkeypatch.setattr(
            Memorial, "parse", lambda *_args, **_kwargs: pytest.fail("network call")
        )
        recorded = helpers.graver_cli(
            f"admin aliases record {source.memorial_id} 999999 --db '{database.name}' "
            "--type merged --reason reviewed"
        )
        listed = helpers.graver_cli(
            f"admin aliases list --db '{database.name}' --status active --json"
        )
        shown = helpers.graver_cli(
            f"admin aliases show {source.memorial_id} --db '{database.name}' --json"
        )
        retracted = helpers.graver_cli(
            f"admin aliases retract {source.memorial_id} --db '{database.name}' "
            "--reason wrong"
        )
        assert (
            recorded.exit_code
            == listed.exit_code
            == shown.exit_code
            == retracted.exit_code
            == 0
        )
        assert json.loads(listed.output)["data"][0]["target_memorial_id"] == 999999
        assert json.loads(shown.output)["data"]["path"] == [
            source.memorial_id,
            999999,
        ]
        assert (
            json.loads(retracted.output)["data"]["history"][-1]["event_type"]
            == "retracted"
        )

    def test_scrape_task_refuses_known_alias_before_network(
        self, database, helpers, monkeypatch
    ):
        source = MemorialSummary.from_dict(
            Test.load_memorial_from_json("andrew-jackson")
        ).save()
        graver.api.queue_memorials(database.name)
        graver.api.update_research_task(
            database.name, source.memorial_id, status="ready_for_full_scrape"
        )
        graver.api.record_memorial_alias(
            database.name, source.memorial_id, 999999, "merged"
        )
        monkeypatch.setattr(
            Memorial, "parse", lambda *_args, **_kwargs: pytest.fail("network call")
        )
        result = helpers.graver_cli(
            f"work enrich {source.memorial_id} --db '{database.name}'"
        )
        assert result.exit_code == 1
        assert "redirects this memorial" in result.output

    def test_scrape_task_records_new_merge_without_touching_local_target(
        self, database, helpers, monkeypatch
    ):
        source = MemorialSummary.from_dict(
            Test.load_memorial_from_json("andrew-jackson")
        ).save()
        target = MemorialSummary.from_dict(
            Test.load_memorial_from_json("john-j-pershing")
        ).save()
        graver.api.queue_memorials(database.name)
        graver.api.update_research_task(
            database.name, source.memorial_id, status="ready_for_full_scrape"
        )
        target_before = graver.api.show_research_task(database.name, target.memorial_id)
        error = MemorialMergedException(
            "merged", source.findagrave_url, target.findagrave_url
        )
        calls = []

        def merged_once(url):
            calls.append(url)
            raise error

        monkeypatch.setattr(Memorial, "parse", merged_once)
        result = helpers.graver_cli(
            f"work enrich {source.memorial_id} --db '{database.name}'"
        )
        target_after = graver.api.show_research_task(database.name, target.memorial_id)
        source_after = graver.api.show_research_task(database.name, source.memorial_id)
        assert result.exit_code == 1
        assert calls == [source.findagrave_url]
        assert target_after["grave"] == target_before["grave"]
        assert target_after["task"] == target_before["task"]
        assert target_after["observations"] == target_before["observations"]
        assert source_after["task"]["status"] == "ready_for_full_scrape"
        assert source_after["alias"]["canonical_memorial_id"] == target.memorial_id
        assert source_after["observations"][-1]["fetch_outcome"] == "failure"

    @staticmethod
    @pytest.fixture
    def fake_memorial(faker):
        def _fake_memorial() -> Memorial:
            m = faker.memorial(faker)
            TestCli.cache(m)
            return m

        return _fake_memorial

    @staticmethod
    @pytest.fixture
    def api_mock(monkeypatch, faker):
        def _api_mock(url: str) -> bool:
            monkeypatch.setattr(
                "graver.api.Memorial.parse",
                lambda _, **kwargs: TestCli.fake_parse(
                    faker, findagrave_url=url, **kwargs
                ),
            )
            monkeypatch.setattr("graver.api.Memorial.save", TestCli.fake_save)
            monkeypatch.setattr(
                "graver.api.Memorial.create_table", TestCli.fake_create_graves_table
            )
            monkeypatch.setattr(
                "graver.api.Cemetery.create_table", TestCli.fake_create_cemeteries_table
            )
            return True

        return _api_mock

    @staticmethod
    def fake_parse(factory, **kwargs) -> Memorial:
        memorial: Memorial | None = None
        if (url := kwargs.get("findagrave_url", None)) is not None:
            memorial = TestCli.memorials_by_url[url]
        elif (mid := kwargs.get("memorial_id")) is not None:
            memorial = TestCli.memorials_by_id[mid]
        else:
            if "expected" in kwargs:
                memorial = kwargs.get("expected", TestCli.fake_memorial(factory))
        assert memorial is not None
        return memorial

    @staticmethod
    def fake_save(m: Memorial) -> Memorial:
        logging.getLogger(__name__).warning(f"In fake_save for {m}")
        return m

    @staticmethod
    def fake_create_graves_table(filename: str) -> None:
        logging.getLogger(__name__).warning(
            f"In fake_create_graves_table for {filename}"
        )
        return

    @staticmethod
    def fake_create_cemeteries_table(filename: str) -> None:
        logging.getLogger(__name__).warning(
            f"In fake_create_cemeteries_table for {filename}"
        )
        return


class TestCliCommonOptions(TestCli):
    def test_terminal_text_escapes_controls_and_preserves_unicode(self) -> None:
        source = "Zoë\x1b[2J\r\nnext\t\u202efalse"

        assert graver_cli_module._terminal_safe_text(source) == (
            r"Zoë\x1b[2J\r\nnext\t\u202efalse"
        )

    def test_human_task_output_neutralizes_untrusted_controls(self, capsys) -> None:
        graver_cli_module._display_work_list(
            [
                {
                    "alias_status": None,
                    "birth": "1900",
                    "death": "1980",
                    "detail_level": "summary",
                    "memorial_id": 123,
                    "name": "Person\x1b[2J\nForged line",
                    "priority": 100,
                    "status": "unprocessed",
                }
            ]
        )

        output = capsys.readouterr().out
        assert "\x1b" not in output
        assert "Person\\x1b[2J\\nForged line" in output
        assert output.count("\n") == 1

    def test_json_output_preserves_source_values(self, capsys) -> None:
        source = "Person\x1b[2J\nSecond line"

        graver_cli_module._json_output("test.output", {"name": source})

        payload = json.loads(capsys.readouterr().out)
        assert payload["data"]["name"] == source

    def test_import_has_no_persistent_logging_side_effect(self, tmp_path) -> None:
        result = subprocess.run(
            [sys.executable, "-c", "import graver.cli"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
            text=True,
        )

        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""
        assert not (tmp_path / "graver.log").exists()

    @pytest.mark.parametrize("arg", ["-V", "--version"])
    def test_version(self, helpers, arg) -> None:
        metadata = importlib.metadata.metadata(DISTRIBUTION_NAME)
        version_str = metadata["Version"]
        expected_str = "{} v{}".format(APP_NAME, version_str)
        result: Result = helpers.graver_cli(arg)
        assert result.exit_code == 0
        assert result.output == expected_str + "\n"


class TestCliQueueMemorials(TestCli):
    def test_queues_without_network_requests(self, helpers, tmp_path, monkeypatch):
        database = tmp_path / "queue.db"
        Memorial.create_table(str(database))
        with connect_database(database) as connection:
            connection.executemany(
                "INSERT INTO graves (memorial_id, cemetery_id) VALUES (?, ?)",
                [(1, 10), (2, 10), (3, 20)],
            )
            for memorial_id in (1, 2, 3):
                graver.api._ensure_subject_for_memorial(
                    connection, memorial_id, "fixture"
                )

        def fail_network(*args, **kwargs):
            raise AssertionError("work queue must not use the network")

        monkeypatch.setattr("graver.api.Driver.get", fail_network)

        result = helpers.graver_cli(
            f"work queue --db '{database}' --cemetery-id 10 --priority 4"
        )

        assert result.exit_code == 0
        assert (
            "Added 2 people to the research queue; 0 people were already present."
            in result.output
        )
        with connect_database(database) as connection:
            tasks = connection.execute("""SELECT sm.memorial_id, t.status, t.priority
                   FROM research_tasks t
                   JOIN subject_memorials sm ON sm.subject_id=t.subject_id
                   ORDER BY sm.memorial_id""").fetchall()
        assert tasks == [(1, "unprocessed", 4), (2, "unprocessed", 4)]

        repeated = helpers.graver_cli(
            f"work queue --db '{database}' --cemetery-id 10 --priority 1"
        )
        assert repeated.exit_code == 0
        assert (
            "Added 0 people to the research queue; 2 people were already present."
            in repeated.output
        )


class TestCliResearchTasks(Test):
    @staticmethod
    def summary(fixture_name="andrew-jackson", **updates):
        values = Test.load_memorial_from_json(fixture_name)
        values.update(updates)
        return MemorialSummary.from_dict(values)

    @staticmethod
    def full(fixture_name="andrew-jackson", **updates):
        values = Test.load_memorial_from_json(fixture_name)
        values.update(updates)
        return Memorial.from_dict(values)

    def test_list_show_and_update_json_are_stable_and_network_free(
        self, helpers, database, monkeypatch
    ):
        summary = self.summary()
        summary.save()
        graver.api.queue_memorials(database.name, priority=3)

        def fail_network(*args, **kwargs):
            raise AssertionError("research task inspection must not use the network")

        monkeypatch.setattr("graver.api.Driver.get", fail_network)
        listed = helpers.graver_cli(
            f"work list --db '{database.name}' --status unprocessed "
            f"--cemetery-id {summary.cemetery_id} --json"
        )
        shown = helpers.graver_cli(
            f"work show {summary.memorial_id} --db '{database.name}' --json"
        )
        updated = helpers.graver_cli(
            f"work mark {summary.memorial_id} --db '{database.name}' "
            "--status researching --owner researcher --json"
        )

        assert listed.exit_code == shown.exit_code == updated.exit_code == 0
        assert (
            json.loads(listed.output)["data"][0]["memorial_id"] == summary.memorial_id
        )
        assert (
            listed.output
            == json.dumps(json.loads(listed.output), ensure_ascii=False, sort_keys=True)
            + "\n"
        )
        assert (
            json.loads(shown.output)["data"]["observations"][0]["payload"]
            == summary.to_dict()
        )
        assert json.loads(updated.output)["data"]["status"] == "researching"

    def test_missing_memorial_and_missing_task_exit_nonzero(self, helpers, database):
        missing_memorial = helpers.graver_cli(f"work show 999 --db '{database.name}'")
        with connect_database(database.name) as connection:
            connection.execute("INSERT INTO graves (memorial_id) VALUES (999)")
            graver.api._ensure_subject_for_memorial(connection, 999, "fixture")
        missing_task = helpers.graver_cli(f"work show 999 --db '{database.name}'")

        assert missing_memorial.exit_code != 0
        assert "Memorial 999 does not exist" in missing_memorial.output
        assert missing_task.exit_code != 0
        assert "Research task 999 does not exist" in missing_task.output

    @pytest.mark.parametrize(
        "task_exists, status", [(False, None), (True, "researching")]
    )
    def test_scrape_task_preconditions_make_no_request(
        self, helpers, database, monkeypatch, task_exists, status
    ):
        summary = self.summary()
        summary.save()
        if task_exists:
            graver.api.queue_memorials(database.name)
            graver.api.update_research_task(
                database.name, summary.memorial_id, status=status
            )
        calls = []
        monkeypatch.setattr(
            Memorial, "parse", lambda *args, **kwargs: calls.append(args)
        )

        result = helpers.graver_cli(
            f"work enrich {summary.memorial_id} --db '{database.name}'"
        )

        assert result.exit_code != 0
        assert calls == []

    def test_scrape_task_success_processes_only_selected_task(
        self, helpers, database, monkeypatch
    ):
        selected = self.summary()
        other = self.summary("carl-sagan")
        selected.save()
        other.save()
        graver.api.queue_memorials(database.name)
        graver.api.update_research_task(
            database.name,
            selected.memorial_id,
            status="ready_for_full_scrape",
            priority=7,
            owner="owner",
            review_note="keep",
        )
        calls = []

        def parse(url):
            calls.append(url)
            return self.full()

        monkeypatch.setattr(Memorial, "parse", parse)

        result = helpers.graver_cli(
            f"work enrich {selected.memorial_id} --db '{database.name}'"
        )

        assert result.exit_code == 0
        assert "selected fields" in result.output.lower()
        assert "not a complete page archive" in result.output.lower()
        assert calls == [selected.findagrave_url]
        history = helpers.graver_cli(
            f"work show {selected.memorial_id} --db '{database.name}' --history"
        )
        assert history.exit_code == 0
        assert "only the selected structured fields" in history.output.lower()
        assert "not a page archive" in history.output.lower()
        shown = graver.api.show_research_task(database.name, selected.memorial_id)
        other_task = graver.api.show_research_task(database.name, other.memorial_id)
        assert shown["task"]["status"] == "full_scrape_complete"
        assert shown["task"]["priority"] == 7
        assert shown["task"]["owner"] == "owner"
        assert shown["task"]["review_note"] == "keep"
        assert shown["observations"][-1]["acquisition_level"] == "full"
        assert other_task["task"]["status"] == "unprocessed"

    def test_scrape_task_failure_preserves_record_and_human_task_fields(
        self, helpers, database, monkeypatch
    ):
        summary = self.summary(name="preserved name")
        summary.save()
        graver.api.queue_memorials(database.name)
        graver.api.update_research_task(
            database.name,
            summary.memorial_id,
            status="ready_for_full_scrape",
            priority=4,
            owner="owner",
            review_note="human note",
        )

        def fail_parse(url):
            raise MemorialParseException("mocked parse failure")

        monkeypatch.setattr(Memorial, "parse", fail_parse)

        result = helpers.graver_cli(
            f"work enrich {summary.memorial_id} --db '{database.name}'"
        )

        assert result.exit_code != 0
        shown = graver.api.show_research_task(database.name, summary.memorial_id)
        assert shown["grave"]["name"] == "preserved name"
        assert shown["task"]["status"] == "ready_for_full_scrape"
        assert shown["task"]["priority"] == 4
        assert shown["task"]["owner"] == "owner"
        assert shown["task"]["review_note"] == "human note"
        assert shown["observations"][-1]["fetch_outcome"] == "failure"


class TestCliResearcherSurface(Test):
    @staticmethod
    def summary(fixture_name="andrew-jackson", **updates):
        values = Test.load_memorial_from_json(fixture_name)
        values.update(updates)
        return MemorialSummary.from_dict(values)

    @staticmethod
    def full(fixture_name="andrew-jackson", **updates):
        values = Test.load_memorial_from_json(fixture_name)
        values.update(updates)
        return Memorial.from_dict(values)

    def test_use_select_show_and_clear(
        self, helpers, database, isolate_graver_configuration
    ):
        selected = helpers.graver_cli(f"use '{database.name}'")
        shown = helpers.graver_cli("use --show")
        cleared = helpers.graver_cli("use --clear")
        empty = helpers.graver_cli("use --show")
        cleared_again = helpers.graver_cli("use --clear")

        expected_path = str(Path(database.name).resolve())
        assert all(
            result.exit_code == 0
            for result in (selected, shown, cleared, empty, cleared_again)
        )
        assert expected_path in selected.output
        assert expected_path in shown.output
        assert "No default research database is selected" in empty.output
        assert "graver use DATABASE" in empty.output
        assert "No database was deleted" in cleared.output
        assert "No database was deleted" in cleared_again.output
        assert "default_database" not in json.loads(
            isolate_graver_configuration.read_text()
        )

    @pytest.mark.parametrize(
        "command",
        ["use", "use --show --clear", "use some.db --show", "use some.db --clear"],
    )
    def test_use_requires_exactly_one_action(self, helpers, command):
        result = helpers.graver_cli(command)

        assert result.exit_code == 2
        assert "Choose exactly one action" in result.output

    def test_use_reports_malformed_and_stale_configuration(
        self, helpers, isolate_graver_configuration, tmp_path
    ):
        isolate_graver_configuration.parent.mkdir(parents=True)
        isolate_graver_configuration.write_text("{bad-json")
        malformed = helpers.graver_cli("use --show")
        isolate_graver_configuration.write_text(
            json.dumps({"default_database": str(tmp_path / "missing.db")})
        )
        stale = helpers.graver_cli("use --show")

        assert malformed.exit_code == stale.exit_code == 1
        assert "configuration is unreadable" in malformed.output
        assert "does not exist" in stale.output
        assert "graver use" not in stale.output

    def test_use_help_is_researcher_oriented(self, helpers):
        result = helpers.graver_cli("use --help")
        rendered = " ".join(result.output.split())

        assert result.exit_code == 0
        assert "Offline: select, show, or forget the default database" in rendered
        assert "Existing graver database to use by default" in rendered
        assert "Show the currently selected default database" in rendered
        assert "without deleting it" in rendered

    def test_existing_commands_use_central_database_resolution(
        self, helpers, database, tmp_path, monkeypatch
    ):
        saved = Path(database.name).resolve()
        environment = tmp_path / "environment.db"
        explicit = tmp_path / "explicit.db"
        Memorial.create_table(str(environment))
        Memorial.create_table(str(explicit))
        assert helpers.graver_cli(f"use '{saved}'").exit_code == 0
        calls = []
        monkeypatch.setattr(
            "graver.cli.ResearchService.query_tasks",
            lambda service, *_args: calls.append(service.database_name) or (),
        )

        monkeypatch.delenv("GRAVER_DB")
        saved_result = helpers.graver_cli("work list --json")
        monkeypatch.setenv("GRAVER_DB", str(environment))
        environment_result = helpers.graver_cli("work list --json")
        explicit_result = helpers.graver_cli(f"work list --db '{explicit}' --json")

        assert all(
            result.exit_code == 0
            for result in (saved_result, environment_result, explicit_result)
        )
        assert calls == [str(saved), str(environment.resolve()), str(explicit)]
        saved_json = json.loads(saved_result.output)
        assert saved_json == {
            "command": "work.list",
            "data": [],
            "schema_version": 1,
        }
        assert json.loads(environment_result.output)["data"] == []
        assert json.loads(explicit_result.output)["data"] == []

    def test_invalid_saved_database_blocks_command_without_fallback(
        self, helpers, isolate_graver_configuration, tmp_path, monkeypatch
    ):
        monkeypatch.delenv("GRAVER_DB")
        isolate_graver_configuration.parent.mkdir(parents=True)
        isolate_graver_configuration.write_text(
            json.dumps({"default_database": str(tmp_path / "gone.db")})
        )

        result = helpers.graver_cli("work list --json")

        assert result.exit_code == 2
        assert "does not exist" in result.output
        assert not (tmp_path / "gone.db").exists()

    def test_help_uses_progressive_disclosure(self, helpers):
        root = helpers.graver_cli("--help")
        work = helpers.graver_cli("work --help")
        enrich = helpers.graver_cli("work enrich --help")
        aliases = helpers.graver_cli("admin aliases --help")

        assert (
            root.exit_code
            == work.exit_code
            == enrich.exit_code
            == aliases.exit_code
            == 0
        )
        assert "work" in root.output
        assert "admin" in root.output
        for legacy in (
            "list-tasks",
            "show-task",
            "update-task",
            "scrape-task",
            "queue-memorials",
            "list-aliases",
            "show-alias",
            "record-alias",
            "retract-alias",
            "scrape-file",
            "scrape-url",
        ):
            assert legacy not in root.output
        assert "Offline: show the next person needing research" in work.output
        assert "Offline: review one person's current research state" in work.output
        assert "Live: observe one approved memorial" in work.output
        assert "selected structured fields" in enrich.output
        assert "one live" in enrich.output
        for command in ("list", "show", "record", "retract"):
            assert command in aliases.output

    @pytest.mark.parametrize(
        "command",
        [
            "list-tasks",
            "show-task",
            "update-task",
            "scrape-task",
            "queue-memorials",
            "list-aliases",
            "show-alias",
            "record-alias",
            "retract-alias",
            "scrape-file",
            "scrape-url",
        ],
    )
    def test_retired_commands_are_unavailable(self, helpers, command):
        result = helpers.graver_cli(command)

        assert result.exit_code == 2
        assert f"No such command '{command}'" in unstyle(result.output)

    @pytest.mark.parametrize(
        "command, expected_descriptions",
        [
            (
                "work list --help",
                (
                    "Offline: list people",
                    "Research database to read",
                    "Filter by machine status",
                    "ready_for_full_scrape",
                    "full_scrape_complete",
                    "Maximum people to show",
                    "machine-readable JSON",
                ),
            ),
            (
                "work show --help",
                (
                    "memorial ID for the person",
                    "detailed acquisition and redirect",
                ),
            ),
            (
                "work mark --help",
                (
                    "New machine status",
                    "unprocessed",
                    "researching",
                    "ready_for_full_scrape",
                    "full_scrape_complete",
                    "ready_for_review",
                    "completed",
                    "unable_to_resolve",
                    "Changing status is offline",
                    "work enrich makes the later live request",
                    "higher numbers are shown",
                    "Researcher responsible",
                    "Review note",
                ),
            ),
            (
                "admin aliases record --help",
                (
                    "Memorial ID that redirects elsewhere",
                    "Redirect type: merged or redirected",
                    "Research note explaining",
                ),
            ),
            (
                "search --help",
                (
                    "Live: find memorial summaries",
                    "First name to search for",
                    "Birth year used with",
                    "Include nicknames",
                    "Filter by grave coordinates",
                    "specific search-results",
                    "summaries to process during this live search",
                    "default: 20",
                ),
            ),
        ],
    )
    def test_visible_help_describes_arguments_and_options(
        self, helpers, command, expected_descriptions
    ):
        result = helpers.graver_cli(command)

        assert result.exit_code == 0
        rendered_help = " ".join(unstyle(result.output).replace("│", " ").split())
        for description in expected_descriptions:
            assert description in rendered_help

    def test_work_list_filters_orders_and_marks_redirects(self, helpers, database):
        first = self.summary(name="First", cemetery_id=10).save()
        second = self.summary("carl-sagan", name="Second", cemetery_id=10).save()
        self.summary("john-j-pershing", cemetery_id=20).save()
        graver.api.queue_memorials(database.name)
        graver.api.update_research_task(database.name, first.memorial_id, priority=3)
        graver.api.update_research_task(database.name, second.memorial_id, priority=8)
        graver.api.record_memorial_alias(
            database.name, second.memorial_id, 999999, "merged"
        )

        result = helpers.graver_cli(
            f"work list --db '{database.name}' --status unprocessed " "--cemetery-id 10"
        )

        assert result.exit_code == 0
        assert result.output.index("Second") < result.output.index("First")
        assert "Unprocessed [unprocessed]" in result.output
        assert "summary-only" in result.output
        assert "Redirect requires review" in result.output
        assert "alias_path" not in result.output

    def test_work_list_does_not_guess_legacy_acquisition_level(self, helpers, database):
        summary = self.summary().save()
        graver.api.queue_memorials(database.name)
        with connect_database(database.name) as connection:
            connection.execute(
                "UPDATE graves SET detail_level=NULL WHERE memorial_id=?",
                (summary.memorial_id,),
            )

        result = helpers.graver_cli(f"work list --db '{database.name}'")

        assert result.exit_code == 0
        assert "acquisition level unknown" in result.output
        assert "summary-only" not in result.output

    def test_work_next_is_deterministic_and_empty_is_success(self, helpers, database):
        older = self.summary(name="Older activity").save()
        newer = self.summary("carl-sagan", name="Newer activity").save()
        graver.api.queue_memorials(database.name)
        graver.api.update_research_task(database.name, older.memorial_id, priority=4)
        graver.api.update_research_task(database.name, newer.memorial_id, priority=9)

        selected = helpers.graver_cli(f"work next --db '{database.name}' --json")
        empty = helpers.graver_cli(
            f"work next --db '{database.name}' --status completed"
        )

        assert selected.exit_code == empty.exit_code == 0
        selected_json = json.loads(selected.output)
        assert selected_json["schema_version"] == 1
        assert selected_json["command"] == "work.next"
        assert selected_json["data"]["grave"]["memorial_id"] == newer.memorial_id
        assert "No people match" in empty.output

    def test_work_show_discloses_history_and_alias_only_when_relevant(
        self, helpers, database
    ):
        ordinary = self.summary().save()
        redirected = self.summary("carl-sagan").save()
        graver.api.queue_memorials(database.name)

        ordinary_result = helpers.graver_cli(
            f"work show {ordinary.memorial_id} --db '{database.name}'"
        )
        history_result = helpers.graver_cli(
            f"work show {ordinary.memorial_id} --db '{database.name}' --history"
        )
        graver.api.record_memorial_alias(
            database.name, redirected.memorial_id, 999999, "redirected"
        )
        alias_result = helpers.graver_cli(
            f"work show {redirected.memorial_id} --db '{database.name}'"
        )
        json_result = helpers.graver_cli(
            f"work show {redirected.memorial_id} --db '{database.name}' --json"
        )

        assert "alias" not in ordinary_result.output.lower()
        assert "Unprocessed [unprocessed]" in ordinary_result.output
        assert "subject_id" not in ordinary_result.output
        assert "subject_id" not in history_result.output
        assert "payload" not in ordinary_result.output
        assert "Detailed provenance" in history_result.output
        assert ordinary.name in history_result.output
        assert "Redirect requires review" in alias_result.output
        assert "alias_path" not in alias_result.output
        shown_json = json.loads(json_result.output)
        assert shown_json["schema_version"] == 1
        assert shown_json["command"] == "work.show"
        assert shown_json["data"]["alias"]["path"] == [
            redirected.memorial_id,
            999999,
        ]
        assert "subject_id" not in json_result.output

    def test_work_mark_preserves_fields_and_noop_timestamps(self, helpers, database):
        summary = self.summary().save()
        graver.api.queue_memorials(database.name, priority=6)
        graver.api.update_research_task(
            database.name, summary.memorial_id, owner="owner", review_note="old"
        )

        changed = helpers.graver_cli(
            f"work mark {summary.memorial_id} --db '{database.name}' "
            "--status researching --note new"
        )
        before_noop = graver.api.show_research_task(database.name, summary.memorial_id)[
            "task"
        ]
        noop = helpers.graver_cli(
            f"work mark {summary.memorial_id} --db '{database.name}' "
            "--status researching"
        )
        machine_result = helpers.graver_cli(
            f"work mark {summary.memorial_id} --db '{database.name}' "
            "--status researching --json"
        )
        after_noop = graver.api.show_research_task(database.name, summary.memorial_id)[
            "task"
        ]

        assert changed.exit_code == noop.exit_code == machine_result.exit_code == 0
        assert "Updated status, note" in changed.output
        assert "Research in progress [researching]" in changed.output
        assert "Offline; does not approve a live retrieval" in changed.output
        assert "No changes were needed" in noop.output
        assert after_noop == before_noop
        assert after_noop["priority"] == 6
        assert after_noop["owner"] == "owner"
        assert after_noop["review_note"] == "new"
        assert json.loads(machine_result.output)["command"] == "work.mark"

    @pytest.mark.parametrize(
        "status, label, next_action",
        [
            ("unprocessed", "Unprocessed", "begin research"),
            ("researching", "Research in progress", "continue research"),
            (
                "ready_for_full_scrape",
                "Approved for enrichment",
                "Next action (live)",
            ),
            (
                "full_scrape_complete",
                "Enrichment complete",
                "review the retained observation",
            ),
            ("ready_for_review", "Ready for review", "review the current research"),
            ("completed", "Research complete", "no action is required"),
            (
                "unable_to_resolve",
                "Unable to resolve",
                "resume when new evidence is available",
            ),
        ],
    )
    def test_work_show_explains_every_research_state(
        self, helpers, database, status, label, next_action
    ):
        summary = self.summary().save()
        graver.api.queue_memorials(database.name)
        graver.api.update_research_task(
            database.name, summary.memorial_id, status=status
        )

        result = helpers.graver_cli(
            f"work show {summary.memorial_id} --db '{database.name}'"
        )

        assert result.exit_code == 0
        assert f"{label} [{status}]" in result.output
        assert next_action in result.output

    def test_work_queue_is_idempotent_and_network_free(
        self, helpers, database, monkeypatch
    ):
        summary = self.summary().save()
        monkeypatch.setattr(
            Memorial, "parse", lambda *_args, **_kwargs: pytest.fail("network call")
        )

        first = helpers.graver_cli(f"work queue --db '{database.name}'")
        second = helpers.graver_cli(f"work queue --db '{database.name}'")

        assert first.exit_code == second.exit_code == 0
        assert "Added 1 person" in first.output
        assert "Added 0 people" in second.output
        task = graver.api.show_research_task(database.name, summary.memorial_id)["task"]
        assert task["status"] == "unprocessed"

    def test_work_enrich_uses_existing_one_person_safety(
        self, helpers, database, monkeypatch
    ):
        summary = self.summary().save()
        graver.api.queue_memorials(database.name)
        calls = []
        monkeypatch.setattr(
            Memorial, "parse", lambda url: calls.append(url) or self.full()
        )

        refused = helpers.graver_cli(
            f"work enrich {summary.memorial_id} --db '{database.name}'"
        )
        graver.api.update_research_task(
            database.name, summary.memorial_id, status="ready_for_full_scrape"
        )
        enriched = helpers.graver_cli(
            f"work enrich {summary.memorial_id} --db '{database.name}' --json"
        )

        assert refused.exit_code == 1
        assert "not approved for enrichment" in refused.output
        assert calls == [summary.findagrave_url]
        assert enriched.exit_code == 0
        enriched_json = json.loads(enriched.output)
        assert enriched_json["command"] == "work.enrich"
        assert enriched_json["data"]["status"] == "full_scrape_complete"
        assert set(enriched_json["data"]) == {
            "memorial_id",
            "status",
            "full_observed_at",
        }

    def test_work_enrich_explains_changes_and_retained_observations(
        self, helpers, database, monkeypatch
    ):
        summary = self.summary(name="Earlier Name").save()
        graver.api.queue_memorials(database.name)
        graver.api.update_research_task(
            database.name,
            summary.memorial_id,
            status="ready_for_full_scrape",
        )
        monkeypatch.setattr(
            Memorial,
            "parse",
            lambda _url: self.full(name="Later\nName", birth_place="New place"),
        )

        result = helpers.graver_cli(
            f"work enrich {summary.memorial_id} --db '{database.name}'"
        )

        assert result.exit_code == 0
        assert "Acquisition receipt:" in result.output
        assert "Compared retained observation" in result.output
        assert "with new selected-field observation" in result.output
        assert "Newly retained values:" in result.output
        assert 'birth_place: null -> "New place"' in result.output
        assert "Different retained values:" in result.output
        assert 'name: "Earlier Name" -> "Later\\nName"' in result.output
        assert "equal non-null values" in result.output
        assert "equality is not corroboration or verification" in result.output
        assert "website display, not proven kinship" in result.output
        assert "Differences do not supersede earlier values" in result.output

    def test_enrichment_receipt_handles_no_prior_observation_or_changes(
        self, monkeypatch
    ):
        output = []
        monkeypatch.setattr(graver_cli_module, "_human_echo", output.append)

        graver_cli_module._display_enrichment_receipt(
            ResearchEnrichmentResult(
                memorial_id=1075,
                status="full_scrape_complete",
                full_observed_at="observed",
                observation_id=4,
                displayed_relationship_links=1,
            )
        )

        assert output == [
            "Acquisition receipt:",
            "  Retained selected-field observation 4.",
            "  No value differences were detected in supported fields.",
            "  0 supported fields had equal non-null values in the two retained "
            "representations; equality is not corroboration or verification.",
            "  Retained 1 Find a Grave-displayed relationship link; "
            "website display, not proven kinship.",
            "  Differences do not supersede earlier values; evaluate both "
            "observations and underlying sources before changing a research "
            "conclusion.",
        ]

    def test_enrichment_receipt_marks_missing_later_value_as_indeterminate(
        self, monkeypatch
    ):
        output = []
        monkeypatch.setattr(graver_cli_module, "_human_echo", output.append)

        graver_cli_module._display_enrichment_receipt(
            ResearchEnrichmentResult(
                memorial_id=1075,
                status="full_scrape_complete",
                full_observed_at="observed",
                previous_observation_id=3,
                observation_id=4,
                unretained_values=(
                    ResearchEnrichmentFieldChange("plot", "Section A", None, 3, 4),
                ),
            )
        )

        rendered = "\n".join(output)
        assert "No value retained in the new observation" in rendered
        assert 'plot: earlier retained value "Section A"' in rendered
        assert "cannot distinguish not displayed, not collected" in rendered
        assert "A zero retained-link count does not by itself prove" in rendered

    def test_admin_aliases_commands_are_machine_readable(self, helpers, database):
        source = self.summary().save()
        graver.api.queue_memorials(database.name)

        recorded = helpers.graver_cli(
            f"admin aliases record {source.memorial_id} 999999 "
            f"--db '{database.name}' --type merged --reason reviewed"
        )
        listed = helpers.graver_cli(f"admin aliases list --db '{database.name}' --json")
        shown = helpers.graver_cli(
            f"admin aliases show {source.memorial_id} --db '{database.name}' --json"
        )
        retracted = helpers.graver_cli(
            f"admin aliases retract {source.memorial_id} --db '{database.name}' "
            "--reason correction"
        )

        assert all(
            result.exit_code == 0 for result in (recorded, listed, shown, retracted)
        )
        listed_json = json.loads(listed.output)
        shown_json = json.loads(shown.output)
        assert listed_json["command"] == "admin.aliases.list"
        assert listed_json["data"][0]["target_memorial_id"] == 999999
        assert shown_json["command"] == "admin.aliases.show"
        assert shown_json["data"]["canonical_memorial_id"] == 999999
        assert json.loads(recorded.output)["command"] == "admin.aliases.record"
        retracted_json = json.loads(retracted.output)
        assert retracted_json["command"] == "admin.aliases.retract"
        assert retracted_json["data"]["history"][-1]["event_type"] == "retracted"


class TestCliSearch(TestCli):
    def test_search_uses_a_finite_default_result_limit(
        self, helpers, tmp_path, monkeypatch
    ) -> None:
        """A live search is bounded even when the researcher omits the option."""
        database = tmp_path / "bounded.db"
        commands = []

        def search(_workspace, command, **_kwargs):
            commands.append(command)
            return AcquisitionReceipt(
                operation="search_memorial_summaries",
                source="fixture:bounded",
                memorial_ids=(),
                observations_appended=0,
                memorials_created=0,
                memorials_existing=0,
                changed_memorials=0,
                changes=(),
            )

        monkeypatch.setattr(WorkspaceAcquisition, "search", search)

        result = helpers.graver_cli(f"search --db '{database}' --memorial-id 1075")

        assert result.exit_code == 0
        assert commands[0].max_results == 20

    def test_search_cli_projects_the_workspace_receipt(
        self, helpers, tmp_path, monkeypatch
    ) -> None:
        """CLI arguments and output adapt the same typed application operation."""
        database = tmp_path / "parity.db"
        commands = []

        def search(_workspace, command, **_kwargs):
            commands.append(command)
            return AcquisitionReceipt(
                operation="search_memorial_summaries",
                source="fixture:parity",
                memorial_ids=(1075,),
                observations_appended=1,
                memorials_created=1,
                memorials_existing=0,
                changed_memorials=0,
                changes=(),
            )

        monkeypatch.setattr(WorkspaceAcquisition, "search", search)

        result = helpers.graver_cli(
            f"search --db '{database}' --memorial-id 1075 --max-results 1"
        )

        assert result.exit_code == 0
        assert len(commands) == 1
        assert commands[0].memorial_id == 1075
        assert commands[0].max_results == 1
        assert "1 new, 0 existing" in result.output
        assert "1 dated snapshot" in result.output

    def test_access_block_is_reported_without_traceback(
        self, helpers, tmp_path, monkeypatch
    ) -> None:
        database = tmp_path / "blocked.db"

        def blocked(*_args, **_kwargs):
            raise TransportAccessBlocked(
                "Find a Grave challenged access; stop for human review."
            )

        monkeypatch.setattr(Memorial, "search", blocked)

        result = helpers.graver_cli(f"search --db '{database}'")

        assert result.exit_code == 1
        assert "stop for human review" in result.output
        assert "Traceback" not in result.output

    def test_researcher_tutorial_workflow_is_offline(
        self,
        helpers,
        tmp_path,
        monkeypatch,
        isolate_graver_configuration,
    ) -> None:
        """Exercise the documented workflow without contacting Find a Grave."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("GRAVER_DB", raising=False)
        tutorial_database = (tmp_path / "tutorial.db").resolve()
        values = Test.load_memorial_from_json("george-washington")
        summary = MemorialSummary.from_dict(values)
        full = Memorial.from_dict(values)
        search_calls = []
        full_calls = []

        def mocked_search(*args, **kwargs):
            search_calls.append(kwargs)
            return [summary]

        def mocked_full_acquisition(url):
            full_calls.append(url)
            return full

        def unexpected_network(*_args, **_kwargs):
            pytest.fail("the tutorial workflow attempted an unexpected network call")

        monkeypatch.setattr(Memorial, "search", mocked_search)
        monkeypatch.setattr(Memorial, "parse", mocked_full_acquisition)
        monkeypatch.setattr(Driver, "get", unexpected_network)

        initialized = helpers.graver_cli("init tutorial.db")
        selected = helpers.graver_cli("use --show")
        searched = helpers.graver_cli("search --memorial-id 1075 --max-results 1")
        queued = helpers.graver_cli("work queue")
        listed = helpers.graver_cli("work list --limit 10")
        next_person = helpers.graver_cli("work next")
        initial = helpers.graver_cli("work show 1075 --json")
        refused = helpers.graver_cli("work enrich 1075")
        approved = helpers.graver_cli(
            "work mark 1075 --status ready_for_full_scrape "
            "--note 'Approved during the tutorial'"
        )
        approved_tasks = graver.api.list_research_tasks(
            str(tutorial_database),
            status="ready_for_full_scrape",
            cemetery_id=None,
            limit=20,
        )
        enriched = helpers.graver_cli("work enrich 1075")
        final = helpers.graver_cli("work show 1075 --json")

        assert all(
            result.exit_code == 0
            for result in (
                initialized,
                selected,
                searched,
                queued,
                listed,
                next_person,
                initial,
                approved,
                enriched,
                final,
            )
        )
        assert refused.exit_code == 1
        assert "not approved for enrichment" in refused.output
        assert str(tutorial_database) in initialized.output
        assert str(tutorial_database) in selected.output
        assert json.loads(isolate_graver_configuration.read_text())[
            "default_database"
        ] == str(tutorial_database)
        assert len(search_calls) == 1
        assert search_calls[0]["memorialid"] == "1075"
        assert search_calls[0]["max_results"] == 1
        assert "Added 1 person" in queued.output
        assert "1075 | George Washington" in listed.output
        assert "Person: George Washington" in next_person.output

        initial_record = json.loads(initial.output)["data"]
        assert initial_record["grave"]["detail_level"] == "summary"
        assert initial_record["task"]["status"] == "unprocessed"
        assert len(initial_record["observations"]) == 1
        assert initial_record["observations"][0]["acquisition_level"] == "summary"
        assert [task["memorial_id"] for task in approved_tasks] == [1075]
        assert full_calls == [summary.findagrave_url]

        final_record = json.loads(final.output)["data"]
        assert final_record["task"]["status"] == "full_scrape_complete"
        assert final_record["grave"]["detail_level"] == "full"
        assert final_record["grave"]["full_fetched_at"]
        assert final_record["grave"]["findagrave_url"] == summary.findagrave_url
        assert final_record["grave"]["cemetery_id"] == summary.cemetery_id
        assert [
            observation["acquisition_level"]
            for observation in final_record["observations"]
        ] == ["summary", "full"]
        assert all(
            observation["fetch_outcome"] == "success"
            for observation in final_record["observations"]
        )
        assert (
            sum(
                task["status"] == "full_scrape_complete"
                for task in graver.api.list_research_tasks(
                    str(tutorial_database), status=None, cemetery_id=None, limit=20
                )
            )
            == 1
        )

    def test_saves_results_to_specified_database(
        self, helpers, tmp_path, fake_memorial, monkeypatch
    ) -> None:
        expected = MemorialSummary.from_dict(fake_memorial().to_dict())
        assert isinstance(expected, MemorialSummary)
        database = tmp_path / "search.db"
        monkeypatch.setattr(Memorial, "search", lambda *args, **kwargs: [expected])

        result = helpers.graver_cli(f"search --db '{database}'")

        assert result.exit_code == 0
        with connect_database(database) as connection:
            row = connection.execute(
                "SELECT memorial_id, detail_level, summary_fetched_at "
                "FROM graves WHERE memorial_id = ?",
                (expected.memorial_id,),
            ).fetchone()
        assert row[0:2] == (expected.memorial_id, "summary")
        assert row[2].endswith("Z")

    def test_uses_specified_database(self, helpers, tmp_path, monkeypatch) -> None:
        database = tmp_path / "search.db"
        monkeypatch.setattr(Memorial, "search", lambda *args, **kwargs: [])

        result = helpers.graver_cli(f"search --db '{database}'")

        assert result.exit_code == 0
        assert database.exists()

    def test_current_search_fields_are_forwarded(self, helpers, monkeypatch) -> None:
        captured = {}

        def mock_search(*args, **kwargs):
            captured.update(kwargs)
            return []

        monkeypatch.setattr(Memorial, "search", mock_search)
        result = helpers.graver_cli(
            "search --memorial-id=123 --full-text='John Smith' --biography=married "
            "--tags='american revolutionary war' --birth-year-filter=unknown "
            "--death-year-filter=25 --date-filter=-90 --order-by=dc"
        )

        assert result.exit_code == 0
        assert captured["memorialid"] == "123"
        assert captured["fulltext"] == "John Smith"
        assert captured["bio"] == "married"
        assert captured["tags"] == "american revolutionary war"
        assert captured["birthyearfilter"] == "unknown"
        assert captured["deathyearfilter"] == "25"
        assert captured["datefilter"] == -90
        assert captured["orderby"] == "dc"

    @pytest.mark.parametrize(
        "option, field, expected",
        [
            ("--famous", "famous", True),
            ("--not-famous", "famous", False),
            ("--sponsored", "sponsored", True),
            ("--not-sponsored", "sponsored", False),
            ("--cenotaph", "cenotaph", True),
            ("--not-cenotaph", "cenotaph", False),
            ("--monument", "monument", True),
            ("--not-monument", "monument", False),
            ("--veteran", "isVeteran", True),
            ("--not-veteran", "isVeteran", False),
            ("--flowers", "flowers", True),
            ("--no-flowers", "flowers", False),
            ("--has-plot", "hasPlot", True),
            ("--no-plot", "hasPlot", False),
        ],
    )
    def test_tristate_search_flags_are_forwarded(
        self, helpers, monkeypatch, option, field, expected
    ):
        captured = {}

        def mock_search(*args, **kwargs):
            captured.update(kwargs)
            return []

        monkeypatch.setattr(Memorial, "search", mock_search)

        result = helpers.graver_cli(f"search {option}")

        assert result.exit_code == 0
        assert captured[field] is expected

    @pytest.mark.parametrize(
        "option",
        [
            "--id=1075",
            "--cid=1",
            "--max=1",
            "--firstname=Eleanor",
            "--locationId=1",
            "--isVeteran=true",
            "--exactName",
        ],
    )
    def test_removed_search_option_spellings_are_rejected(self, helpers, option):
        result = helpers.graver_cli(f"search {option}")

        assert result.exit_code == 2
        assert "No such option" in unstyle(result.output)

    @pytest.mark.parametrize(
        "cemetery_id, lastname, death_year", [(641417, "Jackson", 1828)]
    )
    def test_search_in_cemetery(
        self, cemetery_id, lastname, death_year, helpers, caplog, faker, monkeypatch
    ):
        max_results = 10

        def mock_search(*args, **kwargs):
            return faker.result_set(
                faker,
                "foobar",
                2,
                cemetery_id=cemetery_id,
                lastname=lastname,
                death_year=death_year,
            )

        monkeypatch.setattr(Memorial, "search", mock_search)

        class FakeCemetery:
            def __init__(self):
                self.cemetery_id = cemetery_id
                self.findagrave_url = (
                    f"https://www.findagrave.com/cemetery/{cemetery_id}"
                )
                self.name = "Fixture cemetery"
                self.location = "Fixture location"
                self.coords = ""

        monkeypatch.setattr(
            "graver.acquisition.legacy_api.Cemetery", lambda url: FakeCemetery()
        )
        command = (
            f"search --cemetery-id={cemetery_id} --last-name='{lastname}' "
            f"--death-year={death_year} --max-results={max_results}"
        )
        result = helpers.graver_cli(command)
        assert result.exit_code == 0
        assert "memorial summaries" in result.output
        assert "dated snapshots" in result.output

    @pytest.mark.parametrize("value", ["yes", "true"])
    def test_gpsfilter_callback(self, value, helpers):
        command = f"search --gps-filter={value}"
        result = helpers.graver_cli(command)
        assert result.exit_code == 2
        assert "Invalid value" in result.output

    @pytest.mark.parametrize("value", ["yes", "true"])
    def test_photofilter_callback(self, value, helpers):
        command = f"search --photo-filter={value}"
        result = helpers.graver_cli(command)
        assert result.exit_code == 2
        assert "Invalid value" in result.output

    @pytest.mark.parametrize("value", ["yes", "true"])
    def test_yearfilter_callback(self, value, helpers, caplog):
        command = f"search --birth-year=1856 --birth-year-filter={value}"
        result = helpers.graver_cli(command)
        assert result.exit_code == 2
        assert "Invalid value" in result.output

    @pytest.mark.parametrize("value", [0, 14, -30])
    def test_datefilter_callback(self, value, helpers):
        result = helpers.graver_cli(f"search --date-filter={value}")
        assert result.exit_code == 2
        assert "Invalid value" in result.output

    def test_orderby_callback(self, helpers):
        result = helpers.graver_cli("search --order-by=invalid")
        assert result.exit_code == 2
        assert "Invalid value" in result.output

    @pytest.mark.parametrize(
        "param",
        [
            "exact-name",
            "fuzzy-names",
        ],
    )
    def test_name_filter_callback(self, param, helpers, monkeypatch):
        monkeypatch.setattr(Memorial, "search", lambda *args, **kwargs: [])
        # Success case
        command = f"search --first-name=foo --{param} --max-results=5"
        result = helpers.graver_cli(command)
        assert result.exit_code == 0

        # Failure case
        command = f"search --{param} --max-results=5"
        result = helpers.graver_cli(command)
        assert result.exit_code == 2
        assert "Invalid value" in result.output
