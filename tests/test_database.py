"""
Tests for historical tracking database.
"""

import os
import tempfile

import pytest

from database import ResultsDatabase


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    db = ResultsDatabase(path)
    yield db

    db.close()
    os.unlink(path)


class TestResultsDatabase:
    """Test database operations."""

    def test_database_initialization(self, temp_db) -> None:
        """Test database tables are created."""
        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        assert "test_runs" in tables
        assert "test_results" in tables

    def test_save_and_retrieve_run(self, temp_db) -> None:
        """Test saving and retrieving a test run."""
        results = [
            {"attempt": 0, "exit_code": 0, "passed": True, "stdout": "ok", "stderr": ""},
            {
                "attempt": 1,
                "exit_code": 1,
                "passed": False,
                "stdout": "",
                "stderr": "error",
            },
        ]

        run_id = temp_db.save_run(
            repository="test/repo",
            test_command="pytest tests/",
            total_runs=2,
            parallelism=2,
            failures=1,
            repro_rate=0.5,
            severity="HIGH",
            results=results,
            duration_seconds=10.5,
            pr_number=123,
            branch="main",
            commit_sha="abc123",
        )

        assert run_id > 0

        # Retrieve the run
        run = temp_db.get_run_details(run_id)
        assert run is not None
        assert run["repository"] == "test/repo"
        assert run["test_command"] == "pytest tests/"
        assert run["total_runs"] == 2
        assert run["failures"] == 1
        assert run["repro_rate"] == 0.5
        assert run["severity"] == "HIGH"
        assert run["pr_number"] == 123
        assert len(run["results"]) == 2

    def test_get_recent_runs(self, temp_db) -> None:
        """Test retrieving recent runs."""
        # Add multiple runs
        for i in range(5):
            temp_db.save_run(
                repository="test/repo",
                test_command=f"pytest test_{i}.py",
                total_runs=10,
                parallelism=2,
                failures=i,
                repro_rate=i / 10,
                severity="MEDIUM",
                results=[],
            )

        recent = temp_db.get_recent_runs(limit=3)
        assert len(recent) == 3
        # Should be in reverse chronological order
        assert recent[0]["test_command"] == "pytest test_4.py"
        assert recent[1]["test_command"] == "pytest test_3.py"

    def test_get_runs_by_repository(self, temp_db) -> None:
        """Test filtering runs by repository."""
        temp_db.save_run(
            repository="repo1",
            test_command="pytest",
            total_runs=10,
            parallelism=2,
            failures=1,
            repro_rate=0.1,
            severity="LOW",
            results=[],
        )
        temp_db.save_run(
            repository="repo2",
            test_command="pytest",
            total_runs=10,
            parallelism=2,
            failures=2,
            repro_rate=0.2,
            severity="MEDIUM",
            results=[],
        )

        repo1_runs = temp_db.get_runs_by_repository("repo1")
        assert len(repo1_runs) == 1
        assert repo1_runs[0]["repository"] == "repo1"

    def test_get_flakiness_trend(self, temp_db) -> None:
        """Test flakiness trend calculation."""
        # Add runs over multiple days (simulated with manual timestamps)
        cursor = temp_db.conn.cursor()

        # Day 1: High flakiness
        cursor.execute(
            """
            INSERT INTO test_runs (
                timestamp, repository, test_command, total_runs,
                parallelism, failures, repro_rate, severity
            ) VALUES (
                datetime('now', '-2 days'), 'test/repo', 'pytest',
                10, 2, 8, 0.8, 'HIGH'
            )
        """
        )

        # Day 2: Lower flakiness
        cursor.execute(
            """
            INSERT INTO test_runs (
                timestamp, repository, test_command, total_runs,
                parallelism, failures, repro_rate, severity
            ) VALUES (
                datetime('now', '-1 days'), 'test/repo', 'pytest',
                10, 2, 3, 0.3, 'MEDIUM'
            )
        """
        )

        temp_db.conn.commit()

        trend = temp_db.get_flakiness_trend("test/repo", days=7)
        assert len(trend) >= 1  # At least one day of data
        assert "avg_repro_rate" in trend[0]
        assert "num_runs" in trend[0]

    def test_get_most_flaky_commands(self, temp_db) -> None:
        """Test getting most flaky test commands."""
        # Add runs with different commands and flakiness levels
        commands = [
            ("pytest test_a.py", 0.5),
            ("pytest test_b.py", 0.8),
            ("pytest test_c.py", 0.2),
        ]

        for cmd, rate in commands:
            temp_db.save_run(
                repository="test/repo",
                test_command=cmd,
                total_runs=10,
                parallelism=2,
                failures=int(10 * rate),
                repro_rate=rate,
                severity="MEDIUM",
                results=[],
            )

        flaky = temp_db.get_most_flaky_commands("test/repo", limit=2)
        assert len(flaky) == 2
        # Should be sorted by avg_repro_rate descending
        assert flaky[0]["test_command"] == "pytest test_b.py"
        assert flaky[0]["avg_repro_rate"] == 0.8

    def test_get_statistics(self, temp_db) -> None:
        """Test getting overall statistics."""
        # Add runs with different severities
        severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"]
        for severity in severities:
            temp_db.save_run(
                repository="test/repo",
                test_command="pytest",
                total_runs=10,
                parallelism=2,
                failures=1,
                repro_rate=0.1,
                severity=severity,
                results=[],
            )

        stats = temp_db.get_statistics()
        assert stats["total_runs"] == 5
        assert stats["critical_runs"] == 1
        assert stats["high_runs"] == 1
        assert stats["medium_runs"] == 1
        assert stats["low_runs"] == 1
        assert stats["none_runs"] == 1

    def test_get_statistics_by_repository(self, temp_db) -> None:
        """Test statistics filtered by repository."""
        temp_db.save_run(
            repository="repo1",
            test_command="pytest",
            total_runs=10,
            parallelism=2,
            failures=5,
            repro_rate=0.5,
            severity="HIGH",
            results=[],
        )
        temp_db.save_run(
            repository="repo2",
            test_command="pytest",
            total_runs=10,
            parallelism=2,
            failures=1,
            repro_rate=0.1,
            severity="LOW",
            results=[],
        )

        stats = temp_db.get_statistics(repository="repo1")
        assert stats["total_runs"] == 1
        assert stats["high_runs"] == 1

    def test_context_manager(self) -> None:
        """Test database can be used as context manager."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        try:
            with ResultsDatabase(path) as db:
                run_id = db.save_run(
                    repository="test/repo",
                    test_command="pytest",
                    total_runs=10,
                    parallelism=2,
                    failures=1,
                    repro_rate=0.1,
                    severity="LOW",
                    results=[],
                )
                assert run_id > 0
        finally:
            os.unlink(path)

    def test_get_nonexistent_run(self, temp_db) -> None:
        """Test retrieving non-existent run returns None."""
        run = temp_db.get_run_details(99999)
        assert run is None
