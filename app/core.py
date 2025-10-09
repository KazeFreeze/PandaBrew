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
            is_processed = child in files_to_process
            is_parent_of_processed = False
            if child.is_dir():
                is_parent_of_processed = any(p.is_relative_to(child) for p in files_to_process)

            if not show_excluded and not is_processed and not is_parent_of_processed:
                continue

            f.write(f"{prefix}{connector}{child.name}")

            if child.is_file() and not is_processed:
                f.write(" [EXCLUDED]\n")
            else:
                f.write("\n")

            if child.is_dir():
                if show_excluded or is_parent_of_processed:
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

    files_to_process = set()

    all_paths = list(source_path.rglob("*"))
    total_paths = len(all_paths)

    for i, path in enumerate(all_paths):
        if cancel_event.is_set(): return 0
        if not path.is_file(): continue

        if progress_callback and i % 50 == 0:
            progress = (i / total_paths) * 20 if total_paths > 0 else 0
            progress_callback(progress, f"Filtering... ({i}/{total_paths})")

        is_manually_in: bool
        if not manual_selections:
            is_manually_in = not include_mode
        else:
            if include_mode:
                is_manually_in = any(str(path).startswith(str(ms)) for ms in manual_selections)
            else:
                is_manually_in = not any(str(path).startswith(str(ms)) for ms in manual_selections)

        relative_path = path.relative_to(source_path)
        is_excluded = _matches_pattern(relative_path, exclude_patterns)
        is_included = _matches_pattern(relative_path, include_patterns)

        if is_included:
            files_to_process.add(path)
        elif is_manually_in and not is_excluded:
            files_to_process.add(path)

    files_to_process_sorted = sorted(list(files_to_process))
    if cancel_event.is_set(): return 0

    with open(output_file, "w", encoding="utf-8", errors="ignore") as f:
        _write_report_header(f, include_mode)
        if progress_callback: progress_callback(25, "Writing project structure...")

        _write_project_structure(f, source_path, files_to_process, show_excluded)

        if not filenames_only:
            _write_file_contents(f, files_to_process_sorted, source_path, cancel_event, progress_callback)
    return len(files_to_process_sorted)
