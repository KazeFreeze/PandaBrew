import json
from pathlib import Path
from typing import Dict, Any

CONFIG_FILE_NAME = ".panda_brew_config.json"

class ConfigManager:
    """
    Manages loading and saving of the application's configuration in a UI-agnostic way.
    """
    def __init__(self):
        self.config_file = Path.home() / CONFIG_FILE_NAME

    def load_app_state(self) -> Dict[str, Any]:
        """Loads the configuration from a JSON file."""
        try:
            if self.config_file.exists():
                with self.config_file.open("r") as f:
                    config = json.load(f)
                    if not isinstance(config, dict): return self.get_default_config()
                    # Ensure all essential keys are present
                    config.setdefault("open_tabs", [])
                    config.setdefault("active_tab_id", None)
                    config.setdefault("window_geometry", {})
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
            "active_tab_id": None,
            "window_geometry": {},
        }

    def save_app_state(self, app_state: Dict[str, Any]) -> None:
        """Saves the current application state to the JSON file."""
        try:
            # Clean up obsolete keys from older versions if they exist
            app_state.pop("selections", None)
            app_state.pop("include_mode", None)
            app_state.pop("filenames_only", None)
            app_state.pop("show_excluded_in_structure", None)

            with self.config_file.open("w") as f:
                json.dump(app_state, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")