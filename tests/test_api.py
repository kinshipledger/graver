import json
import logging
import re
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import requests
from bs4 import BeautifulSoup
from urllib3 import exceptions

import graver.api
import graver.database
from graver import (
    Cemetery,
    Driver,
    Memorial,
    MemorialAliasError,
    MemorialMergedException,
    MemorialParseException,
    MemorialRemovedException,
    MemorialSummary,
    ResearchTaskNotFound,
    alias_history,
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
from graver._sqlite import connect_database
from graver.research import (
    EnrichmentAliasBlocked,
    EnrichmentFailed,
    EnrichmentNotApproved,
    ResearchEnrichmentRequest,
    ResearchEnrichmentResult,
    ResearchInputError,
    ResearchQueueRequest,
    ResearchQueueResult,
    ResearchService,
    ResearchTaskDetail,
    ResearchTaskQuery,
    ResearchTaskRecord,
    ResearchTaskSummary,
    ResearchTaskUpdate,
)
from graver.transport import TransportRateLimited
from tests.test import Test

logging.getLogger().setLevel(logging.INFO)


class TestApi(Test):
    memorials = [
        "andrew-jackson",
        "carl-sagan",
        "dennis-macalistair-ritchie",
        "george-washington",
        "grace-brewster-hopper",
        "isaac-asimov",
        "john-j-pershing",
        "john-quincy-adams",
        "martin-luther-king",
        "rod-serling",
        "thomas-jefferson",
    ]

    famous_memorials = [
        "andrew-jackson",
        "carl-sagan",
        "george-washington",
        "grace-brewster-hopper",
        "isaac-asimov",
        "john-j-pershing",
        "martin-luther-king",
        "rod-serling",
        "thomas-jefferson",
    ]


class TestDriver(TestApi):
    @pytest.mark.parametrize(
        "headers, expected_sleep",
        [
            ({"Retry-After": "2"}, [2.0]),
            ({"Retry-After": "120"}, [60.0]),
            ({}, [0.02]),
        ],
    )
    def test_driver_retries_rate_limit_with_retry_after_or_backoff(
        self, requests_mock, monkeypatch, headers, expected_sleep
    ):
        url = "https://www.findagrave.com/memorial/429"
        sleeps = []
        monkeypatch.setattr(graver.api, "sleep", sleeps.append)
        requests_mock.get(
            url,
            [
                {"status_code": 429, "reason": "Too Many Requests", "headers": headers},
                {"status_code": 200, "reason": "OK"},
            ],
        )

        response = Driver(retry_ms=10, max_retries=1).get(url)

        assert response.status_code == 200
        assert sleeps == expected_sleep

    def test_driver_stops_after_repeated_rate_limits(self, requests_mock, monkeypatch):
        url = "https://www.findagrave.com/memorial/429"
        sleeps = []
        monkeypatch.setattr(graver.api, "sleep", sleeps.append)
        requests_mock.get(
            url,
            [
                {"status_code": 429, "reason": "Too Many Requests"},
                {"status_code": 429, "reason": "Too Many Requests"},
            ],
        )

        with pytest.raises(TransportRateLimited, match="human review"):
            Driver(retry_ms=10, max_retries=2).get(url)

        assert sleeps == [0.02]

    @pytest.mark.parametrize("url", ["https://www.findagrave.com/memorial/544"])
    @pytest.mark.parametrize(
        "status_code, reason",
        [
            (500, "Internal Server Error"),
            (502, "Bad Gateway"),
            (503, "Service Unavailable"),
            (504, "Gateway Timeout"),
            (599, "Network Connect Timeout Error"),
        ],
    )
    def test_driver_retries_recoverable_errors(
        self, url, status_code, reason, requests_mock
    ):
        requests_mock.get(
            url,
            [
                {"status_code": status_code, "reason": reason},
                {"status_code": 200, "reason": "None"},
            ],
        )
        driver = Driver(retry_ms=10, max_retries=1)
        response = driver.get(url)
        assert response.ok and response.status_code == 200
        assert driver.num_retries == 1

    @pytest.mark.parametrize(
        "url", ["https://www.findagrave.com/memorial/7/john-quincy-adams"]
    )
    def test_driver_unrecoverable_http_error(self, url, helpers, requests_mock):
        requests_mock.reset()
        requests_mock.get(
            url,
            [
                {"status_code": 403, "reason": "Forbidden"},
            ],
        )
        with pytest.raises(MemorialParseException, match="will not attempt to bypass"):
            Memorial.parse(url)

    @pytest.mark.parametrize(
        "url", ["https://www.findagrave.com/memorial/7/john-quincy-adams"]
    )
    def test_driver_unrecoverable_requests_error(
        self, url, helpers, caplog, requests_mock
    ):
        requests_mock.reset()
        requests_mock.get(
            url,
            exc=requests.exceptions.ConnectTimeout(
                exceptions.MaxRetryError(None, url, None), None
            ),
        )
        with pytest.raises(MemorialParseException, match="Request timed out"):
            Memorial.parse(url)


class TestMemorialParser(TestApi):
    @pytest.mark.parametrize(
        "name, memorial_link",
        [
            (
                "John Q. Public-Citizen",
                "/memorial/12345/john-q-public-citizen",
            ),
            (
                "Mary E. Smith-Johnson",
                "https://www.findagrave.com/memorial/101010101/mary-e-smith-johnson",
            ),
            (
                "Ann-Marie Smitherson",
                "https://www.findagrave.com/memorial/101010101/ann-marie-smitherson",
            ),
        ],
    )
    def test_get_prefix_suffix_with_compact_url_name(self, name, memorial_link):
        prefix, suffix = graver.api._MemorialParser.get_prefix_suffix(
            name,
            memorial_link,
        )

        assert prefix is None
        assert suffix is None


class TestMemorial(TestApi):
    pass

    @pytest.mark.parametrize(
        "html, expected",
        [
            (
                '<input type="hidden" id="addedDate" '
                'value="Added: 2012-10-07T15:26:53.000Z">',
                "2012-10-07T15:26:53.000Z",
            ),
            ("<html></html>", None),
        ],
    )
    def test_scrape_date_added(self, html, expected):
        parser = graver.api._MemorialParser(
            "https://www.findagrave.com/memorial/1/example",
            get=False,
            scrape=False,
        )
        parser.soup = BeautifulSoup(html, "html.parser")

        parser.scrape_date_added()

        assert parser.date_added == expected

    def test_memorial_not_equal_different_class(self):
        m = Memorial.from_dict(Test.load_memorial_from_json("james-fenimore-cooper"))
        assert m != str("A string object")

    @pytest.mark.parametrize("name", TestApi.memorials)
    def test_memorial_parse(self, name: str, driver):
        mem_dict = Test.load_memorial_from_json(name)
        m = Memorial.parse(mem_dict["findagrave_url"], driver=driver)
        assert isinstance(m, Memorial)
        expected_m = Memorial.from_dict(mem_dict)
        assert m == expected_m

    @pytest.mark.parametrize("name", TestApi.memorials)
    def test_memorial_from_dict(self, name: str):
        expected = Test.load_memorial_from_json(name)
        result = Memorial.from_dict(expected)
        assert result.memorial_id == expected["memorial_id"]
        assert result.findagrave_url == expected["findagrave_url"]
        if "prefix" in expected.keys():
            assert result.prefix == expected["prefix"]
        else:
            assert result.prefix is None
        assert result.name == expected["name"]
        if "suffix" in expected.keys():
            assert result.suffix == expected["suffix"]
        else:
            assert result.suffix is None
        assert result.maiden_name == expected["maiden_name"]
        assert result.original_name == expected["original_name"]
        assert result.famous == expected["famous"]
        assert result.veteran == expected["veteran"]
        assert result.birth == expected["birth"]
        assert result.birth_place == expected["birth_place"]
        assert result.death == expected["death"]
        assert result.death_place == expected["death_place"]
        assert result.memorial_type == expected["memorial_type"]
        assert result.plot == expected["plot"]
        assert result.coords == expected["coords"]
        assert result.has_bio == expected["has_bio"]
        assert result.date_added == expected["date_added"]

    @pytest.mark.parametrize("name", TestApi.memorials)
    def test_memorial_to_dict(self, name: str):
        expected = Test.load_memorial_from_json(name)
        m = Memorial.from_dict(expected)
        result = m.to_dict()
        assert result["memorial_id"] == expected["memorial_id"]
        assert result["findagrave_url"] == expected["findagrave_url"]
        assert result["prefix"] == expected["prefix"]
        assert result["name"] == expected["name"]
        assert result["suffix"] == expected["suffix"]
        assert result["nickname"] == expected["nickname"]
        if "maiden_name" in expected:
            assert "maiden_name" in result
            assert result["maiden_name"] == expected["maiden_name"]
        assert result["original_name"] == expected["original_name"]
        assert result["famous"] == expected["famous"]
        assert result["veteran"] == expected["veteran"]
        assert result["birth"] == expected["birth"]
        assert result["birth_place"] == expected["birth_place"]
        assert result["death"] == expected["death"]
        assert result["death_place"] == expected["death_place"]
        assert result["memorial_type"] == expected["memorial_type"]
        assert result["burial_place"] == expected["burial_place"]
        assert result["cemetery_id"] == expected["cemetery_id"]
        assert result["plot"] == expected["plot"]
        assert result["coords"] == expected["coords"]
        assert result["has_bio"] == expected["has_bio"]
        assert result["date_added"] == expected["date_added"]

    @pytest.mark.parametrize("name", TestApi.memorials)
    def test_memorial_to_json(self, name):
        d = Test.load_memorial_from_json(name)
        m1 = Memorial.from_dict(d)
        json_str = m1.to_json()
        m2 = Memorial.from_dict(json.loads(json_str))
        assert m2 == m1

    def test_parser_captures_displayed_relationship_links_without_inference(self):
        parser = graver.api._MemorialParser(
            "https://www.findagrave.com/memorial/1075/george-washington",
            get=False,
            scrape=False,
        )
        parser.soup = BeautifulSoup(
            """
            <div class="overview-panel data-family">
              <b class="label-relation">Spouse</b>
              <ul class="member-family">
                <li>
                  <a href="/memorial/2382/martha-washington">
                    <h3 itemprop="name">Martha Dandridge Washington</h3>
                    <p class="life"><span itemprop="birthDate">1731</span> –
                      <span itemprop="deathDate">1802</span> (m. 1759)</p>
                  </a>
                </li>
              </ul>
            </div>
            """,
            "html.parser",
        )

        parser.scrape_related_memorials()

        assert len(parser.findagrave_displayed_relationship_links) == 1
        observed = parser.findagrave_displayed_relationship_links[0]
        assert observed.displayed_group == "Spouse"
        assert observed.memorial_id == 2382
        assert (
            observed.url == "https://www.findagrave.com/memorial/2382/martha-washington"
        )
        assert observed.name == "Martha Dandridge Washington"
        assert observed.birth_text == "1731"
        assert observed.death_text == "1802"
        assert observed.marriage_year == "1759"

    @pytest.mark.parametrize(
        "url",
        [
            "https://www.findagrave.com/memorial/should-produce-404",
        ],
    )
    def test_memorial_parse_raises_exception_on_unexpected_404(
        self, url, helpers, tmp_path, caplog, driver
    ):
        with pytest.raises(
            MemorialParseException, match=f"404 Client Error: Not Found for url: {url}"
        ):
            Memorial.parse(url, driver=driver)

    @pytest.mark.parametrize(
        "requested_url, new_url",
        [
            (
                "https://www.findagrave.com/memorial/244781332/william-h-boekholder",
                "https://www.findagrave.com/memorial/260829715/wiliam-henry-boekholder",
            )
        ],
    )
    def test_memorial_parser_merged_raises_exception(
        self, requested_url, new_url, driver
    ):
        with pytest.raises(
            MemorialMergedException,
            match=f"{requested_url} has been merged into {new_url}",
        ) as ex_info:
            Memorial.parse(requested_url, driver=driver)
        assert ex_info.value.new_url == new_url

    @pytest.mark.parametrize(
        "findagrave_url",
        [
            "https://www.findagrave.com/memorial/261491035/dolores-higginbotham",
        ],
    )
    def test_memorial_parser_removed_raises_exception(self, findagrave_url, driver):
        with pytest.raises(MemorialRemovedException, match="has been removed"):
            Memorial.parse(findagrave_url, driver=driver)


class TestCemetery(TestApi):
    def test_not_equal_different_class(self):
        m = Cemetery.from_dict(Test.load_cemetery_from_json("monticello-graveyard"))
        assert m != str("A string object")

    @pytest.mark.parametrize(
        "expected",
        [
            Test.load_cemetery_from_json("arlington-national-cemetery"),
            Test.load_cemetery_from_json("crown-hill-memorial-park"),
            Test.load_cemetery_from_json("monticello-graveyard"),
        ],
    )
    def test_cemetery_from_dict(self, expected: dict):
        cem = Cemetery.from_dict(expected)
        assert isinstance(cem, Cemetery)
        assert cem.cemetery_id == expected["cemetery_id"]
        assert cem.findagrave_url == expected["findagrave_url"]
        assert cem.name == expected["name"]
        assert cem.location == expected["location"]
        assert cem.coords == expected["coords"]

    @pytest.mark.parametrize(
        "expected",
        [
            Test.load_cemetery_from_json("arlington-national-cemetery"),
            Test.load_cemetery_from_json("crown-hill-memorial-park"),
            Test.load_cemetery_from_json("monticello-graveyard"),
        ],
    )
    def test_cemetery_to_dict(self, expected: dict):
        c: Cemetery = Cemetery.from_dict(expected)
        assert isinstance(c, Cemetery)
        result = c.to_dict()
        assert result["cemetery_id"] == expected["cemetery_id"]
        assert result["findagrave_url"] == expected["findagrave_url"]
        assert result["name"] == expected["name"]
        assert result["location"] == expected["location"]
        assert result["coords"] == expected["coords"]
        assert result["num_memorials"] == expected["num_memorials"]

    @pytest.mark.parametrize(
        "expected",
        [
            Test.load_cemetery_from_json("crown-hill-memorial-park"),
        ],
    )
    def test_cemetery(self, expected, driver):
        url = expected["findagrave_url"]
        expected_cem = Cemetery.from_dict(expected)
        cem = Cemetery(url, driver=driver)
        assert cem == expected_cem
        assert cem.cemetery_id == expected["cemetery_id"]
        assert cem.name == expected["name"]
        assert cem.findagrave_url == expected["findagrave_url"]
        assert cem.location == expected["location"]
        assert cem.coords == expected["coords"]


class TestDatabaseOps(TestApi):
    def test_explicit_upgrade_migrates_additive_columns(self, tmp_path):
        database_name = tmp_path / "legacy.db"
        with connect_database(database_name) as connection:
            connection.execute("""CREATE TABLE graves (
                    memorial_id INTEGER PRIMARY KEY, findagrave_url TEXT,
                    name TEXT, birth TEXT, death TEXT, original_name TEXT,
                    birth_place TEXT, death_place TEXT, has_bio BOOL
                )""")
            connection.executemany(
                "INSERT INTO graves (memorial_id) VALUES (?)", [(123,), (456,), (789,)]
            )

        graver.database.upgrade_database(str(database_name))

        with connect_database(database_name) as connection:
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(graves)").fetchall()
            }
            row = connection.execute(
                "SELECT COUNT(*), COUNT(DISTINCT memorial_id), "
                "COUNT(detail_level), COUNT(summary_fetched_at), "
                "COUNT(full_fetched_at) FROM graves"
            ).fetchone()
        assert {
            "date_added",
            "detail_level",
            "summary_fetched_at",
            "full_fetched_at",
        } <= columns
        assert row == (3, 3, 0, 0, 0)

    def test_research_tables_indexes_constraints_and_foreign_keys(self, tmp_path):
        database_name = tmp_path / "research.db"

        Memorial.create_table(str(database_name))

        with graver.api._connect(str(database_name)) as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            indexes = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'index'"
                )
            }
            triggers = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'trigger'"
                )
            }
            foreign_keys_enabled = connection.execute("PRAGMA foreign_keys").fetchone()[
                0
            ]
            observation_foreign_keys = {
                row[2]
                for row in connection.execute(
                    "PRAGMA foreign_key_list(memorial_observations)"
                ).fetchall()
            }
            cemetery_columns = {
                row[1]
                for row in connection.execute(
                    "PRAGMA table_info(cemeteries)"
                ).fetchall()
            }
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute("""INSERT INTO research_tasks (
                        subject_id, status, priority, created_at, updated_at,
                        last_activity_at
                    ) VALUES ('00000000-0000-4000-8000-000000000000',
                              'unprocessed', 0, 'now', 'now', 'now')""")
            connection.execute("""INSERT INTO research_subjects (subject_id, created_at)
                   VALUES ('00000000-0000-4000-8000-000000000001', 'now')""")
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute("""INSERT INTO research_tasks (
                        subject_id, status, priority, created_at, updated_at,
                        last_activity_at
                    ) VALUES ('00000000-0000-4000-8000-000000000001',
                              'invalid', 0, 'now', 'now', 'now')""")

        assert {
            "graves",
            "cemeteries",
            "memorial_observations",
            "research_tasks",
        } <= tables
        assert {
            "idx_graves_cemetery_id",
            "idx_memorial_observations_memorial_id",
            "idx_memorial_observations_cemetery_id",
            "idx_research_tasks_status_priority",
        } <= indexes
        assert {
            "memorial_observations_no_update",
            "memorial_observations_no_delete",
        } <= triggers
        assert foreign_keys_enabled == 1
        assert observation_foreign_keys == {"graves", "cemeteries"}
        assert {
            "cemetery_id",
            "url",
            "name",
            "location",
            "coords",
            "first_observed_at",
            "last_observed_at",
        } <= cemetery_columns

    def test_cemetery_save_preserves_first_observed_timestamp(
        self, tmp_path, monkeypatch
    ):
        database_name = tmp_path / "cemetery.db"
        timestamps = iter(["first", "last"])
        monkeypatch.setattr(graver.api, "_utc_now_iso", lambda: next(timestamps))
        cemetery = Cemetery.from_dict(
            {
                "cemetery_id": 10,
                "findagrave_url": "https://www.findagrave.com/cemetery/10/example",
                "name": "Original name",
                "location": "Original location",
                "coords": "1,2",
                "num_memorials": 3,
            }
        )
        cemetery.save(str(database_name))
        cemetery.name = "Updated name"
        cemetery.save(str(database_name))

        with connect_database(database_name) as connection:
            row = connection.execute(
                "SELECT name, first_observed_at, last_observed_at FROM cemeteries"
            ).fetchone()
        assert row == ("Updated name", "first", "last")

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

    def test_new_summary_records_detail_level_and_timestamp(self, database):
        summary = self.summary().save()

        with connect_database(database.name) as connection:
            row = connection.execute(
                "SELECT detail_level, summary_fetched_at, full_fetched_at "
                "FROM graves WHERE memorial_id = ?",
                (summary.memorial_id,),
            ).fetchone()
            observation = connection.execute(
                """SELECT memorial_id, cemetery_id, acquisition_level,
                          observed_at, fetch_outcome, parser_version, payload_json
                   FROM memorial_observations"""
            ).fetchone()
        assert row[0] == "summary"
        assert row[1].endswith("Z")
        assert row[2] is None
        assert observation[0:3] == (
            summary.memorial_id,
            summary.cemetery_id,
            "summary",
        )
        assert observation[3].endswith("Z")
        assert observation[4] == "success"
        assert observation[5]
        assert json.loads(observation[6]) == summary.to_dict()
        with connect_database(database.name) as connection:
            cemetery = connection.execute(
                """SELECT cemetery_id, url, name, first_observed_at,
                          last_observed_at FROM cemeteries"""
            ).fetchone()
        assert cemetery[0:3] == (summary.cemetery_id, None, None)
        assert cemetery[3] == cemetery[4] == observation[3]

    def test_new_full_save_creates_full_observation(self, database):
        full = self.full(
            findagrave_displayed_relationship_links=[
                {
                    "displayed_group": "Spouse",
                    "memorial_id": 2382,
                    "url": "https://www.findagrave.com/memorial/2382/martha-washington",
                    "name": "Martha Dandridge Washington",
                    "life_text": "1731 – 1802 (m. 1759)",
                    "birth_text": "1731",
                    "death_text": "1802",
                    "marriage_year": "1759",
                }
            ]
        ).save()

        with connect_database(database.name) as connection:
            observation = connection.execute("""SELECT acquisition_level, payload_json
                   FROM memorial_observations""").fetchone()
        assert observation[0] == "full"
        assert json.loads(observation[1]) == full.to_dict()
        assert (
            json.loads(observation[1])["findagrave_displayed_relationship_links"][0][
                "displayed_group"
            ]
            == "Spouse"
        )

    def test_repeated_acquisitions_create_immutable_observations(self, database):
        summary = self.summary(name="first observation")
        summary.save()
        self.summary(name="second observation").save()

        with connect_database(database.name) as connection:
            observations = connection.execute("""SELECT observation_id, payload_json
                   FROM memorial_observations ORDER BY observation_id""").fetchall()
        assert len(observations) == 2
        assert observations[0][0] != observations[1][0]
        assert json.loads(observations[0][1])["name"] == "first observation"
        assert json.loads(observations[1][1])["name"] == "second observation"
        with connect_database(database.name) as connection:
            with pytest.raises(
                sqlite3.IntegrityError, match="memorial observations are immutable"
            ):
                connection.execute(
                    "UPDATE memorial_observations SET fetch_outcome = 'changed'"
                )
            with pytest.raises(
                sqlite3.IntegrityError, match="memorial observations are immutable"
            ):
                connection.execute("DELETE FROM memorial_observations")

    def test_observation_failure_rolls_back_grave_upsert(self, database):
        summary = self.summary(name="preserved name")
        summary.save()
        with connect_database(database.name) as connection:
            connection.execute("""CREATE TRIGGER fail_observation
                   BEFORE INSERT ON memorial_observations
                   BEGIN
                       SELECT RAISE(FAIL, 'observation failed');
                   END""")

        with pytest.raises(sqlite3.IntegrityError, match="observation failed"):
            self.summary(name="rolled back name").save()

        with connect_database(database.name) as connection:
            grave_name = connection.execute(
                "SELECT name FROM graves WHERE memorial_id = ?",
                (summary.memorial_id,),
            ).fetchone()[0]
            observation_count = connection.execute(
                "SELECT COUNT(*) FROM memorial_observations"
            ).fetchone()[0]
        assert grave_name == "preserved name"
        assert observation_count == 1

    def test_queueing_filters_and_is_idempotent(self, database):
        summaries = [
            self.summary(cemetery_id=10),
            self.summary("carl-sagan", cemetery_id=10),
            self.summary("george-washington", cemetery_id=20),
        ]
        for summary in summaries:
            summary.save()

        assert queue_memorials(database.name, cemetery_id=10, priority=7) == (2, 0)
        with connect_database(database.name) as connection:
            connection.execute(
                """UPDATE research_tasks SET status = 'researching', owner = 'owner',
                   priority = 99, review_note = 'keep', updated_at = 'updated',
                   last_activity_at = 'active' WHERE subject_id =
                   (SELECT subject_id FROM subject_memorials WHERE memorial_id = ?)""",
                (summaries[0].memorial_id,),
            )
            preserved = connection.execute(
                """SELECT * FROM research_tasks WHERE subject_id =
                   (SELECT subject_id FROM subject_memorials WHERE memorial_id = ?)""",
                (summaries[0].memorial_id,),
            ).fetchone()

        assert queue_memorials(database.name, cemetery_id=10, priority=1) == (0, 2)
        assert queue_memorials(database.name, priority=3) == (1, 2)

        with connect_database(database.name) as connection:
            task_count = connection.execute(
                "SELECT COUNT(*) FROM research_tasks"
            ).fetchone()[0]
            after = connection.execute(
                """SELECT * FROM research_tasks WHERE subject_id =
                   (SELECT subject_id FROM subject_memorials WHERE memorial_id = ?)""",
                (summaries[0].memorial_id,),
            ).fetchone()
        assert task_count == 3
        assert after == preserved

    def test_list_tasks_filters_orders_and_defaults_to_twenty(self, database):
        with connect_database(database.name) as connection:
            connection.executemany(
                "INSERT INTO graves (memorial_id, name, cemetery_id) VALUES (?, ?, ?)",
                [
                    (number, f"Person {number}", 10 if number < 22 else 20)
                    for number in range(1, 26)
                ],
            )
            for number in range(1, 26):
                graver.api._ensure_subject_for_memorial(connection, number, "fixture")
        queue_memorials(database.name)
        with connect_database(database.name) as connection:
            connection.execute(
                """UPDATE research_tasks SET status = 'researching' WHERE subject_id =
                   (SELECT subject_id FROM subject_memorials WHERE memorial_id = 1)"""
            )
            connection.execute(
                """UPDATE research_tasks SET priority = 5, last_activity_at = 'later'
                   WHERE subject_id = (SELECT subject_id FROM subject_memorials
                                       WHERE memorial_id = 3)"""
            )
            connection.execute(
                """UPDATE research_tasks SET priority = 5, last_activity_at = 'earlier'
                   WHERE subject_id = (SELECT subject_id FROM subject_memorials
                                       WHERE memorial_id = 2)"""
            )

        tasks = list_research_tasks(database.name)
        filtered = list_research_tasks(
            database.name, status="unprocessed", cemetery_id=20, limit=10
        )

        assert len(tasks) == 20
        assert [task["memorial_id"] for task in tasks[:2]] == [2, 3]
        assert [task["memorial_id"] for task in filtered] == [22, 23, 24, 25]
        assert list(tasks[0]) == [
            "memorial_id",
            "name",
            "birth",
            "death",
            "cemetery_id",
            "detail_level",
            "status",
            "priority",
            "owner",
            "last_activity_at",
            "alias_target_id",
            "alias_status",
            "alias_canonical_id",
            "alias_path",
        ]

    def test_subject_service_preserves_compatibility_api_projection(self, database):
        summary = self.summary().save()
        service = ResearchService(database.name)

        assert service.queue_memorials(priority=4) == (1, 0)
        assert queue_memorials(database.name, priority=9) == (0, 1)
        assert service.list_tasks() == list_research_tasks(database.name)
        assert service.show_task(summary.memorial_id) == show_research_task(
            database.name, summary.memorial_id
        )

        updated = service.update_task(summary.memorial_id, status="researching")

        assert updated == show_research_task(database.name, summary.memorial_id)["task"]
        assert updated["memorial_id"] == summary.memorial_id
        assert "subject_id" not in updated

    def test_subject_service_exposes_typed_queries_and_updates(self, database):
        summary = self.summary().save()
        service = ResearchService(database.name)
        service.queue_memorials(priority=4)

        tasks = service.query_tasks(ResearchTaskQuery(limit=1))
        detail = service.get_task(summary.memorial_id)
        updated = service.apply_task_update(
            ResearchTaskUpdate(summary.memorial_id, status="researching")
        )

        assert isinstance(tasks, tuple)
        assert isinstance(tasks[0], ResearchTaskSummary)
        assert tasks[0].memorial_id == summary.memorial_id
        assert isinstance(detail, ResearchTaskDetail)
        assert isinstance(detail.task, ResearchTaskRecord)
        assert detail.task.subject_id
        assert detail.task.memorial_id == summary.memorial_id
        assert updated.status == "researching"
        assert updated.subject_id == detail.task.subject_id
        assert "subject_id" not in detail.to_compatibility_dict()["task"]

    def test_subject_service_rolls_back_if_updated_task_disappears(
        self, database, monkeypatch
    ):
        summary = self.summary().save()
        service = ResearchService(database.name)
        service.queue_memorials()
        monkeypatch.setattr(
            "graver.research._ResearchTaskRepository.task_for_subject",
            lambda _connection, _subject_id: None,
        )

        with pytest.raises(ResearchTaskNotFound, match="disappeared during update"):
            service.apply_task_update(
                ResearchTaskUpdate(summary.memorial_id, status="researching")
            )

        assert service.get_task(summary.memorial_id).task.status == "unprocessed"

    def test_subject_service_exposes_typed_queue_result(self, database):
        self.summary().save()
        service = ResearchService(database.name)

        first = service.queue_research(ResearchQueueRequest(priority=4))
        second = service.queue_research(ResearchQueueRequest(priority=9))

        assert first == ResearchQueueResult(created=1, existing=0)
        assert second == ResearchQueueResult(created=0, existing=1)
        assert service.queue_memorials(priority=9) == (0, 1)

    def test_typed_enrichment_validates_before_acquisition(self, database):
        summary = self.summary().save()
        service = ResearchService(database.name)
        service.queue_research(ResearchQueueRequest())
        calls = []

        with pytest.raises(EnrichmentNotApproved):
            service.enrich_memorial(
                ResearchEnrichmentRequest(summary.memorial_id),
                acquire=lambda url: calls.append(url),
            )

        assert calls == []

    def test_typed_enrichment_returns_result_and_preserves_projection(self, database):
        summary = self.summary().save()
        service = ResearchService(database.name)
        service.queue_research(ResearchQueueRequest())
        service.apply_task_update(
            ResearchTaskUpdate(summary.memorial_id, status="ready_for_full_scrape")
        )

        result = service.enrich_memorial(
            ResearchEnrichmentRequest(summary.memorial_id),
            acquire=lambda _url: self.full(),
        )

        assert isinstance(result, ResearchEnrichmentResult)
        assert result.memorial_id == summary.memorial_id
        assert result.status == "full_scrape_complete"
        assert result.to_compatibility_dict() == {
            "memorial_id": summary.memorial_id,
            "status": "full_scrape_complete",
            "full_observed_at": result.full_observed_at,
        }

    def test_typed_enrichment_records_failure_and_known_alias_blocks_network(
        self, database
    ):
        summary = self.summary().save()
        service = ResearchService(database.name)
        service.queue_research(ResearchQueueRequest())
        service.apply_task_update(
            ResearchTaskUpdate(summary.memorial_id, status="ready_for_full_scrape")
        )

        with pytest.raises(EnrichmentFailed, match="mock failure"):
            service.enrich_memorial(
                ResearchEnrichmentRequest(summary.memorial_id),
                acquire=lambda _url: (_ for _ in ()).throw(
                    MemorialParseException("mock failure")
                ),
            )
        record_memorial_alias(
            database.name,
            summary.memorial_id,
            999999,
            "merged",
            reason="fixture",
        )
        calls = []
        with pytest.raises(EnrichmentAliasBlocked):
            service.enrich_memorial(
                ResearchEnrichmentRequest(summary.memorial_id),
                acquire=lambda url: calls.append(url),
            )

        shown = service.get_task(summary.memorial_id)
        assert calls == []
        assert shown.task.status == "ready_for_full_scrape"
        assert shown.observations[-1]["fetch_outcome"] == "failure"

    @pytest.mark.parametrize(
        "request_factory, message",
        [
            (lambda: ResearchTaskQuery(status="invalid"), "Invalid task status"),
            (lambda: ResearchTaskQuery(limit=0), "Limit must be at least 1"),
            (
                lambda: ResearchTaskUpdate(1075),
                "At least one task change is required",
            ),
            (
                lambda: ResearchTaskUpdate(1075, status="invalid"),
                "Invalid task status",
            ),
        ],
    )
    def test_typed_research_requests_validate_at_the_boundary(
        self, request_factory, message
    ):
        with pytest.raises(ResearchInputError, match=message):
            request_factory()

    def test_show_task_includes_cemetery_and_chronological_observations(
        self, database, monkeypatch
    ):
        timestamps = iter(["second", "first", "queue"])
        monkeypatch.setattr(graver.api, "_utc_now_iso", lambda: next(timestamps))
        summary = self.summary()
        summary.save()
        self.summary(name="later acquisition").save()
        queue_memorials(database.name)
        cemetery = Cemetery.from_dict(
            {
                "cemetery_id": summary.cemetery_id,
                "findagrave_url": "https://example.test/cemetery",
                "name": "Observed cemetery",
                "location": "A place",
                "coords": "1,2",
                "num_memorials": 1,
            }
        )
        monkeypatch.setattr(graver.api, "_utc_now_iso", lambda: "third")
        cemetery.save(database.name)

        result = show_research_task(database.name, summary.memorial_id)

        assert result["task"]["memorial_id"] == summary.memorial_id
        assert result["grave"]["name"] == "later acquisition"
        assert result["cemetery"]["name"] == "Observed cemetery"
        assert [item["observed_at"] for item in result["observations"]] == [
            "first",
            "second",
        ]
        assert result["observations"][0]["payload"]["name"] == "later acquisition"

    def test_show_task_distinguishes_missing_memorial_and_task(self, database):
        with pytest.raises(graver.api.NotFound, match="Memorial 999"):
            show_research_task(database.name, 999)
        with connect_database(database.name) as connection:
            connection.execute("INSERT INTO graves (memorial_id) VALUES (999)")
            graver.api._ensure_subject_for_memorial(connection, 999, "fixture")
        with pytest.raises(ResearchTaskNotFound, match="Research task 999"):
            show_research_task(database.name, 999)

    def test_partial_and_noop_task_updates(self, database, monkeypatch):
        summary = self.summary()
        summary.save()
        queue_memorials(database.name, priority=7)
        with connect_database(database.name) as connection:
            connection.execute(
                """UPDATE research_tasks SET owner = 'owner', review_note = 'keep',
                   updated_at = 'old-update', last_activity_at = 'old-activity'"""
            )
        monkeypatch.setattr(graver.api, "_utc_now_iso", lambda: "new-time")

        changed = update_research_task(
            database.name, summary.memorial_id, status="researching"
        )
        noop = update_research_task(
            database.name, summary.memorial_id, status="researching"
        )

        with connect_database(database.name) as connection:
            task_events = connection.execute(
                """SELECT event_type, before_json, after_json
                   FROM research_task_events ORDER BY event_id"""
            ).fetchall()

        assert changed["priority"] == 7
        assert changed["owner"] == "owner"
        assert changed["review_note"] == "keep"
        assert changed["updated_at"] == changed["last_activity_at"] == "new-time"
        assert noop == changed
        assert [event[0] for event in task_events] == ["task_created", "task_updated"]
        assert json.loads(task_events[-1][1])["status"] == "unprocessed"
        assert json.loads(task_events[-1][2])["status"] == "researching"
        with pytest.raises(ValueError, match="Invalid task status"):
            update_research_task(
                database.name, summary.memorial_id, status="not-a-status"
            )

    def test_successful_task_scrape_is_atomic_and_preserves_task_fields(
        self, database, monkeypatch
    ):
        summary = self.summary(name="summary name")
        summary.save()
        queue_memorials(database.name, priority=8)
        with connect_database(database.name) as connection:
            connection.execute(
                """UPDATE research_tasks SET status = 'ready_for_full_scrape',
                   owner = 'owner', review_note = 'note'"""
            )
        monkeypatch.setattr(graver.api, "_utc_now_iso", lambda: "full-time")

        result = save_completed_task_scrape(
            database.name, summary.memorial_id, self.full(name="full name")
        )

        shown = show_research_task(database.name, summary.memorial_id)
        assert result == {
            "memorial_id": summary.memorial_id,
            "status": "full_scrape_complete",
            "full_observed_at": "full-time",
        }
        assert shown["grave"]["name"] == "full name"
        assert shown["task"]["status"] == "full_scrape_complete"
        assert shown["task"]["priority"] == 8
        assert shown["task"]["owner"] == "owner"
        assert shown["task"]["review_note"] == "note"
        assert shown["observations"][-1]["acquisition_level"] == "full"

    def test_failed_task_scrape_records_observation_without_changing_grave(
        self, database, monkeypatch
    ):
        summary = self.summary(name="preserved")
        summary.save()
        queue_memorials(database.name, priority=9)
        with connect_database(database.name) as connection:
            connection.execute(
                """UPDATE research_tasks SET status = 'ready_for_full_scrape',
                   owner = 'owner', review_note = 'human note'"""
            )
        monkeypatch.setattr(graver.api, "_utc_now_iso", lambda: "failure-time")

        record_failed_task_scrape(
            database.name,
            summary.memorial_id,
            summary.findagrave_url,
            MemorialParseException("concise failure"),
        )

        shown = show_research_task(database.name, summary.memorial_id)
        failure = shown["observations"][-1]
        assert shown["grave"]["name"] == "preserved"
        assert shown["task"]["status"] == "ready_for_full_scrape"
        assert shown["task"]["priority"] == 9
        assert shown["task"]["owner"] == "owner"
        assert shown["task"]["review_note"] == "human note"
        assert failure["fetch_outcome"] == "failure"
        assert failure["payload"] == {
            "attempted_url": summary.findagrave_url,
            "exception_type": "MemorialParseException",
            "error_message": "concise failure",
        }

    def test_full_save_upgrades_summary_and_preserves_timestamp(
        self, database, monkeypatch
    ):
        timestamps = iter(
            ["2026-01-01T00:00:00.000000Z", "2026-01-02T00:00:00.000000Z"]
        )
        monkeypatch.setattr(graver.api, "_utc_now_iso", lambda: next(timestamps))
        summary = self.summary()

        summary.save()
        self.full().save()

        with connect_database(database.name) as connection:
            row = connection.execute(
                "SELECT detail_level, summary_fetched_at, full_fetched_at "
                "FROM graves WHERE memorial_id = ?",
                (summary.memorial_id,),
            ).fetchone()
        assert row == (
            "full",
            "2026-01-01T00:00:00.000000Z",
            "2026-01-02T00:00:00.000000Z",
        )

    def test_summary_does_not_downgrade_or_clear_full_fields(
        self, database, monkeypatch
    ):
        timestamps = iter(["full-time", "summary-time"])
        monkeypatch.setattr(graver.api, "_utc_now_iso", lambda: next(timestamps))
        full = self.full(original_name="full original", coords="1.0,2.0")
        full.save()

        self.summary(name="refreshed summary").save()

        with connect_database(database.name) as connection:
            row = connection.execute(
                "SELECT detail_level, name, original_name, coords, "
                "summary_fetched_at, full_fetched_at FROM graves "
                "WHERE memorial_id = ?",
                (full.memorial_id,),
            ).fetchone()
        assert row == (
            "full",
            "refreshed summary",
            "full original",
            "1.0,2.0",
            "summary-time",
            "full-time",
        )

    def test_repeated_summary_refreshes_fields_and_timestamp(
        self, database, monkeypatch
    ):
        timestamps = iter(["summary-one", "summary-two"])
        monkeypatch.setattr(graver.api, "_utc_now_iso", lambda: next(timestamps))
        self.summary(name="old summary").save()

        summary = self.summary(name="new summary", plot="new plot").save()

        with connect_database(database.name) as connection:
            row = connection.execute(
                "SELECT name, plot, detail_level, summary_fetched_at "
                "FROM graves WHERE memorial_id = ?",
                (summary.memorial_id,),
            ).fetchone()
        assert row == ("new summary", "new plot", "summary", "summary-two")

    def test_repeated_full_save_refreshes_complete_fields_and_timestamp(
        self, database, monkeypatch
    ):
        timestamps = iter(["full-one", "full-two"])
        monkeypatch.setattr(graver.api, "_utc_now_iso", lambda: next(timestamps))
        self.full(original_name="old original", coords="1.0,2.0").save()

        full = self.full(original_name=None, coords=None).save()

        with connect_database(database.name) as connection:
            row = connection.execute(
                "SELECT original_name, coords, detail_level, full_fetched_at "
                "FROM graves WHERE memorial_id = ?",
                (full.memorial_id,),
            ).fetchone()
        assert row == (None, None, "full", "full-two")

    @pytest.mark.parametrize("name", TestApi.memorials)
    def test_memorial_save(self, name: str, database):
        expected = Test.load_memorial_from_json(name)
        result = Memorial.from_dict(expected).save()
        assert result.memorial_id == expected["memorial_id"]
        assert result.findagrave_url == expected["findagrave_url"]
        assert result.name == expected["name"]
        assert result.original_name == expected["original_name"]
        assert result.birth == expected["birth"]
        assert result.birth_place == expected["birth_place"]
        assert result.death == expected["death"]
        assert result.death_place == expected["death_place"]
        assert result.memorial_type == expected["memorial_type"]
        assert result.plot == expected["plot"]
        assert result.coords == expected["coords"]
        assert result.has_bio == expected["has_bio"]
        assert result.date_added == expected["date_added"]

    @pytest.mark.parametrize("name", TestApi.memorials)
    def test_memorial_get_by_id(self, name: str, database):
        expected = Test.load_memorial_from_json(name)
        mid: int = expected["memorial_id"]
        expected_memorial = Memorial.from_dict(expected).save()
        result: Memorial = Memorial.get_by_id(mid)
        assert result == expected_memorial

    @pytest.mark.parametrize("memorial_id", [99999, -12345])
    def test_memorial_by_id_not_found(self, memorial_id, database):
        with pytest.raises(graver.api.NotFound):
            Memorial.get_by_id(memorial_id)


