"""
Historical tracking database for flaky test results.
Stores test run results in SQLite for trend analysis.
"""

import sqlite3
from typing import Any


class ResultsDatabase:
    """Manage historical test results in SQLite."""

    def __init__(self, db_path: str = "flaky_test_history.db") -> None:
        """Initialize database connection."""
        self.db_path = db_path
        self.conn: sqlite3.Connection
        self._init_db()

    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Test runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                repository TEXT NOT NULL,
                test_command TEXT NOT NULL,
                total_runs INTEGER NOT NULL,
                parallelism INTEGER NOT NULL,
                failures INTEGER NOT NULL,
                repro_rate REAL NOT NULL,
                severity TEXT NOT NULL,
                duration_seconds REAL,
                pr_number INTEGER,
                branch TEXT,
                commit_sha TEXT
            )
        """)

        # Individual test results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                attempt INTEGER NOT NULL,
                exit_code INTEGER,
                passed BOOLEAN NOT NULL,
                stdout TEXT,
                stderr TEXT,
                FOREIGN KEY (run_id) REFERENCES test_runs(id)
            )
        """)

        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_repository
            ON test_runs(repository)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON test_runs(timestamp)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pr_number
            ON test_runs(pr_number)
        """)

        self.conn.commit()

    def save_run(
        self,
        repository: str,
        test_command: str,
        total_runs: int,
        parallelism: int,
        failures: int,
        repro_rate: float,
        severity: str,
        results: list[dict[str, Any]],
        duration_seconds: float | None = None,
        pr_number: int | None = None,
        branch: str | None = None,
        commit_sha: str | None = None,
    ) -> int:
        """
        Save a test run to the database.

        Returns:
            int: The ID of the inserted run
        """
        cursor = self.conn.cursor()

        # Insert run summary
        cursor.execute(
            """
            INSERT INTO test_runs (
                repository, test_command, total_runs, parallelism,
                failures, repro_rate, severity, duration_seconds,
                pr_number, branch, commit_sha
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                repository,
                test_command,
                total_runs,
                parallelism,
                failures,
                repro_rate,
                severity,
                duration_seconds,
                pr_number,
                branch,
                commit_sha,
            ),
        )

        run_id = cursor.lastrowid
        assert run_id is not None, "Failed to get last row ID"

        # Insert individual test results
        for result in results:
            cursor.execute(
                """
                INSERT INTO test_results (
                    run_id, attempt, exit_code, passed, stdout, stderr
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    run_id,
                    result["attempt"],
                    result.get("exit_code"),
                    result["passed"],
                    result.get("stdout"),
                    result.get("stderr"),
                ),
            )

        self.conn.commit()
        return run_id

    def get_recent_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent test runs."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM test_runs
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (limit,),
        )

        return [dict(row) for row in cursor.fetchall()]

    def get_runs_by_repository(self, repository: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get test runs for a specific repository."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM test_runs
            WHERE repository = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (repository, limit),
        )

        return [dict(row) for row in cursor.fetchall()]

    def get_run_details(self, run_id: int) -> dict[str, Any] | None:
        """Get detailed results for a specific run."""
        cursor = self.conn.cursor()

        # Get run summary
        cursor.execute("SELECT * FROM test_runs WHERE id = ?", (run_id,))
        run = cursor.fetchone()

        if not run:
            return None

        run_dict = dict(run)

        # Get individual test results
        cursor.execute(
            """
            SELECT * FROM test_results
            WHERE run_id = ?
            ORDER BY attempt
        """,
            (run_id,),
        )

        run_dict["results"] = [dict(row) for row in cursor.fetchall()]

        return run_dict

    def get_flakiness_trend(self, repository: str, days: int = 30) -> list[dict[str, Any]]:
        """Get flakiness trend for a repository over time."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT
                DATE(timestamp) as date,
                AVG(repro_rate) as avg_repro_rate,
                COUNT(*) as num_runs,
                SUM(CASE WHEN repro_rate > 0.1 THEN 1 ELSE 0 END) as flaky_runs
            FROM test_runs
            WHERE repository = ?
            AND timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """,
            (repository, days),
        )

        return [dict(row) for row in cursor.fetchall()]

    def get_most_flaky_commands(self, repository: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get the most flaky test commands."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT
                test_command,
                COUNT(*) as run_count,
                AVG(repro_rate) as avg_repro_rate,
                MAX(repro_rate) as max_repro_rate,
                MAX(timestamp) as last_run
            FROM test_runs
            WHERE repository = ?
            GROUP BY test_command
            HAVING avg_repro_rate > 0
            ORDER BY avg_repro_rate DESC
            LIMIT ?
        """,
            (repository, limit),
        )

        return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self, repository: str | None = None) -> dict[str, Any]:
        """Get overall statistics."""
        cursor = self.conn.cursor()

        where_clause = "WHERE repository = ?" if repository else ""
        params = (repository,) if repository else ()

        cursor.execute(
            f"""
            SELECT
                COUNT(*) as total_runs,
                SUM(total_runs) as total_tests,
                SUM(failures) as total_failures,
                AVG(repro_rate) as avg_repro_rate,
                SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_runs,
                SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) as high_runs,
                SUM(CASE WHEN severity = 'MEDIUM' THEN 1 ELSE 0 END) as medium_runs,
                SUM(CASE WHEN severity = 'LOW' THEN 1 ELSE 0 END) as low_runs,
                SUM(CASE WHEN severity = 'NONE' THEN 1 ELSE 0 END) as none_runs
            FROM test_runs
            {where_clause}
        """,
            params,
        )

        return dict(cursor.fetchone())

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self) -> "ResultsDatabase":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
