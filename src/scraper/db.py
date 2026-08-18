"""One SQLite connection policy, shared by `fetch.db` and `index.db`.

Both databases are read while the other stage is running — extraction reads `fetch.db`
during a two-hour fetch, and a `coverage` report reads `index.db` during an extract pass.
With the default rollback journal a writer locks readers out of the whole file, so a
long-running read can fail outright at any moment. WAL lets readers and one writer
proceed together, which is how this project is actually operated.
"""

from __future__ import annotations

import sqlite3
from contextlib import suppress
from pathlib import Path

BUSY_TIMEOUT_MS = 10_000


def connect(path: str | Path) -> sqlite3.Connection:
    """Open a connection with the project's pragmas applied."""
    conn = sqlite3.connect(path, timeout=BUSY_TIMEOUT_MS / 1000)
    conn.row_factory = sqlite3.Row
    conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    # Switching an in-use database needs a moment's exclusive access; if another process
    # holds it right now, the mode is already set or the next open will set it.
    with suppress(sqlite3.OperationalError):
        conn.execute("PRAGMA journal_mode = WAL")
    return conn
