"""
Configuration management for flaky test detector.
Loads settings from .flaky-detector.yml in the cloned repository.
"""
import os
import yaml
from typing import Dict, Any, Optional


DEFAULT_CONFIG = {
    "runs": 100,
    "parallelism": 10,
    "timeout": 600,
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

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """Initialize config with optional overrides."""
        self.config = DEFAULT_CONFIG.copy()
        if config_dict:
            self._merge_config(config_dict)

    def _merge_config(self, override: Dict[str, Any]):
        """Merge override config into default config."""
        for key, value in override.items():
            if key in self.config:
                if isinstance(value, dict) and isinstance(self.config[key], dict):
                    # Deep merge for nested dicts
                    self.config[key].update(value)
                else:
                    self.config[key] = value

    @classmethod
    def load_from_file(cls, filepath: str = ".flaky-detector.yml") -> "Config":
        """Load configuration from YAML file."""
        if not os.path.exists(filepath):
            return cls()

        try:
            with open(filepath, "r") as f:
                config_dict = yaml.safe_load(f) or {}
            return cls(config_dict)
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}")
            return cls()

    def get(self, key: str, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)

    def get_severity(self, repro_rate: float) -> tuple[str, str]:
        """
        Get severity level and emoji for a given reproduction rate.

        Returns:
            tuple: (severity_level, emoji)
        """
        thresholds = self.config["severity_thresholds"]

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
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(test_name, pattern):
                return False
        return True

    def __repr__(self):
        return f"Config({self.config})"
