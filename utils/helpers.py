def get_file_icon(path):
    """
    Returns an emoji icon based on the file's extension.

    Args:
        path (Path): The path of the file.

    Returns:
        str: An emoji representing the file type.
    """
    suffix = path.suffix.lower()
    icon_map = {
        ".py": "🐍",
        ".js": "📜",
        ".html": "🌐",
        ".css": "🎨",
        ".json": "📋",
        ".txt": "📄",
        ".md": "📝",
        ".yml": "⚙️",
        ".yaml": "⚙️",
        ".xml": "📰",
        ".png": "🖼️",
        ".jpg": "🖼️",
        ".jpeg": "🖼️",
        ".gif": "🖼️",
        ".svg": "🖼️",
        ".zip": "📦",
        ".tar": "📦",
        ".gz": "📦",
        ".rar": "📦",
        ".exe": "⚙️",
        ".bat": "⚙️",
        ".sh": "⚙️",
    }
    return icon_map.get(suffix, "📄")


def format_file_size(size):
    """
    Formats a file size in bytes into a human-readable string.

    Args:
        size (int): The size of the file in bytes.

    Returns:
        str: A formatted string representing the file size (e.g., "1.2 MB").
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def get_language_for_highlighting(suffix):
    """
    Gets the language identifier for syntax highlighting in Markdown.

    Args:
        suffix (str): The file extension.

    Returns:
        str: The language identifier (e.g., "python", "javascript").
    """
    lang_map = {
        ".py": "python",
        ".js": "javascript",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".xml": "xml",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".sh": "bash",
        ".bat": "batch",
        ".ps1": "powershell",
        ".c": "c",
        ".cpp": "cpp",
        ".java": "java",
        ".cs": "csharp",
        ".php": "php",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
        ".sql": "sql",
        ".md": "markdown",
    }
    return lang_map.get(suffix.lower(), "text")
