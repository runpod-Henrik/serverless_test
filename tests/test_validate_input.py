"""Tests for input validation."""

from validate_input import _basic_validation, validate_and_report, validate_input


class TestValidateInput:
    """Test input validation against JSON schema."""

    def test_valid_minimal_config(self):
        """Test minimal valid configuration."""
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest tests/",
        }
        is_valid, errors = validate_input(config)
        assert is_valid
        assert len(errors) == 0

    def test_valid_full_config(self):
        """Test configuration with all fields."""
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest tests/",
            "runs": 50,
            "parallelism": 5,
            "framework": "python",
        }
        is_valid, errors = validate_input(config)
        assert is_valid
        assert len(errors) == 0

    def test_valid_local_path(self):
        """Test configuration with local path."""
        config = {
            "repo": "/path/to/local/repo",
            "test_command": "go test ./...",
            "runs": 10,
        }
        is_valid, errors = validate_input(config)
        assert is_valid
        assert len(errors) == 0

    def test_missing_repo(self):
        """Test validation fails when repo is missing."""
        config = {
            "test_command": "pytest tests/",
        }
        is_valid, errors = validate_input(config)
        assert not is_valid
        assert any("repo" in error.lower() for error in errors)

    def test_missing_test_command(self):
        """Test validation fails when test_command is missing."""
        config = {
            "repo": "https://github.com/user/repo",
        }
        is_valid, errors = validate_input(config)
        assert not is_valid
        assert any("test_command" in error.lower() for error in errors)

    def test_empty_repo(self):
        """Test validation fails when repo is empty."""
        config = {
            "repo": "",
            "test_command": "pytest tests/",
        }
        is_valid, errors = validate_input(config)
        assert not is_valid

    def test_runs_too_low(self):
        """Test validation fails when runs < 1."""
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest tests/",
            "runs": 0,
        }
        is_valid, errors = validate_input(config)
        assert not is_valid
        assert any("runs" in error.lower() for error in errors)

    def test_runs_too_high(self):
        """Test validation fails when runs > 1000."""
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest tests/",
            "runs": 1001,
        }
        is_valid, errors = validate_input(config)
        assert not is_valid
        assert any("runs" in error.lower() for error in errors)

    def test_parallelism_too_low(self):
        """Test validation fails when parallelism < 1."""
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest tests/",
            "parallelism": 0,
        }
        is_valid, errors = validate_input(config)
        assert not is_valid
        assert any("parallelism" in error.lower() for error in errors)

    def test_parallelism_too_high(self):
        """Test validation fails when parallelism > 50."""
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest tests/",
            "parallelism": 51,
        }
        is_valid, errors = validate_input(config)
        assert not is_valid
        assert any("parallelism" in error.lower() for error in errors)

    def test_invalid_framework(self):
        """Test validation fails with invalid framework."""
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest tests/",
            "framework": "invalid-framework",
        }
        is_valid, errors = validate_input(config)
        assert not is_valid
        assert any("framework" in error.lower() for error in errors)

    def test_valid_frameworks(self):
        """Test all valid framework values."""
        frameworks = ["python", "go", "typescript-jest", "typescript-vitest", "javascript-mocha"]
        for framework in frameworks:
            config = {
                "repo": "https://github.com/user/repo",
                "test_command": "test command",
                "framework": framework,
            }
            is_valid, errors = validate_input(config)
            assert is_valid, f"Framework {framework} should be valid, got errors: {errors}"

    def test_additional_properties_rejected(self):
        """Test that additional unknown properties are rejected."""
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest tests/",
            "unknown_field": "should fail",
        }
        is_valid, errors = validate_input(config)
        assert not is_valid
        assert any("additional" in error.lower() or "unknown" in error.lower() for error in errors)

    def test_wrong_type_runs(self):
        """Test validation fails when runs is not an integer."""
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest tests/",
            "runs": "50",  # String instead of int
        }
        is_valid, errors = validate_input(config)
        assert not is_valid
        assert any("runs" in error.lower() for error in errors)

    def test_wrong_type_parallelism(self):
        """Test validation fails when parallelism is not an integer."""
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest tests/",
            "parallelism": 5.5,  # Float instead of int
        }
        is_valid, errors = validate_input(config)
        assert not is_valid

    def test_basic_validation_fallback(self):
        """Test basic validation works when jsonschema is not available."""
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest tests/",
            "runs": 50,
            "parallelism": 5,
        }
        is_valid, errors = _basic_validation(config)
        assert is_valid
        assert len(errors) == 0

    def test_basic_validation_missing_required(self):
        """Test basic validation catches missing required fields."""
        config = {
            "test_command": "pytest tests/",
        }
        is_valid, errors = _basic_validation(config)
        assert not is_valid
        assert any("repo" in error for error in errors)

    def test_validate_and_report_valid(self, capsys):
        """Test validate_and_report with valid config."""
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest tests/",
        }
        result = validate_and_report(config, "test.json")
        assert result is True

        captured = capsys.readouterr()
        assert "❌" not in captured.out

    def test_validate_and_report_invalid(self, capsys):
        """Test validate_and_report with invalid config."""
        config = {
            "repo": "https://github.com/user/repo",
            # Missing test_command
        }
        result = validate_and_report(config, "test.json")
        assert result is False

        captured = capsys.readouterr()
        assert "❌" in captured.out
        assert "test.json" in captured.out
