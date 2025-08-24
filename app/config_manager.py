import json
import hashlib
from pathlib import Path
from typing import Dict, Any, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .app import ModernCodeExtractorGUI


CONFIG_FILE_NAME = ".panda_brew_config.json"


class ConfigManager:
    """
    Manages loading and saving of the application's configuration.
    - Supports multiple tabs with per-tab output paths.
    - Saves separate include/exclude selections for each project.
    - Handles global include/exclude filter patterns.
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
                    # Ensure essential keys exist for backward compatibility
                    config.setdefault("selections", {})
                    config.setdefault("open_tabs", [])
                    config.setdefault("active_tab_source", None)
                    config.setdefault("global_include_patterns", "")
                    config.setdefault("global_exclude_patterns", "")
                    config.setdefault("show_excluded_in_structure", True)
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
            "selections": {},
            "include_mode": True,
            "filenames_only": False,
            "show_excluded_in_structure": True,
            "active_tab_source": None,
            "global_include_patterns": "# Examples:\n# *.py\n# src/**/*.js",
            "global_exclude_patterns": "# Examples:\n# .git\n# __pycache__\n# *.log",
        }

    def save_app_state(self) -> None:
        """
        Saves the current application state to the JSON file.
        This includes open tabs, selections, and global filter patterns.
        """
        try:
            # Ensure selections for all open tabs are saved before writing config
            for tab_data in self.app.tabs.values():
                if tab_data["source_path"].get():
                    self.save_selections(tab_data)

            open_tabs_info = [
                {
                    "source": t["source_path"].get(),
                    "output": t["output_path"].get(),
                }
                for t in self.app.tabs.values()
                if t["source_path"].get()
            ]

            active_tab = self.app.get_active_tab()
            active_tab_source = (
                active_tab["source_path"].get()
                if active_tab and active_tab["source_path"].get()
                else None
            )

            # Prepare the configuration dictionary to be saved
            config_to_save = {
                "open_tabs": open_tabs_info[-10:],  # Save last 10 tabs
                "selections": self.app.config.get("selections", {}),
                "include_mode": self.app.include_mode.get(),
                "filenames_only": self.app.filenames_only.get(),
                "show_excluded_in_structure": self.app.show_excluded_in_structure.get(),
                "active_tab_source": active_tab_source,
                "global_include_patterns": self.app.global_include_patterns.get(
                    "1.0", "end-1c"
                )
                if self.app.global_include_patterns
                else "",
                "global_exclude_patterns": self.app.global_exclude_patterns.get(
                    "1.0", "end-1c"
                )
                if self.app.global_exclude_patterns
                else "",
            }

            with self.config_file.open("w") as f:
                json.dump(config_to_save, f, indent=2)
                print(f"Config saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")

    def save_selections(self, tab_data: Dict[str, Any]) -> None:
        """
        Saves the current checked paths for a tab's source directory,
        storing them based on the current selection mode (include/exclude).
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

        # Ensure the project entry is a dictionary
        if source_hash not in self.app.config["selections"] or not isinstance(
            self.app.config["selections"][source_hash], dict
        ):
            self.app.config["selections"][source_hash] = {
                "include_checked": [],
                "exclude_checked": [],
            }

        # Determine which key to save to based on the current mode
        mode_key = (
            "include_checked" if self.app.include_mode.get() else "exclude_checked"
        )
        self.app.config["selections"][source_hash][mode_key] = sorted(
            relative_checked_paths
        )

    def load_selections(self, tab_data: Dict[str, Any]) -> None:
        """
        Loads checked paths for a tab's source directory based on the current
        selection mode, gracefully migrating old config formats if needed.
        """
        source_path_str = tab_data["source_path"].get()
        if not source_path_str:
            return

        source_hash = hashlib.md5(source_path_str.encode()).hexdigest()
        project_selections = self.app.config.get("selections", {}).get(source_hash)

        # Gracefully handle migration from old format (list) to new (dict)
        if isinstance(project_selections, list):
            project_selections = {
                "include_checked": project_selections,
                "exclude_checked": [],
            }
            self.app.config["selections"][source_hash] = project_selections

        tree_manager = tab_data["tree_view_manager"]
        tree_manager.checked_paths.clear()

        if not isinstance(project_selections, dict):
            return  # No valid selection data found

        # Determine which list of selections to load
        mode_key = (
            "include_checked" if self.app.include_mode.get() else "exclude_checked"
        )
        selections = project_selections.get(mode_key, [])

        source_path = Path(source_path_str)
        for rel_path in selections:
            full_path = source_path / rel_path
            tree_manager.checked_paths.add(str(full_path))
