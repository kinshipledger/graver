import os
import re
import shlex
import shutil
from types import SimpleNamespace

import pytest
from click.testing import Result
from faker import Faker
from typer.testing import CliRunner

from graver import config as graver_config
from graver.api import Driver, Memorial
from graver.cli import app
from tests.memorial_provider import MemorialProvider, ResultSetProvider
from tests.synthetic_provider import response_for

pytest_plugins = ["pytest_helpers_namespace"]


def pytest_collection_modifyitems(items):
    """Classify every synthetic provider-contract consumer."""
    for item in items:
        if "driver" in item.fixturenames:
            item.add_marker(pytest.mark.integration)


@pytest.fixture(autouse=True)
def customize_faker(faker: Faker):
    faker.add_provider(MemorialProvider)
    faker.add_provider(ResultSetProvider)


@pytest.fixture(autouse=True)
def disable_progress_bars(monkeypatch):
    monkeypatch.setenv("TQDM_DISABLE", "1")


@pytest.fixture(autouse=True)
def isolate_graver_configuration(monkeypatch, tmp_path, database_template):
    """Prevent CLI tests from reading or writing the developer's preferences."""
    config_path = tmp_path / "user-config" / "graver" / "config.json"
    default_database = tmp_path / "user-config" / "default.db"
    default_database.parent.mkdir(parents=True)
    shutil.copyfile(database_template, default_database)
    real_configuration_path = graver_config.configuration_path

    def isolated_path(environment=None, platform=None, home=None):
        if environment is None and platform is None and home is None:
            return config_path
        return real_configuration_path(environment, platform, home)

    monkeypatch.setattr(graver_config, "configuration_path", isolated_path)
    monkeypatch.setenv("GRAVER_DB", str(default_database))
    return config_path


@pytest.fixture(scope="session")
def database_template(tmp_path_factory):
    """Create one empty current-schema database for isolated per-test copies."""
    template = tmp_path_factory.mktemp("database-template") / "current.db"
    Memorial.create_table(str(template))
    return template


runner = CliRunner()


@pytest.fixture(scope="function")
def driver(requests_mock):
    """Provide offline HTTP responses from maintained synthetic specimens."""

    def respond(request, context):
        status, body = response_for(request.url)
        context.status_code = status
        context.reason = "OK" if status < 400 else "Not Found"
        context.headers["Content-Type"] = "text/html; charset=utf-8"
        return body

    requests_mock.get(re.compile(r"https://www\.findagrave\.com/.*"), text=respond)
    d = Driver()
    yield d
    d.close()


# configure Faker
@pytest.fixture(scope="session", autouse=True)
def faker_seed() -> int:
    return 20260822


@pytest.fixture
def database(tmp_path, database_template, monkeypatch):
    """Provide an isolated current-schema database removed by pytest cleanup."""
    path = tmp_path / "fixture.db"
    shutil.copyfile(database_template, path)
    monkeypatch.setenv("DATABASE_NAME", str(path))
    yield SimpleNamespace(name=str(path))


class Helpers:
    @staticmethod
    def graver_cli(command_string) -> Result:
        command_list = shlex.split(command_string)
        env = os.environ.copy()
        env["TQDM_DISABLE"] = "1"
        result = runner.invoke(
            app, command_list, env=env, obj=driver, terminal_width=120
        )
        return result


@pytest.fixture
def helpers():
    return Helpers
