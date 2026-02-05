"""
Tests for worker.py - the main serverless handler.
"""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mock runpod before importing worker
sys.modules["runpod"] = MagicMock()
sys.modules["runpod.serverless"] = MagicMock()

# Now we can import worker
from worker import detect_framework, get_seed_env_var, handler, install_dependencies, run_test_once


class TestRunTestOnce:
    """Test the run_test_once function."""

    @patch("worker.subprocess.run")
    def test_successful_test_run(self, mock_run):
        """Test a successful test execution."""
        mock_run.return_value = Mock(returncode=0, stdout="1 passed in 0.01s", stderr="")

        result = run_test_once(["pytest", "test.py"], {"TEST_SEED": "123", "ATTEMPT": "0"}, 0)

        assert result["attempt"] == 0
        assert result["exit_code"] == 0
        assert result["passed"] is True
        assert "1 passed" in result["stdout"]
        assert result["stderr"] == ""

    @patch("worker.subprocess.run")
    def test_failed_test_run(self, mock_run):
        """Test a failed test execution."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="AssertionError: test failed")

        result = run_test_once(["pytest", "test.py"], {"TEST_SEED": "456", "ATTEMPT": "1"}, 1)

        assert result["attempt"] == 1
        assert result["exit_code"] == 1
        assert result["passed"] is False
        assert "AssertionError" in result["stderr"]

    @patch("worker.subprocess.run")
    def test_timeout_handling(self, mock_run):
        """Test timeout is handled properly."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=300)

        result = run_test_once(["pytest", "test.py"], {"TEST_SEED": "789"}, 2)

        assert result["attempt"] == 2
        assert result["exit_code"] is None
        assert result["passed"] is False
        assert result["stderr"] == "TIMEOUT"

    @patch("worker.subprocess.run")
    def test_general_exception_handling(self, mock_run):
        """Test general exception is handled."""
        mock_run.side_effect = RuntimeError("Something went wrong")

        result = run_test_once(["pytest", "test.py"], {"TEST_SEED": "999"}, 3)

        assert result["attempt"] == 3
        assert result["exit_code"] is None
        assert result["passed"] is False
        assert "ERROR:" in result["stderr"]
        assert "Something went wrong" in result["stderr"]

    @patch("worker.subprocess.run")
    def test_environment_variables_passed(self, mock_run):
        """Test that environment variables are passed correctly."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        env_overrides = {"TEST_SEED": "12345", "ATTEMPT": "5"}
        run_test_once(["pytest", "test.py"], env_overrides, 5)

        # Check that subprocess.run was called with env containing our overrides
        call_kwargs = mock_run.call_args[1]
        assert "env" in call_kwargs
        assert call_kwargs["env"]["TEST_SEED"] == "12345"
        assert call_kwargs["env"]["ATTEMPT"] == "5"


class TestHandler:
    """Test the main handler function."""

    @patch("worker.shutil.rmtree")
    @patch("worker.os.chdir")
    @patch("worker.os.getcwd")
    @patch("worker.os.path.exists")
    @patch("worker.subprocess.run")
    @patch("worker.tempfile.mkdtemp")
    @patch("worker.ThreadPoolExecutor")
    def test_handler_basic_flow(
        self,
        mock_executor,
        mock_mkdtemp,
        mock_subprocess,
        mock_exists,
        mock_getcwd,
        mock_chdir,
        mock_rmtree,
    ):
        """Test basic handler flow with valid input."""
        # Setup mocks
        mock_mkdtemp.return_value = "/tmp/test123"
        mock_getcwd.return_value = "/original/dir"
        mock_exists.return_value = False  # No requirements.txt

        # Mock git clone success
        mock_subprocess.return_value = Mock(returncode=0, stdout="", stderr="")

        # Mock ThreadPoolExecutor
        mock_future = Mock()
        mock_future.result.return_value = {
            "attempt": 0,
            "exit_code": 0,
            "passed": True,
            "stdout": "ok",
            "stderr": "",
        }

        mock_executor_instance = Mock()
        mock_executor_instance.__enter__ = Mock(return_value=mock_executor_instance)
        mock_executor_instance.__exit__ = Mock(return_value=False)
        mock_executor_instance.submit = Mock(return_value=mock_future)
        mock_executor.return_value = mock_executor_instance

        # Mock as_completed
        with patch("worker.as_completed", return_value=[mock_future]):
            # Call handler
            job = {
                "input": {
                    "repo": "https://github.com/test/repo",
                    "test_command": "pytest tests/",
                    "runs": 2,
                    "parallelism": 1,
                }
            }

            result = handler(job)

        # Verify result structure
        assert "total_runs" in result
        assert "parallelism" in result
        assert "failures" in result
        assert "repro_rate" in result
        assert "results" in result

        assert result["total_runs"] == 2
        assert result["parallelism"] == 1

        # Verify cleanup was called
        mock_rmtree.assert_called_once_with("/tmp/test123")
        mock_chdir.assert_called()  # Called to restore directory

    @patch("worker.subprocess.run")
    def test_handler_validates_repo_url(self, mock_subprocess):
        """Test that invalid repo URLs are rejected."""
        job = {
            "input": {"repo": "invalid-url", "test_command": "pytest", "runs": 10, "parallelism": 2}
        }

        with pytest.raises(ValueError, match="Invalid repository URL"):
            handler(job)

    @patch("worker.subprocess.run")
    def test_handler_validates_runs(self, mock_subprocess):
        """Test that runs are validated."""
        job = {
            "input": {
                "repo": "https://github.com/test/repo",
                "test_command": "pytest",
                "runs": 5000,  # Too many
                "parallelism": 2,
            }
        }

        with pytest.raises(ValueError, match="Runs must be between"):
            handler(job)

    @patch("worker.subprocess.run")
    def test_handler_validates_parallelism(self, mock_subprocess):
        """Test that parallelism is validated."""
        job = {
            "input": {
                "repo": "https://github.com/test/repo",
                "test_command": "pytest",
                "runs": 10,
                "parallelism": 100,  # Too many
            }
        }

        with pytest.raises(ValueError, match="Parallelism must be between"):
            handler(job)

    @patch("worker.subprocess.run")
    def test_handler_requires_repo(self, mock_subprocess):
        """Test that repo is required."""
        job = {"input": {"repo": "", "test_command": "pytest", "runs": 10, "parallelism": 2}}

        with pytest.raises(ValueError, match="Repository URL is required"):
            handler(job)

    @patch("worker.subprocess.run")
    def test_handler_requires_test_command(self, mock_subprocess):
        """Test that test_command is required."""
        job = {
            "input": {
                "repo": "https://github.com/test/repo",
                "test_command": "",
                "runs": 10,
                "parallelism": 2,
            }
        }

        with pytest.raises(ValueError, match="Test command is required"):
            handler(job)

    @patch("worker.shutil.rmtree")
    @patch("worker.os.chdir")
    @patch("worker.os.getcwd")
    @patch("worker.subprocess.run")
    @patch("worker.tempfile.mkdtemp")
    def test_handler_git_clone_failure(
        self, mock_mkdtemp, mock_subprocess, mock_getcwd, mock_chdir, mock_rmtree
    ):
        """Test handling of git clone failure."""
        import subprocess

        mock_mkdtemp.return_value = "/tmp/test456"
        mock_getcwd.return_value = "/original/dir"

        # Mock git clone failure
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="git clone", stderr="repository not found"
        )

        job = {
            "input": {
                "repo": "https://github.com/test/nonexistent",
                "test_command": "pytest",
                "runs": 10,
                "parallelism": 2,
            }
        }

        with pytest.raises(RuntimeError, match="Failed to clone repository"):
            handler(job)

        # Verify cleanup still happens
        mock_rmtree.assert_called()

    @patch("worker.shutil.rmtree")
    @patch("worker.os.chdir")
    @patch("worker.os.getcwd")
    @patch("worker.subprocess.run")
    @patch("worker.tempfile.mkdtemp")
    def test_handler_git_clone_timeout(
        self, mock_mkdtemp, mock_subprocess, mock_getcwd, mock_chdir, mock_rmtree
    ):
        """Test handling of git clone timeout."""
        import subprocess

        mock_mkdtemp.return_value = "/tmp/test789"
        mock_getcwd.return_value = "/original/dir"

        # Mock git clone timeout
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd="git clone", timeout=300)

        job = {
            "input": {
                "repo": "https://github.com/test/huge-repo",
                "test_command": "pytest",
                "runs": 10,
                "parallelism": 2,
            }
        }

        with pytest.raises(RuntimeError, match="timed out"):
            handler(job)

    @patch("worker.shutil.rmtree")
    @patch("worker.os.chdir")
    @patch("worker.os.getcwd")
    @patch("worker.os.path.exists")
    @patch("worker.subprocess.run")
    @patch("worker.tempfile.mkdtemp")
    @patch("worker.ThreadPoolExecutor")
    def test_handler_installs_dependencies(
        self,
        mock_executor,
        mock_mkdtemp,
        mock_subprocess,
        mock_exists,
        mock_getcwd,
        mock_chdir,
        mock_rmtree,
    ):
        """Test that dependencies are installed if requirements.txt exists."""
        mock_mkdtemp.return_value = "/tmp/test999"
        mock_getcwd.return_value = "/original/dir"
        mock_exists.return_value = True  # requirements.txt exists

        # Track subprocess calls
        call_count = [0]

        def subprocess_side_effect(*args, **kwargs):
            call_count[0] += 1
            return Mock(returncode=0, stdout="", stderr="")

        mock_subprocess.side_effect = subprocess_side_effect

        # Mock executor
        mock_future = Mock()
        mock_future.result.return_value = {
            "attempt": 0,
            "exit_code": 0,
            "passed": True,
            "stdout": "",
            "stderr": "",
        }

        mock_executor_instance = Mock()
        mock_executor_instance.__enter__ = Mock(return_value=mock_executor_instance)
        mock_executor_instance.__exit__ = Mock(return_value=False)
        mock_executor_instance.submit = Mock(return_value=mock_future)
        mock_executor.return_value = mock_executor_instance

        with patch("worker.as_completed", return_value=[mock_future]):
            job = {
                "input": {
                    "repo": "https://github.com/test/repo",
                    "test_command": "pytest",
                    "runs": 1,
                    "parallelism": 1,
                }
            }

            handler(job)

        # Should have called subprocess twice: git clone + pip install
        assert call_count[0] >= 2

    def test_handler_default_values(self):
        """Test that default values are used when not specified."""
        with (
            patch("worker.tempfile.mkdtemp"),
            patch("worker.os.getcwd"),
            patch("worker.os.chdir"),
            patch("worker.shutil.rmtree"),
            patch("worker.subprocess.run"),
            patch("worker.ThreadPoolExecutor") as mock_executor,
            patch("worker.os.path.exists", return_value=False),
        ):
            mock_future = Mock()
            mock_future.result.return_value = {
                "attempt": 0,
                "exit_code": 0,
                "passed": True,
                "stdout": "",
                "stderr": "",
            }

            mock_executor_instance = Mock()
            mock_executor_instance.__enter__ = Mock(return_value=mock_executor_instance)
            mock_executor_instance.__exit__ = Mock(return_value=False)
            mock_executor_instance.submit = Mock(return_value=mock_future)
            mock_executor.return_value = mock_executor_instance

            with patch("worker.as_completed", return_value=[mock_future]):
                job = {
                    "input": {
                        "repo": "https://github.com/test/repo",
                        "test_command": "pytest",
                        # runs and parallelism not specified
                    }
                }

                result = handler(job)

                # Should use defaults
                assert result["total_runs"] == 10  # default
                assert result["parallelism"] == 4  # default


class TestDetectFramework:
    """Test the detect_framework function."""

    def test_detect_go_framework(self, tmp_path):
        """Test detection of Go projects."""
        # Create go.mod file
        go_mod = tmp_path / "go.mod"
        go_mod.write_text("module example.com/myproject\n\ngo 1.22")

        framework = detect_framework(str(tmp_path))
        assert framework == "go"

    def test_detect_python_requirements(self, tmp_path):
        """Test detection of Python projects with requirements.txt."""
        # Create requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("pytest==9.0.2\n")

        framework = detect_framework(str(tmp_path))
        assert framework == "python"

    def test_detect_python_pyproject(self, tmp_path):
        """Test detection of Python projects with pyproject.toml."""
        # Create pyproject.toml
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[project]\nname = 'myproject'\n")

        framework = detect_framework(str(tmp_path))
        assert framework == "python"

    def test_detect_typescript_jest(self, tmp_path):
        """Test detection of TypeScript Jest projects."""
        # Create package.json with jest
        package_json = tmp_path / "package.json"
        package_json.write_text('{"devDependencies": {"jest": "^29.0.0"}}')

        framework = detect_framework(str(tmp_path))
        assert framework == "typescript-jest"

    def test_detect_typescript_vitest(self, tmp_path):
        """Test detection of TypeScript Vitest projects."""
        # Create package.json with vitest
        package_json = tmp_path / "package.json"
        package_json.write_text('{"devDependencies": {"vitest": "^1.0.0"}}')

        framework = detect_framework(str(tmp_path))
        assert framework == "typescript-vitest"

    def test_detect_javascript_mocha(self, tmp_path):
        """Test detection of JavaScript Mocha projects."""
        # Create package.json with mocha
        package_json = tmp_path / "package.json"
        package_json.write_text('{"devDependencies": {"mocha": "^10.0.0"}}')

        framework = detect_framework(str(tmp_path))
        assert framework == "javascript-mocha"

    def test_detect_unknown_framework(self, tmp_path):
        """Test detection returns unknown for unrecognized projects."""
        # Empty directory
        framework = detect_framework(str(tmp_path))
        assert framework == "unknown"

    def test_detect_invalid_package_json(self, tmp_path):
        """Test handling of invalid package.json."""
        # Create invalid package.json
        package_json = tmp_path / "package.json"
        package_json.write_text("not valid json {")

        # Should fall back to unknown
        framework = detect_framework(str(tmp_path))
        assert framework == "unknown"


class TestGetSeedEnvVar:
    """Test the get_seed_env_var function."""

    def test_python_seed_var(self):
        """Test Python seed environment variable."""
        env = get_seed_env_var("python", 12345)
        assert env == {"TEST_SEED": "12345"}

    def test_go_seed_var(self):
        """Test Go seed environment variable."""
        env = get_seed_env_var("go", 67890)
        assert env == {"GO_TEST_SEED": "67890"}

    def test_typescript_jest_seed_var(self):
        """Test TypeScript Jest seed environment variable."""
        env = get_seed_env_var("typescript-jest", 11111)
        assert env == {"JEST_SEED": "11111"}

    def test_typescript_vitest_seed_var(self):
        """Test TypeScript Vitest seed environment variable."""
        env = get_seed_env_var("typescript-vitest", 22222)
        assert env == {"VITE_TEST_SEED": "22222"}

    def test_javascript_mocha_seed_var(self):
        """Test JavaScript Mocha seed environment variable."""
        env = get_seed_env_var("javascript-mocha", 33333)
        assert env == {"MOCHA_SEED": "33333"}

    def test_unknown_framework_fallback(self):
        """Test unknown framework falls back to TEST_SEED."""
        env = get_seed_env_var("unknown", 99999)
        assert env == {"TEST_SEED": "99999"}


class TestInstallDependencies:
    """Test the install_dependencies function."""

    @patch("worker.subprocess.run")
    def test_install_python_dependencies(self, mock_run, tmp_path):
        """Test installing Python dependencies."""
        # Create requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("pytest==9.0.2\n")

        mock_run.return_value = Mock(returncode=0)

        install_dependencies("python", str(tmp_path))

        # Should have called pip install
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["pip", "install", "-q", "-r", "requirements.txt"]

    @patch("worker.subprocess.run")
    def test_install_go_dependencies(self, mock_run, tmp_path):
        """Test installing Go dependencies."""
        # Create go.mod
        go_mod = tmp_path / "go.mod"
        go_mod.write_text("module example.com/myproject\n")

        mock_run.return_value = Mock(returncode=0)

        install_dependencies("go", str(tmp_path))

        # Should have called go mod download
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["go", "mod", "download"]

    @patch("worker.subprocess.run")
    def test_install_typescript_dependencies(self, mock_run, tmp_path):
        """Test installing TypeScript/JavaScript dependencies."""
        # Create package.json
        package_json = tmp_path / "package.json"
        package_json.write_text('{"dependencies": {}}')

        mock_run.return_value = Mock(returncode=0)

        install_dependencies("typescript-jest", str(tmp_path))

        # Should have called npm install
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["npm", "install", "--silent"]

    def test_skip_install_without_dependency_file(self, tmp_path, capsys):
        """Test skipping installation when dependency file doesn't exist."""
        # No files created
        install_dependencies("python", str(tmp_path))

        # Should print skip message
        captured = capsys.readouterr()
        assert "No requirements.txt found" in captured.out

    def test_skip_install_for_unknown_framework(self, tmp_path, capsys):
        """Test skipping installation for unknown frameworks."""
        install_dependencies("unknown", str(tmp_path))

        # Should print warning
        captured = capsys.readouterr()
        assert "no dependency installation configured" in captured.out

    @patch("worker.subprocess.run")
    def test_handle_installation_failure(self, mock_run, tmp_path, capsys):
        """Test handling of dependency installation failure."""
        import subprocess

        # Create requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("invalid-package==999.999.999\n")

        # Mock failed installation
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["pip", "install"], stderr="ERROR: Package not found"
        )

        install_dependencies("python", str(tmp_path))

        # Should print warning but not raise
        captured = capsys.readouterr()
        assert "Warning: Failed to install dependencies" in captured.out

    @patch("worker.subprocess.run")
    def test_handle_installation_timeout(self, mock_run, tmp_path, capsys):
        """Test handling of dependency installation timeout."""
        import subprocess

        # Create requirements.txt
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("pytest==9.0.2\n")

        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired(["pip", "install"], 300)

        install_dependencies("python", str(tmp_path))

        # Should print timeout warning
        captured = capsys.readouterr()
        assert "Warning: Dependency installation timed out" in captured.out
