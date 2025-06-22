import json
import hashlib
from pathlib import Path


class ConfigManager:
    """
    Manages loading and saving of the application's configuration,
    including recent paths and user selections.
    """

    def __init__(self, app_instance):
        """
        Initializes the ConfigManager.

        Args:
            app_instance: An instance of the main application class.
        """
        self.app = app_instance
        self.config_file = Path.home() / ".code_extractor_config.json"

    def load_config(self):
        """
        Loads the configuration from a JSON file.
        If the file doesn't exist, it creates a default configuration.

        Returns:
            dict: The loaded or default configuration.
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    if "selections" not in config:
                        config["selections"] = {}
                    for key in ["recent_sources", "recent_outputs"]:
                        if key in config:
                            config[key] = config[key][-10:]
                    return config
            else:
                return self.get_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.get_default_config()

    def get_default_config(self):
        """
        Returns a dictionary with the default configuration settings.

        Returns:
            dict: The default configuration.
        """
        return {
            "last_source": "",
            "last_output": "",
            "recent_sources": [],
            "recent_outputs": [],
            "selections": {},
        }

    def save_config(self):
        """
        Saves the current configuration to the JSON file.
        This includes the last used paths and current selections.
        """
        try:
            self.app.config["last_source"] = self.app.source_path.get()
            self.app.config["last_output"] = self.app.output_path.get()

            if self.app.source_path.get():
                self.save_selections()

            for path_var, config_key in [
                (self.app.source_path, "recent_sources"),
                (self.app.output_path, "recent_outputs"),
            ]:
                if path_var.get():
                    if config_key not in self.app.config:
                        self.app.config[config_key] = []
                    if path_var.get() in self.app.config[config_key]:
                        self.app.config[config_key].remove(path_var.get())
                    self.app.config[config_key].append(path_var.get())
                    self.app.config[config_key] = self.app.config[config_key][-10:]

            with open(self.config_file, "w") as f:
                json.dump(self.app.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def save_selections(self):
        """
        Saves the current state of checkboxes in the tree view for the current source directory.
        """
        if not self.app.source_path.get():
            return

        source_hash = hashlib.md5(self.app.source_path.get().encode()).hexdigest()
        selections = {}

        for path_str, tree_item in self.app.tree_view_manager.tree_items.items():
            if tree_item.checked.get():
                try:
                    rel_path = str(
                        Path(path_str).relative_to(self.app.source_path.get())
                    )
                    selections[rel_path] = True
                except ValueError:
                    pass

        self.app.config["selections"][source_hash] = selections

    def load_selections(self):
        """
        Loads and applies the saved checkbox selections for the current source directory.
        """
        if not self.app.source_path.get():
            return

        source_hash = hashlib.md5(self.app.source_path.get().encode()).hexdigest()
        selections = self.app.config.get("selections", {}).get(source_hash, {})

        for rel_path, checked in selections.items():
            try:
                full_path = str(Path(self.app.source_path.get()) / rel_path)
                if full_path in self.app.tree_view_manager.tree_items:
                    self.app.tree_view_manager.tree_items[full_path].checked.set(
                        checked
                    )
            except Exception:
                pass
