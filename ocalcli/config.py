"""Configuration management for ocalcli."""

import os
from pathlib import Path
from typing import Optional

import toml
from platformdirs import user_config_dir

from .timeutils import get_system_timezone


class Config:
    """Configuration manager for ocalcli."""
    
    def __init__(self):
        """Initialize configuration."""
        self.config_dir = Path(user_config_dir("ocalcli", "ocalcli"))
        self.config_file = self.config_dir / "config.toml"
        self._config_data = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._config_data = toml.load(f)
            except (toml.TomlDecodeError, OSError) as e:
                print(f"Warning: Could not load config file: {e}")
                self._config_data = {}
    
    def save_config(self) -> None:
        """Save configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                toml.dump(self._config_data, f)
        except OSError as e:
            print(f"Error: Could not save config file: {e}")
            raise
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value with environment variable override.
        
        Args:
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        # Check environment variable first
        env_key = f"OCALCLI_{key.upper()}"
        if env_value := os.getenv(env_key):
            return env_value
        
        # Check config file
        return self._config_data.get(key, default)
    
    def set(self, key: str, value: str) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config_data[key] = value
    
    @property
    def client_id(self) -> Optional[str]:
        """Get Azure app registration client ID."""
        return self.get("client_id")
    
    @client_id.setter
    def client_id(self, value: str) -> None:
        """Set Azure app registration client ID."""
        self.set("client_id", value)
    
    @property
    def tenant(self) -> str:
        """Get Azure tenant ID."""
        return self.get("tenant", "organizations")
    
    @tenant.setter
    def tenant(self, value: str) -> None:
        """Set Azure tenant ID."""
        self.set("tenant", value)
    
    @property
    def timezone(self) -> str:
        """Get default timezone."""
        return self.get("timezone", get_system_timezone())
    
    @timezone.setter
    def timezone(self, value: str) -> None:
        """Set default timezone."""
        self.set("timezone", value)
    
    @property
    def calendar_id(self) -> Optional[str]:
        """Get default calendar ID."""
        return self.get("calendar_id")
    
    @calendar_id.setter
    def calendar_id(self, value: str) -> None:
        """Set default calendar ID."""
        self.set("calendar_id", value)
    
    def is_configured(self) -> bool:
        """Check if basic configuration is complete.
        
        Returns:
            True if configured, False otherwise
        """
        return bool(self.client_id)
    
    def get_provider_config(self) -> dict:
        """Get provider-specific configuration.
        
        Returns:
            Dictionary of provider configuration
        """
        return {
            "client_id": self.client_id,
            "tenant": self.tenant,
            "calendar_id": self.calendar_id
        }