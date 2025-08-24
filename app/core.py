import datetime
import fnmatch
from pathlib import Path
from typing import List, Set, Optional, Callable, IO
import threading

def _matches_pattern(path: Path, patterns: List[str]) -> bool:
    """
    Checks if a path or its name matches any of the gitignore-style patterns.
    """
    path_str = str(path)
    for pattern in patterns:
        if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path.name, pattern):
            return True
    return False

def _write_report_header(f: IO[str], include_mode: bool):
    """Writes the report header."""
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
):
    """
    Writes a classic ASCII tree structure.
    If show_excluded is True, it shows all files and marks excluded ones.
    Otherwise, it only shows the files that will be processed.
    """
    f.write("### Project Structure\n\n")

    def build_tree(current_path, prefix=""):
        try:
            children = sorted(
                list(current_path.iterdir()),
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except (IOError, PermissionError):
            return

        for i, child in enumerate(children):
            is_last = i == (len(children) - 1)
            connector = "└── " if is_last else "├── "

            is_in_processed_set = child in files_to_process

            # For a directory, we need to know if it contains any processed files
            # to decide whether to draw it in the "hide excluded" mode.
            is_dir_with_processed_children = False
            if child.is_dir():
                is_dir_with_processed_children = any(
                    str(p).startswith(str(child)) for p in files_to_process
                )

            # If we're hiding excluded items, skip this item if it's not a processed file
            # and not a directory that contains processed files.
            if not show_excluded and not is_in_processed_set and not is_dir_with_processed_children:
                continue

            f.write(f"{prefix}{connector}{child.name}")

            # If the item is not in the final set, mark it and don't recurse.
            if not is_in_processed_set and not is_dir_with_processed_children:
                f.write(" [EXCLUDED]\n")
                continue
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
    """Writes the contents of the processed files."""
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

def generate_report_to_file(
    output_file: str,
    source_path_str: str,
    include_mode: bool,
    manual_selections_str: Set[str],
    global_include_patterns: List[str],
    global_exclude_patterns: List[str],
    filenames_only: bool,
    show_excluded: bool,
    cancel_event: threading.Event,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> int:
    """
    Generates a project report and writes it to a file, using a pipelined
    filtering approach. Returns the number of files processed.
    """
    source_path = Path(source_path_str)
    manual_selections = {Path(p) for p in manual_selections_str}

    if progress_callback: progress_callback(0, "Gathering files...")
    all_files = {p for p in source_path.rglob("*") if p.is_file()}
    if cancel_event.is_set(): return 0

    if progress_callback: progress_callback(5, "Applying manual selections...")
    if not manual_selections:
        initial_set = set() if include_mode else all_files
    else:
        if include_mode:
            initial_set = {p for p in all_files if any(str(p).startswith(str(ms)) for ms in manual_selections)}
        else:
            initial_set = {p for p in all_files if not any(str(p).startswith(str(ms)) for ms in manual_selections)}

    if progress_callback: progress_callback(10, "Applying global exclude patterns...")
    files_after_excludes = {p for p in initial_set if not _matches_pattern(p.relative_to(source_path), global_exclude_patterns)}

    if progress_callback: progress_callback(15, "Applying global include patterns...")
    final_files = files_after_excludes.copy()
    for p in all_files:
        if _matches_pattern(p.relative_to(source_path), global_include_patterns):
            final_files.add(p)

    files_to_process = sorted(list(final_files))
    if cancel_event.is_set(): return 0

    with open(output_file, "w", encoding="utf-8", errors="ignore") as f:
        _write_report_header(f, include_mode)
        if progress_callback: progress_callback(25, "Writing project structure...")

        _write_project_structure(f, source_path, set(files_to_process), show_excluded)

        if not filenames_only:
            _write_file_contents(f, files_to_process, source_path, cancel_event, progress_callback)

    return len(files_to_process)
