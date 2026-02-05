"""
Tests for configuration management.
"""

import os
import tempfile

from config import Config


class TestConfig:
    """Test configuration loading and management."""

    def test_default_config(self) -> None:
        """Test default configuration is loaded."""
        config = Config()
        assert config.get("runs") == 10
        assert config.get("parallelism") == 4
        assert config.get("timeout") == 300

    def test_config_override(self) -> None:
        """Test configuration can be overridden."""
        config = Config({"runs": 200, "parallelism": 20})
        assert config.get("runs") == 200
        assert config.get("parallelism") == 20
        assert config.get("timeout") == 300  # Should keep default

    def test_nested_config_merge(self) -> None:
        """Test nested dictionaries are merged properly."""
        config = Config({"severity_thresholds": {"critical": 0.95, "high": 0.6}})
        thresholds = config.get("severity_thresholds")
        assert thresholds["critical"] == 0.95  # Overridden
        assert thresholds["high"] == 0.6  # Overridden
        assert thresholds["medium"] == 0.1  # Kept from default

    def test_load_from_yaml_file(self) -> None:
        """Test loading configuration from YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("runs: 150\n")
            f.write("parallelism: 15\n")
            f.write("severity_thresholds:\n")
            f.write("  critical: 0.95\n")
            temp_path = f.name

        try:
            config = Config.load_from_file(temp_path)
            assert config.get("runs") == 150
            assert config.get("parallelism") == 15
            assert config.get("severity_thresholds")["critical"] == 0.95
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_file(self) -> None:
        """Test loading from non-existent file returns defaults."""
        config = Config.load_from_file("nonexistent.yml")
        assert config.get("runs") == 10  # Should be default

    def test_get_severity_critical(self) -> None:
        """Test severity classification for critical level."""
        config = Config()
        severity, emoji = config.get_severity(0.95)
        assert severity == "CRITICAL"
        assert emoji == "🔴"

    def test_get_severity_high(self) -> None:
        """Test severity classification for high level."""
        config = Config()
        severity, emoji = config.get_severity(0.7)
        assert severity == "HIGH"
        assert emoji == "🟠"

    def test_get_severity_medium(self) -> None:
        """Test severity classification for medium level."""
        config = Config()
        severity, emoji = config.get_severity(0.3)
        assert severity == "MEDIUM"
        assert emoji == "🟡"

    def test_get_severity_low(self) -> None:
        """Test severity classification for low level."""
        config = Config()
        severity, emoji = config.get_severity(0.05)
        assert severity == "LOW"
        assert emoji == "🟢"

    def test_get_severity_none(self) -> None:
        """Test severity classification for none level."""
        config = Config()
        severity, emoji = config.get_severity(0.0)
        assert severity == "NONE"
        assert emoji == "✅"

    def test_custom_severity_thresholds(self) -> None:
        """Test custom severity thresholds work."""
        config = Config(
            {
                "severity_thresholds": {
                    "critical": 0.95,
                    "high": 0.7,
                    "medium": 0.2,  # Raised threshold
                    "low": 0.05,
                }
            }
        )
        # 10% should now be LOW (between 0.05 and 0.2)
        severity, _ = config.get_severity(0.1)
        assert severity == "LOW"

    def test_should_run_test_no_patterns(self) -> None:
        """Test all tests run when no ignore patterns."""
        config = Config()
        assert config.should_run_test("test_anything")
        assert config.should_run_test("test_another")

    def test_should_run_test_with_patterns(self) -> None:
        """Test ignore patterns work."""
        config = Config({"ignore_patterns": ["test_flaky_*", "*_integration"]})
        assert not config.should_run_test("test_flaky_something")
        assert not config.should_run_test("test_something_integration")
        assert config.should_run_test("test_normal")

    def test_config_get_with_default(self) -> None:
        """Test getting config value with default fallback."""
        config = Config()
        assert config.get("nonexistent", "default_value") == "default_value"
        assert config.get("runs", 999) == 10  # Should return actual value

    def test_invalid_yaml_returns_default(self) -> None:
        """Test invalid YAML file returns default config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("invalid: yaml: content: here:\n")
            temp_path = f.name

        try:
            config = Config.load_from_file(temp_path)
            # Should fall back to defaults
            assert config.get("runs") == 10
        finally:
            os.unlink(temp_path)
