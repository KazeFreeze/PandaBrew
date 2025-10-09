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
    def __init__(self, app_instance: "MainWindow"):
        self.app = app_instance
        self.config_file = Path.home() / CONFIG_FILE_NAME

    def load_app_state(self) -> Dict[str, Any]:
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

    def save_app_state(self) -> None:
        """Saves the current application state to the JSON file."""
        try:
            for tab_data in self.app.tabs.values():
                if tab_data["control_panel"].source_path.text():
                    self.save_selections(tab_data)

            open_tabs_info = []
            for t in self.app.tabs.values():
                cp = t["control_panel"]
                if not cp.source_path.text(): continue

                open_tabs_info.append({
                    "source": cp.source_path.text(),
                    "output": cp.output_path.text(),
                    "include_patterns": cp.include_patterns_text.toPlainText(),
                    "exclude_patterns": cp.exclude_patterns_text.toPlainText(),
                })

            active_tab = self.app.get_active_tab()
            active_tab_source = active_tab["control_panel"].source_path.text() if active_tab else None

            config_to_save = {
                "open_tabs": open_tabs_info[-10:],
                "selections": self.app.config.get("selections", {}),
                "include_mode": self.app.include_mode,
                "filenames_only": self.app.filenames_only,
                "show_excluded_in_structure": self.app.show_excluded_in_structure,
                "active_tab_source": active_tab_source,
            }

            with self.config_file.open("w") as f:
                json.dump(config_to_save, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def save_selections(self, tab_data: Dict[str, Any]) -> None:
        """Saves the current checked paths for a tab's source directory."""
        source_path_str = tab_data["control_panel"].source_path.text()
        if not source_path_str: return

        source_hash = hashlib.md5(source_path_str.encode()).hexdigest()
        tree_manager = tab_data["tree_view_manager"]
        relative_checked_paths = [str(Path(p).relative_to(source_path_str)) for p in tree_manager.get_checked_paths()]

        if "selections" not in self.app.config:
            self.app.config["selections"] = {}

        if source_hash not in self.app.config["selections"] or not isinstance(self.app.config["selections"][source_hash], dict):
            self.app.config["selections"][source_hash] = {"include_checked": [], "exclude_checked": []}

        mode_key = "include_checked" if self.app.include_mode else "exclude_checked"
        self.app.config["selections"][source_hash][mode_key] = sorted(relative_checked_paths)

    def load_selections(self, tab_data: Dict[str, Any]) -> None:
        """Loads checked paths for a tab's source directory based on the current mode."""
        source_path_str = tab_data["control_panel"].source_path.text()
        if not source_path_str: return

        source_hash = hashlib.md5(source_path_str.encode()).hexdigest()
        project_selections = self.app.config.get("selections", {}).get(source_hash)

        if isinstance(project_selections, list):
            project_selections = {"include_checked": project_selections, "exclude_checked": []}
            self.app.config["selections"][source_hash] = project_selections

        tree_manager = tab_data["tree_view_manager"]
        # This part of the logic might need to be more sophisticated,
        # for now, we just get the paths. The UI doesn't yet use this to set checks.

        if not isinstance(project_selections, dict): return

        mode_key = "include_checked" if self.app.include_mode else "exclude_checked"
        selections = project_selections.get(mode_key, [])

        # The logic to apply these loaded selections to the QTreeView would need to be added.
        # For now, this method doesn't crash, but it doesn't visually update the tree.
        source_path = Path(source_path_str)
        # tree_manager.checked_paths = {str(source_path / rel_path) for rel_path in selections}
