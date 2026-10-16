"""Test configuration.

The database tests insert and delete rows, so they must never run against a
database someone actually uses. They only run when TEST_DATABASE_URL is set and
names a database ending in "_test"; otherwise they are skipped (unset) or the
run stops (wrong name). Tests that need no database always run.

TEST_DATABASE_URL replaces DATABASE_URL for the whole test run. It has to be
copied into the environment here, before any test module imports the app,
because config.py reads DATABASE_URL once at import time.
"""

import os

import pytest
from sqlalchemy.engine import make_url

_test_database_url = os.environ.get("TEST_DATABASE_URL")
if _test_database_url:
    os.environ["DATABASE_URL"] = _test_database_url


@pytest.fixture(scope="session")
def test_database():
    if not _test_database_url:
        pytest.skip(
            "TEST_DATABASE_URL is not set. Database tests need a dedicated PostgreSQL "
            "database whose name ends in _test, e.g. "
            "postgresql+psycopg2://user:password@localhost:5432/sip_test"
        )

    name = make_url(_test_database_url).database or ""
    if not name.endswith("_test"):
        pytest.exit(
            f"Refusing to run: TEST_DATABASE_URL points at '{name}', and the database "
            "tests write and delete rows. Use a database whose name ends in _test.",
            returncode=2,
        )
    return _test_database_url
