import json
import hashlib
from pathlib import Path
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .app import ModernCodeExtractorGUI


CONFIG_FILE_NAME = ".code_extractor_pro_config.json"


class ConfigManager:
    """
    Manages loading and saving of the application's configuration,
    now supporting multiple open tabs and persistent selections.
    """

    def __init__(self, app_instance: "ModernCodeExtractorGUI"):
        """
        Initializes the ConfigManager.
        """
        self.app = app_instance
        self.config_file = Path.home() / CONFIG_FILE_NAME

    def load_app_state(self) -> Dict[str, Any]:
        """
        Loads the configuration from a JSON file.
        If the file doesn't exist or is invalid, it creates a default configuration.
        """
        try:
            if self.config_file.exists():
                with self.config_file.open("r") as f:
                    config = json.load(f)
                    if not isinstance(config, dict):
                        return self.get_default_config()
                    # Ensure essential keys exist
                    config.setdefault("selections", {})
                    config.setdefault("open_tabs", [])
                    return config
            else:
                return self.get_default_config()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config, resetting to default: {e}")
            return self.get_default_config()

    def get_default_config(self) -> Dict[str, Any]:
        """
        Returns a dictionary with the default configuration settings.
        """
        return {
            "open_tabs": [],
            "last_output": "",
            "selections": {},
            "include_mode": True,
            "filenames_only": False,
        }

    def save_app_state(self) -> None:
        """
        Saves the current application state to the JSON file.
        This includes all open tab paths and current selections for all tabs.
        """
        try:
            for tab_data in self.app.tabs.values():
                if tab_data["source_path"].get():
                    self.save_selections(tab_data)

            open_tab_paths = [
                t["source_path"].get()
                for t in self.app.tabs.values()
                if t["source_path"].get()
            ]

            recent_tab_paths = open_tab_paths[-10:]

            config_to_save = {
                "open_tabs": recent_tab_paths,
                "last_output": self.app.output_path.get(),
                "selections": self.app.config.get("selections", {}),
                "include_mode": self.app.include_mode.get(),
                "filenames_only": self.app.filenames_only.get(),
            }

            with self.config_file.open("w") as f:
                json.dump(config_to_save, f, indent=2)
                print(f"Config saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")

    def save_selections(self, tab_data: Dict[str, Any]) -> None:
        """
        Saves the current checked paths for a given tab's source directory.
        The paths are stored relative to the source directory root.
        """
        source_path_str = tab_data["source_path"].get()
        if not source_path_str:
            return

        source_hash = hashlib.md5(source_path_str.encode()).hexdigest()
        tree_manager = tab_data["tree_view_manager"]
        source_path = Path(source_path_str)

        relative_checked_paths = [
            str(Path(p).relative_to(source_path)) for p in tree_manager.checked_paths
        ]

        if "selections" not in self.app.config:
            self.app.config["selections"] = {}

        self.app.config["selections"][source_hash] = sorted(relative_checked_paths)

    def load_selections(self, tab_data: Dict[str, Any]) -> None:
        """
        Loads the saved checked paths for a given tab's source directory
        and populates the TreeViewManager's checked_paths set.
        """
        source_path_str = tab_data["source_path"].get()
        if not source_path_str:
            return

        source_hash = hashlib.md5(source_path_str.encode()).hexdigest()
        selections = self.app.config.get("selections", {}).get(source_hash, [])

        if not selections:
            return

        tree_manager = tab_data["tree_view_manager"]
        source_path = Path(source_path_str)

        tree_manager.checked_paths.clear()
        for rel_path in selections:
            full_path = source_path / rel_path
            tree_manager.checked_paths.add(str(full_path))
