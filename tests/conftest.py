import os
import pytest


@pytest.fixture(autouse=True, scope="session")
def _ensure_postgres_extensions(django_db_setup, django_db_blocker):
    """Ensure required PostgreSQL extensions exist in the test database.

    This makes CI stable by creating btree_gist needed for GiST indexes
    on bigint/text columns.
    """
    if os.environ.get("DJANGO_SETTINGS_MODULE") is None:
        return

    with django_db_blocker.unblock():
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")
        except Exception:
            # Don't hard-fail tests if extension cannot be created (e.g., permissions)
            pass


