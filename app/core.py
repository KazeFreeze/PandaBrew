import datetime
import fnmatch
from pathlib import Path
from typing import List, Set, Optional, Callable, IO
import threading

def _matches_pattern(path: Path, patterns: List[str]) -> bool:
    path_str = str(path)
    for pattern in patterns:
        if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path.name, pattern):
            return True
    return False

def _write_report_header(f: IO[str], include_mode: bool):
    mode = "INCLUDE" if include_mode else "EXCLUDE"
    f.write("--- Project Extraction Report ---\n")
    f.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
    f.write(f"Selection Mode: {mode} checked items\n")
    f.write("---\n\n")

def _write_project_structure(
    f: IO[str],
    source_path: Path,
    files_to_process: Set[Path],
    show_excluded: bool,
    all_files: Optional[Set[Path]] = None,
):
    f.write("### Project Structure\n\n")
    if all_files is None:
        all_files = set()

    def build_tree(current_path, prefix=""):
        try:
            children = sorted(list(current_path.iterdir()), key=lambda p: (p.is_file(), p.name.lower()))
        except (IOError, PermissionError):
            return

        for i, child in enumerate(children):
            is_last = i == (len(children) - 1)
            connector = "└── " if is_last else "├── "
            is_processed = child in files_to_process

            is_parent_of_processed = False
            if child.is_dir():
                is_parent_of_processed = any(p.is_relative_to(child) for p in files_to_process)

            # A file is considered for showing if it's processed, a parent of a processed file,
            # or if show_excluded is True and it's a file that was filtered out.
            is_explicitly_excluded = show_excluded and child.is_file() and child in all_files and not is_processed

            should_show = is_processed or is_parent_of_processed or is_explicitly_excluded

            if not should_show:
                if show_excluded and child.is_dir() and any(p.is_relative_to(child) for p in all_files):
                    pass
                else:
                    continue

            f.write(f"{prefix}{connector}{child.name}")

            if child.is_file():
                if not is_processed:
                    f.write(" [EXCLUDED]\n")
                else:
                    f.write("\n")
            else:
                f.write("\n")

            if child.is_dir():
                new_prefix = prefix + ("    " if is_last else "│   ")
                build_tree(child, new_prefix)

    f.write(f"{source_path.name}\n")
    build_tree(source_path)
    f.write("\n")

def _write_file_contents(
    f: IO[str],
    files_to_process: List[Path],
    source_path: Path,
    cancel_event: threading.Event,
    progress_callback: Optional[Callable[[float, str], None]] = None,
):
    f.write("### File Contents\n\n")
    total_files = len(files_to_process)
    for i, path in enumerate(files_to_process):
        if cancel_event.is_set(): return
        if progress_callback:
            progress = 25 + ((i / total_files) * 75 if total_files > 0 else 75)
            status = f"Writing {i + 1}/{total_files}: {path.name}"
            progress_callback(progress, status)
        rel_path = path.relative_to(source_path)
        f.write(f"--- file: {rel_path} ---\n")
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            f.write(content.strip() + "\n")
        except Exception as read_error:
            f.write(f"[Error reading file: {read_error}]\n")
        f.write("---\n\n")

def _gather_files_recursively(
    current_path: Path,
    cancel_event: threading.Event,
) -> Set[Path]:
    """
    Recursively gather all files from a starting path.
    """
    files = set()
    if cancel_event.is_set():
        return files

    try:
        for path in current_path.iterdir():
            if cancel_event.is_set():
                break
            if path.is_dir():
                files.update(_gather_files_recursively(path, cancel_event))
            elif path.is_file():
                files.add(path)
    except (IOError, PermissionError):
        pass
    return files


def generate_report_to_file(
    output_file: str,
    source_path_str: str,
    include_mode: bool,
    manual_selections_str: Set[str],
    include_patterns: List[str],
    exclude_patterns: List[str],
    filenames_only: bool,
    show_excluded: bool,
    cancel_event: threading.Event,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> int:
    source_path = Path(source_path_str)
    manual_selections = {Path(p) for p in manual_selections_str}
    if progress_callback: progress_callback(0, "Gathering and filtering files...")

    all_files = _gather_files_recursively(source_path, cancel_event)

    # Apply filters: (Base - Excluded) + Included
    included_by_pattern = {f for f in all_files if _matches_pattern(f.relative_to(source_path), include_patterns)}
    excluded_by_pattern = {f for f in all_files if _matches_pattern(f.relative_to(source_path), exclude_patterns)}

    files_to_process = set()
    if include_mode:
        base_files = set()
        if manual_selections:
            for item in manual_selections:
                if item.is_dir():
                    base_files.update(f for f in all_files if f.is_relative_to(item))
                elif item.is_file() and item in all_files:
                    base_files.add(item)
        else:
            # If no manual selections, the base is determined by include patterns.
            base_files = included_by_pattern

        files_to_process = (base_files - excluded_by_pattern) | included_by_pattern
    else:  # Exclude mode
        base_files = all_files
        manually_excluded = set()
        for item in manual_selections:
            if item.is_dir():
                manually_excluded.update(f for f in all_files if f.is_relative_to(item))
            elif item.is_file() and item in all_files:
                manually_excluded.add(item)

        files_to_process = (base_files - excluded_by_pattern - manually_excluded) | included_by_pattern

    files_to_process_sorted = sorted(list(files_to_process))
    if cancel_event.is_set(): return 0

    with open(output_file, "w", encoding="utf-8", errors="ignore") as f:
        _write_report_header(f, include_mode)
        if progress_callback: progress_callback(25, "Writing project structure...")

        _write_project_structure(f, source_path, files_to_process, show_excluded, all_files=all_files)

        if not filenames_only:
            _write_file_contents(f, files_to_process_sorted, source_path, cancel_event, progress_callback)
    return len(files_to_process_sorted)
