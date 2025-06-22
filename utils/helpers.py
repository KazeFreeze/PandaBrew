from pathlib import Path


def format_file_size(size):
    """
    Formats a file size in bytes into a human-readable string.

    Args:
        size (int): The size of the file in bytes.

    Returns:
        str: A formatted string representing the file size (e.g., "1.2 MB").
    """
    if size < 1024:
        return f"{size} B"
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def get_language_for_highlighting(suffix):
    """
    This function is no longer used for the output file but kept for potential future use.
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