class TestMemorialAliases:
    @staticmethod
    def summary(fixture_name="andrew-jackson", **updates):
        values = Test.load_memorial_from_json(fixture_name)
        values.update(updates)
        return MemorialSummary.from_dict(values)

    def test_schema_constraints_foreign_keys_indexes_and_triggers(self, database):
        with connect_database(database.name) as connection:
            tables = {
                r[0]
                for r in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            indexes = {
                r[0]
                for r in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='index'"
                )
            }
            triggers = {
                r[0]
                for r in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='trigger'"
                )
            }
            foreign_keys = connection.execute(
                "PRAGMA foreign_key_list(memorial_aliases)"
            ).fetchall()
        assert {"memorial_aliases", "memorial_alias_observations"} <= tables
        assert "idx_memorial_aliases_target_status" in indexes
        assert {
            "memorial_alias_observations_no_update",
            "memorial_alias_observations_no_delete",
        } <= triggers
        assert any(row[2] == "graves" for row in foreign_keys)

    def test_observe_change_retract_reactivate_and_history(self, database, monkeypatch):
        source = self.summary().save()
        times = iter(["01", "02", "03", "04", "05"])
        monkeypatch.setattr(graver.api, "_utc_now_iso", lambda: next(times))
        first = record_memorial_alias(
            database.name, source.memorial_id, 900001, "merged"
        )
        second = record_memorial_alias(
            database.name, source.memorial_id, 900001, "merged"
        )
        changed = record_memorial_alias(
            database.name,
            source.memorial_id,
            900002,
            "redirected",
            reason="reviewed change",
        )
        retract_memorial_alias(database.name, source.memorial_id, "not canonical")
        active = record_memorial_alias(
            database.name, source.memorial_id, 900002, "redirected"
        )
        history = alias_history(database.name, source.memorial_id)
        assert first["current"]["first_observed_at"] == "01"
        assert second["current"]["first_observed_at"] == "01"
        assert changed["current"]["target_memorial_id"] == 900002
        assert active["current"]["status"] == "active"
        assert [item["event_type"] for item in history] == [
            "observed",
            "observed",
            "changed",
            "retracted",
            "observed",
        ]

    def test_validation_cycles_resolution_reverse_and_nonlocal_target(self, database):
        first = self.summary().save()
        second = self.summary("john-j-pershing").save()
        third = self.summary("carl-sagan").save()
        with pytest.raises(MemorialAliasError, match="itself"):
            record_memorial_alias(
                database.name, first.memorial_id, first.memorial_id, "merged"
            )
        record_memorial_alias(
            database.name, first.memorial_id, second.memorial_id, "merged"
        )
        record_memorial_alias(
            database.name, second.memorial_id, third.memorial_id, "redirected"
        )
        resolved = resolve_memorial_alias(database.name, first.memorial_id)
        assert resolved == {
            "canonical_memorial_id": third.memorial_id,
            "path": [first.memorial_id, second.memorial_id, third.memorial_id],
        }
        assert reverse_alias_lookup(database.name, second.memorial_id) == [
            first.memorial_id
        ]
        with pytest.raises(MemorialAliasError, match="cycle"):
            record_memorial_alias(
                database.name, third.memorial_id, first.memorial_id, "merged"
            )
        with pytest.raises(MemorialAliasError, match="reason"):
            record_memorial_alias(database.name, first.memorial_id, 999999, "merged")

    def test_immutable_history_and_defensive_cycle_detection(self, database):
        first = self.summary().save()
        second = self.summary("john-j-pershing").save()
        record_memorial_alias(
            database.name, first.memorial_id, second.memorial_id, "merged"
        )
        with connect_database(database.name) as connection:
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                connection.execute("DELETE FROM memorial_alias_observations")
            connection.execute("PRAGMA foreign_keys=OFF")
            connection.execute("PRAGMA ignore_check_constraints=ON")
            connection.execute("DROP TRIGGER memorial_alias_observations_no_update")
            connection.execute(
                "UPDATE memorial_aliases SET target_memorial_id=? WHERE source_memorial_id=?",
                (first.memorial_id, first.memorial_id),
            )
        with graver.api._connect(database.name) as connection:
            with pytest.raises(MemorialAliasError, match="cycle"):
                graver.api._resolve_alias(connection, first.memorial_id)

    def test_merged_attempt_is_atomic_on_alias_observation_failure(
        self, database, monkeypatch
    ):
        source = self.summary().save()
        queue_memorials(database.name)
        with connect_database(database.name) as connection:
            connection.execute(
                "UPDATE research_tasks SET status='ready_for_full_scrape', "
                "updated_at='before', last_activity_at='before'"
            )
            connection.execute("""CREATE TRIGGER fail_alias_observation
                   BEFORE INSERT ON memorial_alias_observations
                   BEGIN SELECT RAISE(FAIL, 'alias observation failed'); END""")
        monkeypatch.setattr(graver.api, "_utc_now_iso", lambda: "after")
        error = MemorialMergedException(
            "merged",
            source.findagrave_url,
            "https://www.findagrave.com/memorial/999999/target",
        )
        with pytest.raises(sqlite3.IntegrityError, match="alias observation failed"):
            record_merged_task_scrape(
                database.name,
                source.memorial_id,
                999999,
                source.findagrave_url,
                error.new_url,
                error,
            )
        with connect_database(database.name) as connection:
            assert (
                connection.execute("SELECT COUNT(*) FROM memorial_aliases").fetchone()[
                    0
                ]
                == 0
            )
            assert connection.execute(
                "SELECT updated_at,last_activity_at FROM research_tasks"
            ).fetchone() == ("before", "before")
            assert (
                connection.execute(
                    "SELECT COUNT(*) FROM memorial_observations WHERE fetch_outcome='failure'"
                ).fetchone()[0]
                == 0
            )


