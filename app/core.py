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
            children = sorted(
                list(current_path.iterdir()),
                key=lambda p: (p.is_file(), p.name.lower()),
            )
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
    if progress_callback: progress_callback(10, "Applying exclude patterns...")
    files_after_excludes = {p for p in initial_set if not _matches_pattern(p.relative_to(source_path), exclude_patterns)}
    if progress_callback: progress_callback(15, "Applying include patterns...")
    final_files = files_after_excludes.copy()
    for p in all_files:
        if _matches_pattern(p.relative_to(source_path), include_patterns):
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
