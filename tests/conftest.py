import pytest
import sqlite3


@pytest.fixture
def memory_conn():
    """In-memory SQLite connection for tests."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()