class TestSearch(TestApi):
    def test_search_reports_progress(self, monkeypatch):
        progress_state = {"updates": []}

        class RecordingProgress:
            def __init__(self, **kwargs):
                progress_state.update(kwargs)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def update(self, amount):
                progress_state["updates"].append(amount)

        response = SimpleNamespace(
            content=b"<html></html>",
            request=SimpleNamespace(url="https://example.test/search"),
        )
        driver = SimpleNamespace(get=lambda *args, **kwargs: response)
        worker = graver.api._SearchWorker(driver=driver)
        pages = iter([[object()] * 20, [object()] * 5])
        monkeypatch.setattr(worker, "scrape_count", lambda soup: 25)
        monkeypatch.setattr(
            worker, "scrape_results_page", lambda *args, **kwargs: next(pages)
        )
        monkeypatch.setattr(graver.api, "tqdm", RecordingProgress)

        results = worker.search()

        assert len(results) == 25
        assert progress_state["total"] == 25
        assert progress_state["desc"] == "Searching memorials"
        assert progress_state["unit"] == "memorial"
        assert progress_state["updates"] == [20, 5]

    def test_worker_supports_current_live_search_fields(self):
        fixture = Path(__file__).parent / "fixtures/live-search/search-form-fields.html"
        soup = BeautifulSoup(fixture.read_text(), "html.parser")
        field_names = {field["name"] for field in soup.select("[name]")}
        worker = graver.api._SearchWorker(
            fulltext="John Smith",
            bio="married",
            memorialid="123",
            tags="american revolutionary war",
        )

        assert field_names == {
            "fulltext",
            "bio",
            "memorialid",
            "tags",
            "birthyearfilter",
            "datefilter",
            "orderby",
        }
        assert field_names <= worker.params.keys()
        assert worker.params["fulltext"] == "John Smith"
        assert worker.params["bio"] == "married"
        assert worker.params["memorialid"] == "123"
        assert worker.params["tags"] == "american revolutionary war"

    @pytest.mark.parametrize(
        "person",
        [
            Test.load_memorial_from_json("james-fenimore-cooper"),
            Test.load_memorial_from_json("john-j-pershing"),
        ],
    )
    def test_search(self, person: dict, driver):
        names = person["name"].split(" ")
        first_name = names[0]
        middle_name = ""
        last_name = names[len(names) - 1]
        if len(names) > 2:
            middle_name = names[1]

        birth_year: str = person["birth"][-4:]
        death_year: str = person["death"][-4:]
        results = Memorial.search(
            firstname=first_name,
            middlename=middle_name,
            lastname=last_name,
            birthyear=birth_year,
            deathyear=death_year,
            max_results=1,
            driver=driver,
        )
        assert results is not None
        assert len(results) == 1
        for result in results:
            assert isinstance(result, MemorialSummary)
            assert first_name in result.name
            assert middle_name in result.name
            assert last_name in result.name
            assert birth_year == result.birth[-4:]
            assert death_year == result.death[-4:]
            assert result.nickname == person["nickname"]

    # @pytest.mark.parametrize(
    #     "param: dict[str, Any]",
    #     [
    #         {"famous": True},
    #         {"famous": False},
    #         {"sponsored": True},
    #         {"sponsored": False},
    #         {"noCemetery": True},
    #         {"cenotaph": True},
    #         {"cenotaph": False},
    #         {"monument": True},
    #         {"monument": False},
    #         {"isVeteran": True},
    #         {"isVeteran": False},
    #         {"photofilter": "photos"},
    #         {"photofilter": "nophotos"},
    #         {"gpsfilter": "gps"},
    #         {"gpsfilter": "nogps"},
    #         {"flowers": True},
    #         {"flowers": False},
    #         {"hasPlot": True},
    #         {"hasPlot": False},
    #     ],
    # )
    # @pytest.mark.parametrize("key, value", [("famous", [True, False])])
    # def test_search_parameters(self, key, value, driver):
    #     max_results = 5
    #     args: dict[str, any] = {
    #         "driver": driver,
    #         "max_results": max_results,
    #         key: value,
    #     }
    #     rs = Memorial.search(**args)
    #     assert 0 < len(rs) <= max_results

    @pytest.mark.parametrize("value", [True, False])
    @pytest.mark.parametrize(
        "key",
        [
            "famous",
            "sponsored",
            "noCemetery",
            "cenotaph",
            "monument",
            "isVeteran",
            "flowers",
            "hasPlot",
        ],
    )
    def test_search_bool_parameters(self, key, value, driver) -> None:
        max_results = 5
        args: dict[str, Any] = {
            "driver": driver,
            "max_results": max_results,
            key: value,
        }
        rs: graver.api.ResultSet = Memorial.search(**args)
        assert 0 <= len(rs) <= max_results

    @pytest.mark.parametrize(
        "key, value",
        [
            ("includeNickName", True),
            ("includeMaidenName", True),
            ("includeTitles", True),
            ("exactName", True),
            ("fuzzyNames", True),
        ],
    )
    @pytest.mark.parametrize("firstname, lastname", [("John", "Smith")])
    def test_search_name_filters(self, firstname, lastname, key, value, driver):
        max_results = 5
        args = {
            "driver": driver,
            "max_results": max_results,
            "firstname": firstname,
            "lastname": lastname,
            key: value,
        }
        rs = Memorial.search(**args)
        assert 0 < len(rs) <= max_results

    @pytest.mark.parametrize("value", ["gps", "nogps"])
    def test_gpsfilter(self, value, driver) -> None:
        max_results = 5
        args: dict[str, Any] = {
            "driver": driver,
            "max_results": max_results,
            "gpsfilter": value,
        }
        rs: graver.api.ResultSet = Memorial.search(**args)
        assert 1 <= len(rs) <= max_results

    @pytest.mark.parametrize(
        "key, value",
        [
            ("photofilter", "photos"),
            ("photofilter", "nophotos"),
            ("gpsfilter", "gps"),
            ("gpsfilter", "nogps"),
        ],
    )
    def test_non_bool_filters(self, key, value, driver) -> None:
        max_results = 5
        args: dict[str, Any] = {
            "driver": driver,
            "max_results": max_results,
            key: value,
        }
        rs: graver.api.ResultSet = Memorial.search(**args)
        assert 1 <= len(rs) <= max_results

    @pytest.mark.parametrize(
        "args, expected", [({"lastname": "Jackson", "max_results": 37}, 37)]
    )
    def test_search_max_results(self, args, expected, driver):
        logging.getLogger().setLevel(logging.DEBUG)
        args["driver"] = driver
        rs = Memorial.search(**args)
        assert 0 < len(rs) <= expected
        pass

    @pytest.mark.parametrize("name", TestApi.famous_memorials)
    def test_search_famous_people(self, name: str, driver) -> None:
        person = Test.load_memorial_from_json(name)
        parts = person["name"].split(" ")
        first = parts[0]
        last = parts[len(parts) - 1]
        if len(parts) > 2:
            middle = parts[1]
        else:
            middle = ""

        patt = re.compile(r"\d{4}$")
        assert (match := re.search(patt, person["birth"])) is not None
        birth_year = match.group(0)
        assert (match := re.search(patt, person["death"])) is not None
        death_year = match.group(0)
        results = Memorial.search(
            firstname=first,
            middlename=middle,
            lastname=last,
            birthyear=birth_year,
            deathyear=death_year,
            famous=True,
            driver=driver,
        )
        assert len(results) >= 1
        assert (m := results[0]) is not None
        assert isinstance(m, MemorialSummary)
        assert m.memorial_id == person["memorial_id"]
        assert first in m.name
        if middle != "":
            assert middle in m.name
        assert last in m.name
        assert birth_year in m.birth
        assert death_year in m.death
        assert m.famous

    def test_search_empty(self, driver) -> None:
        logging.getLogger(__name__).setLevel(logging.DEBUG)
        logging.getLogger("betamax").setLevel(logging.DEBUG)
        results = Memorial.search(driver=driver)
        assert len(results) == 0

    # @pytest.mark.parametrize(
    #     "cemetery_url",
    #     [
    #         "https://www.findagrave.com/cemetery/641519",
    #     ],
    # )
    # def test_search_cemetery_famous_veterans(self, cemetery_url, driver):
    #     c = Cemetery(cemetery_url, driver=driver)
    #     results = Memorial.search(c, famous="true", isVeteran="true")
    #     assert results is not None
    #     assert len(results) > 0
    #     for m in results:
    #         assert m.famous
    #         assert m.veteran

    # @pytest.mark.parametrize(
    #     "url, max_results", [("https://www.findagrave.com/cemetery/641519", 37)]
    # )
    # def test_search_cemetery_max_results(self, url, max_results, driver):
    #     rs = Memorial.search(Cemetery(url, driver=driver), max_results=max_results)
    #     assert len(rs) == max_results

    def test_search_cemetery_identifies_memorial_type_monument(self, driver):
        cem = Cemetery(
            "https://www.findagrave.com/cemetery/1990395/honolulu-memorial",
            driver=driver,
        )
        rs = Memorial.search(cem, firstname="Adrian", lastname="Williams")
        assert len(rs) == 1
        m = rs[0]
        assert isinstance(m, MemorialSummary)
        assert m.memorial_type == "Monument"

    def test_search_cemetery_identifies_memorial_type_cenotaph(self, driver):
        cem = Cemetery(
            "https://www.findagrave.com/cemetery/1990395/honolulu-memorial",
            driver=driver,
        )
        rs = Memorial.search(cem, firstname="Harold", lastname="Costill")
        assert len(rs) == 1
        m = rs[0]
        assert isinstance(m, MemorialSummary)
        assert m.memorial_type == "Cenotaph"

    @pytest.mark.parametrize(
        "cem_url",
        ["https://www.findagrave.com/cemetery/49269/arlington-national-cemetery"],
    )
    def test_search_cemetery_multi_page(self, cem_url, driver):
        rs = Memorial.search(Cemetery(cem_url, driver=driver), max_results=40)
        assert len(rs) == 40

    @pytest.mark.parametrize(
        "cemetery_name, expected_count",
        [("monticello-graveyard", 18)],
    )
    def test_search_cemetery(self, cemetery_name, expected_count, driver):
        cem = Cemetery.from_dict(Test.load_cemetery_from_json(cemetery_name))
        cem.driver = driver
        results = Memorial.search(cem, isVeteran=True)
        assert results is not None
        assert len(results) == expected_count
        for _, m in enumerate(results):
            assert m.veteran

    @pytest.mark.parametrize(
        "url, memorial_dict",
        [
            (
                "https://www.findagrave.com/cemetery/2783285/rachel-levy-gravesite",
                Test.load_memorial_from_json("rachel-machado-levy"),
            )
        ],
    )
    def test_search_cemetery_all(self, url, memorial_dict, driver) -> None:
        cem = Cemetery(url, driver=driver)
        assert cem.num_memorials > 0
        results = Memorial.search(cem)
        assert len(results) == cem.num_memorials
        expected = Memorial.from_dict(memorial_dict)
        m: Memorial = results[0]
        assert m.name == expected.name
        assert m.memorial_id == expected.memorial_id

    @pytest.mark.parametrize(
        "name, page_num",
        [("monticello-graveyard", 3)],
    )
    def test_search_cemetery_specific_page(
        self, name: str, page_num: int, driver: Driver
    ):
        d: dict[str, Any] = self.load_cemetery_from_json(name)
        d["driver"] = driver
        cem = Cemetery.from_dict(d)
        rs = Memorial.search(cem, page=page_num)
        assert len(rs) == 20
        assert f"page={page_num}" in rs.source
