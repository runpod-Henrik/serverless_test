"""
Configuration management for flaky test detector.
Loads settings from .flaky-detector.yml in the cloned repository.
"""

import os
from typing import Any

import yaml

DEFAULT_CONFIG = {
    "runs": 10,
    "parallelism": 4,
    "timeout": 300,
    "ignore_patterns": [],
    "severity_thresholds": {
        "critical": 0.9,
        "high": 0.5,
        "medium": 0.1,
        "low": 0.01,
    },
    "auto_install_dependencies": True,
    "pip_install_timeout": 300,
    "cleanup_on_failure": True,
    "preserve_temp_dir": False,
    "save_full_output": False,
    "max_error_length": 200,
    "random_seed_range": {"min": 1, "max": 1_000_000},
}


class Config:
    """Configuration manager for flaky test detector."""

    def __init__(self, config_dict: dict[str, Any] | None = None):
        """Initialize config with optional overrides."""
        self.config = DEFAULT_CONFIG.copy()
        if config_dict:
            self._merge_config(config_dict)

    def _merge_config(self, override: dict[str, Any]) -> None:
        """Merge override config into default config."""
        for key, value in override.items():
            if key in self.config:
                config_value = self.config[key]
                if isinstance(value, dict) and isinstance(config_value, dict):
                    # Deep merge for nested dicts
                    config_value.update(value)
                else:
                    self.config[key] = value

    @classmethod
    def load_from_file(cls, filepath: str = ".flaky-detector.yml") -> "Config":
        """Load configuration from YAML file."""
        if not os.path.exists(filepath):
            return cls()

        try:
            with open(filepath) as f:
                config_dict = yaml.safe_load(f) or {}
            return cls(config_dict)
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}")
            return cls()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)

    def get_severity(self, repro_rate: float) -> tuple[str, str]:
        """
        Get severity level and emoji for a given reproduction rate.

        Returns:
            tuple: (severity_level, emoji)
        """
        thresholds = self.config["severity_thresholds"]
        assert isinstance(thresholds, dict)

        if repro_rate >= thresholds["critical"]:
            return "CRITICAL", "🔴"
        elif repro_rate >= thresholds["high"]:
            return "HIGH", "🟠"
        elif repro_rate >= thresholds["medium"]:
            return "MEDIUM", "🟡"
        elif repro_rate >= thresholds["low"]:
            return "LOW", "🟢"
        else:
            return "NONE", "✅"

    def should_run_test(self, test_name: str) -> bool:
        """Check if test should be run based on ignore patterns."""
        import fnmatch

        ignore_patterns = self.config.get("ignore_patterns", [])
        assert isinstance(ignore_patterns, list)
        return all(not fnmatch.fnmatch(test_name, pattern) for pattern in ignore_patterns)

    def __repr__(self) -> str:
        return f"Config({self.config})"
