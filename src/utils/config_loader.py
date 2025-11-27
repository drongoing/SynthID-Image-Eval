"""Configuration loader and manager for SynthID-Image-Eval."""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


class ConfigLoader:
    """Load and manage configuration settings."""

    def __init__(self, config_path: str = None):
        """
        Initialize the configuration loader.

        Args:
            config_path: Path to the configuration YAML file.
                        If None, looks for config/config.yaml
        """
        if config_path is None:
            # Try to find config.yaml in the config directory
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}

        # Load environment variables from .env file if it exists
        load_dotenv()

        self._load_config()

    def _load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found at {self.config_path}. "
                f"Please copy config.example.yaml to config.yaml and fill in your settings."
            )

        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Override with environment variables if they exist
        self._override_with_env()

    def _override_with_env(self):
        """Override configuration with environment variables."""
        # Google Cloud settings
        if os.getenv('GOOGLE_CLOUD_PROJECT'):
            self.config.setdefault('google_cloud', {})
            self.config['google_cloud']['project_id'] = os.getenv('GOOGLE_CLOUD_PROJECT')

        if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            self.config.setdefault('google_cloud', {})
            self.config['google_cloud']['credentials_path'] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

        # API Keys
        if os.getenv('GEMINI_API_KEY'):
            self.config.setdefault('api_keys', {})
            self.config['api_keys']['gemini_api_key'] = os.getenv('GEMINI_API_KEY')

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key_path: Dot-separated path to the config value (e.g., 'google_cloud.project_id')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_google_cloud_config(self) -> Dict[str, str]:
        """Get Google Cloud configuration."""
        return self.config.get('google_cloud', {})

    def get_api_keys(self) -> Dict[str, str]:
        """Get API keys configuration."""
        return self.config.get('api_keys', {})

    def get_generation_config(self) -> Dict[str, Any]:
        """Get image generation configuration."""
        return self.config.get('generation', {})

    def get_transformation_config(self) -> Dict[str, Any]:
        """Get transformation configuration."""
        return self.config.get('transformations', {})

    def get_detection_config(self) -> Dict[str, Any]:
        """Get detection configuration."""
        return self.config.get('detection', {})

    def get_testing_config(self) -> Dict[str, Any]:
        """Get testing configuration."""
        return self.config.get('testing', {})

    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration."""
        return self.config.get('output', {})

    def get_experiment_config(self) -> Dict[str, Any]:
        """Get experiment configuration."""
        return self.config.get('experiment', {})


# Singleton instance
_config_instance = None


def get_config(config_path: str = None) -> ConfigLoader:
    """
    Get the global configuration instance.

    Args:
        config_path: Path to configuration file (only used on first call)

    Returns:
        ConfigLoader instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader(config_path)
    return _config_instance
