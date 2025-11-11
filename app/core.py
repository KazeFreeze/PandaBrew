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
    all_files: Set[Path],
    processed_files: Set[Path],
    show_excluded: bool,
):
    f.write("### Project Structure\n\n")

    def build_tree(current_path, prefix=""):
        try:
            children = sorted(list(current_path.iterdir()), key=lambda p: (p.is_file(), p.name.lower()))
        except (IOError, PermissionError):
            return

        for i, child in enumerate(children):
            is_last = i == (len(children) - 1)
            connector = "└── " if is_last else "├── "

            is_processed = child in processed_files
            is_ancestor_of_processed = False
            if child.is_dir():
                is_ancestor_of_processed = any(p.is_relative_to(child) for p in processed_files)

            # If show_excluded is True, we show everything.
            # Otherwise, only show processed files or their parent directories.
            should_show = show_excluded or is_processed or is_ancestor_of_processed

            if not should_show:
                continue

            f.write(f"{prefix}{connector}{child.name}")

            if child.is_file():
                f.write(" [EXCLUDED]\n" if not is_processed else "\n")
            else:
                f.write("\n")

            if child.is_dir():
                # Recurse if the directory is an ancestor of a processed file,
                # or if we are showing all excluded files.
                if is_ancestor_of_processed or show_excluded:
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
    cancel_event: threading.Event
) -> Set[Path]:
    """
    Recursively gather all files, without any filtering.
    """
    files = set()
    if cancel_event.is_set() or not current_path.is_dir():
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
    if progress_callback: progress_callback(0, "Gathering all files...")

    all_files = _gather_files_recursively(source_path, cancel_event)
    if cancel_event.is_set(): return 0

    if progress_callback: progress_callback(10, "Filtering files...")

    files_to_process = set()
    for file_path in all_files:
        if cancel_event.is_set(): break
        relative_path = file_path.relative_to(source_path)

        # --- Filtering Logic ---
        # Rule 1: Include patterns always win.
        if _matches_pattern(relative_path, include_patterns):
            files_to_process.add(file_path)
            continue

        # Rule 2: Exclude patterns are checked next.
        if _matches_pattern(relative_path, exclude_patterns):
            continue

        # Rule 3: Check manual selections.
        is_manually_selected = any(
            str(file_path).startswith(str(p)) for p in manual_selections
        )

        if include_mode:
            # In include mode, we only add files that are manually selected
            # (assuming they haven't been filtered out by exclude patterns).
            if is_manually_selected:
                files_to_process.add(file_path)
        else: # Exclude mode
            # In exclude mode, we add all files EXCEPT those manually unchecked.
            # The 'manual_selections' in this mode are the ones to *exclude*.
            if not is_manually_selected:
                files_to_process.add(file_path)



    files_to_process_sorted = sorted(list(files_to_process))
    if cancel_event.is_set(): return 0

    with open(output_file, "w", encoding="utf-8", errors="ignore") as f:
        _write_report_header(f, include_mode)
        if progress_callback: progress_callback(25, "Writing project structure...")

        _write_project_structure(f, source_path, all_files, files_to_process, show_excluded)

        if not filenames_only:
            _write_file_contents(f, files_to_process_sorted, source_path, cancel_event, progress_callback)
    return len(files_to_process_sorted)
