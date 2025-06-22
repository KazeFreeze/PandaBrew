import json
import hashlib
from pathlib import Path


class ConfigManager:
    """
    Manages loading and saving of the application's configuration,
    now supporting multiple open tabs and persistent selections.
    """

    def __init__(self, app_instance):
        self.app = app_instance
        self.config_file = Path.home() / ".code_extractor_pro_config.json"

    def load_config(self):
        """
        Loads the configuration from a JSON file.
        If the file doesn't exist or is invalid, it creates a default configuration.
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    if not isinstance(config, dict):
                        return self.get_default_config()
                    if "selections" not in config:
                        config["selections"] = {}
                    if "open_tabs" not in config:
                        config["open_tabs"] = []
                    return config
            else:
                return self.get_default_config()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config, resetting to default: {e}")
            return self.get_default_config()

    def get_default_config(self):
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

    def save_config(self):
        """
        Saves the current configuration to the JSON file.
        This includes all open tab paths and current selections for all tabs.
        """
        try:
            for tab_data in self.app.tabs.values():
                if tab_data["source_path"].get():
                    self.save_selections(tab_data)

            tab_paths = []
            for t in self.app.tabs.values():
                path = t["source_path"].get()
                if path and isinstance(path, str):
                    tab_paths.append(path)

            # MODIFIED: Limit saved tabs to the most recent 10
            recent_tab_paths = tab_paths[-10:]

            config_to_save = {
                "open_tabs": recent_tab_paths,
                "last_output": self.app.output_path.get(),
                "selections": self.app.config.get("selections", {}),
                "include_mode": self.app.include_mode.get(),
                "filenames_only": self.app.filenames_only.get(),
            }

            with open(self.config_file, "w") as f:
                json.dump(config_to_save, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def save_selections(self, tab_data):
        """
        Saves the current state of checkboxes in the tree view for a given tab's source directory.
        """
        source_path_str = tab_data["source_path"].get()
        if not source_path_str:
            return

        source_hash = hashlib.md5(source_path_str.encode()).hexdigest()
        selections = {}

        for path_str, tree_item in tab_data["tree_view_manager"].tree_items.items():
            if tree_item.checked.get():
                try:
                    rel_path = str(Path(path_str).relative_to(source_path_str))
                    selections[rel_path] = True
                except ValueError:
                    pass

        if "selections" not in self.app.config:
            self.app.config["selections"] = {}
        self.app.config["selections"][source_hash] = selections

    def load_selections(self, tab_data):
        """
        Loads and applies the saved checkbox selections for a given tab's source directory.
        """
        source_path_str = tab_data["source_path"].get()
        if not source_path_str:
            return

        source_hash = hashlib.md5(source_path_str.encode()).hexdigest()
        selections = self.app.config.get("selections", {}).get(source_hash, {})

        if not selections:
            return

        tree_manager = tab_data["tree_view_manager"]
        for rel_path, checked in selections.items():
            full_path = str(Path(source_path_str) / rel_path)
            if full_path in tree_manager.tree_items:
                tree_manager.tree_items[full_path].checked.set(checked)
