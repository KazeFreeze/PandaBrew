import json
import hashlib
from pathlib import Path
from typing import Dict, Any, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .qt_app.main_window import MainWindow

CONFIG_FILE_NAME = ".panda_brew_config.json"

class ConfigManager:
    """
    Manages loading and saving of the application's configuration.
    """
    def __init__(self):
        self.config_file = Path.home() / CONFIG_FILE_NAME
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Loads the configuration from a JSON file."""
        try:
            if self.config_file.exists():
                with self.config_file.open("r") as f:
                    config = json.load(f)
                    if not isinstance(config, dict): return self.get_default_config()
                    config.setdefault("selections", {})
                    config.setdefault("open_tabs", [])
                    config.setdefault("active_tab_source", None)
                    config.setdefault("include_mode", True)
                    config.setdefault("filenames_only", False)
                    config.setdefault("show_excluded_in_structure", True)
                    return config
            else:
                return self.get_default_config()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config, resetting to default: {e}")
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """Returns a dictionary with the default configuration settings."""
        return {
            "open_tabs": [],
            "selections": {},
            "include_mode": True,
            "filenames_only": False,
            "show_excluded_in_structure": True,
            "active_tab_source": None,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Gets a value from the config."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Sets a value in the config."""
        self.config[key] = value

    def save_config(self) -> None:
        """Saves the current config to the JSON file."""
        try:
            with self.config_file.open("w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
