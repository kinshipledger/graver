import os
import shlex
import tempfile
from datetime import datetime

import pytest
from betamax import Betamax
from click.testing import Result
from faker import Faker
from typer.testing import CliRunner

from graver import Cemetery, Driver, Memorial, config as graver_config
from graver.cli import app
from tests.memorial_provider import MemorialProvider, ResultSetProvider

pytest_plugins = ["pytest_helpers_namespace"]


def sanitize_cassette_interaction(interaction, _cassette):
    """Remove session- and location-identifying headers before recording."""
    request_headers = interaction.data["request"]["headers"]
    response_headers = interaction.data["response"]["headers"]

    for name in list(request_headers):
        if name.casefold() == "cookie":
            request_headers.pop(name)

    for name in list(response_headers):
        normalized_name = name.casefold()
        if normalized_name == "set-cookie" or normalized_name.startswith("cf-"):
            response_headers.pop(name)


def pytest_configure():
    pass


@pytest.fixture(autouse=True)
def customize_faker(faker: Faker):
    faker.add_provider(MemorialProvider)
    faker.add_provider(ResultSetProvider)


@pytest.fixture(autouse=True)
def disable_progress_bars(monkeypatch):
    monkeypatch.setenv("TQDM_DISABLE", "1")


@pytest.fixture(autouse=True)
def isolate_graver_configuration(monkeypatch, tmp_path):
    """Prevent CLI tests from reading or writing the developer's preferences."""
    config_path = tmp_path / "user-config" / "graver" / "config.json"
    default_database = tmp_path / "user-config" / "default.db"
    default_database.parent.mkdir(parents=True)
    Memorial.create_table(str(default_database))
    real_configuration_path = graver_config.configuration_path

    def isolated_path(environment=None, platform=None, home=None):
        if environment is None and platform is None and home is None:
            return config_path
        return real_configuration_path(environment, platform, home)

    monkeypatch.setattr(graver_config, "configuration_path", isolated_path)
    monkeypatch.setenv("GRAVER_DB", str(default_database))
    return config_path


# configure Betamax
with Betamax.configure() as config:
    path = os.path.dirname(os.path.abspath(__file__))
    config.cassette_library_dir = os.path.join(path, "fixtures/cassettes")
    config.before_record(callback=sanitize_cassette_interaction)
    # config.default_cassette_options["record_mode"] = "none"

runner = CliRunner()


@pytest.fixture(scope="function")
def driver(betamax_parametrized_session):
    d = Driver(session=betamax_parametrized_session)
    yield d


# configure Faker
@pytest.fixture(scope="session", autouse=True)
def faker_seed() -> int:
    seed: int = int(datetime.now().timestamp())
    return seed


@pytest.fixture
def database():
    """Creates an empty graver database as a tempfile"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        os.environ["DATABASE_NAME"] = tf.name
        Memorial.create_table(database_name=tf.name)
        Cemetery.create_table(database_name=tf.name)
        yield tf


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
