import datetime
import fnmatch
from pathlib import Path
from typing import List, Set, Optional, Callable, IO
import threading

def _matches_pattern(path: Path, patterns: List[str]) -> bool:
    """Checks if a path or its name matches any of the given glob patterns."""
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
    all_files_in_scope: Set[Path],
    show_excluded: bool,
):
    f.write("### Project Structure\n\n")

    # If not showing excluded, the tree should only contain files to process and their parents.
    tree_items = all_files_in_scope if show_excluded else files_to_process

    # We need all parent directories to build the tree structure correctly.
    required_dirs = set()
    for item in tree_items:
        parent = item.parent
        while parent.is_relative_to(source_path) and parent != source_path:
            required_dirs.add(parent)
            parent = parent.parent

    tree_nodes = tree_items.union(required_dirs)

    def build_tree(current_path, prefix=""):
        try:
            children = sorted(
                [p for p in current_path.iterdir() if p in tree_nodes or p.is_dir() and any(n.is_relative_to(p) for n in tree_nodes)],
                key=lambda p: (p.is_file(), p.name.lower())
            )
        except (IOError, PermissionError):
            return

        for i, child in enumerate(children):
            is_last = i == (len(children) - 1)
            connector = "└── " if is_last else "├── "

            f.write(f"{prefix}{connector}{child.name}")

            if child.is_file():
                if child not in files_to_process:
                    f.write(" [EXCLUDED]")
                f.write("\n")
            else: # is_dir()
                f.write("\n")
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
    manual_exclusions_str: Set[str],
    include_patterns: List[str],
    exclude_patterns: List[str],
    filenames_only: bool,
    show_excluded: bool,
    cancel_event: threading.Event,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> int:
    source_path = Path(source_path_str)
    manual_selections = {Path(p) for p in manual_selections_str}
    manual_exclusions = {Path(p) for p in manual_exclusions_str}
    if progress_callback: progress_callback(0, "Gathering and filtering files...")

    all_files = {p for p in source_path.rglob("*") if p.is_file()}

    # 1. Determine the initial set of files based on manual selections
    if progress_callback: progress_callback(5, "Applying manual selections...")
    initial_set = set()
    if include_mode:
        if manual_selections:
            for path in all_files:
                if any(path == ms or path.is_relative_to(ms) for ms in manual_selections):
                    initial_set.add(path)
        # Now, remove any files that were explicitly deselected.
        initial_set.difference_update(manual_exclusions)
    else:  # Exclude mode
        initial_set = all_files.copy()

        # In exclude mode, `manual_selections` are the items to EXCLUDE.
        # `manual_exclusions` are items that were UNCHECKED, so they need to be RE-INCLUDED.

        if manual_selections:
            # Optimization: Prune the exclusion list. If '/a' is excluded,
            # there's no need to also check against '/a/b'.
            sorted_selections = sorted(list(manual_selections), key=lambda p: len(p.parts))
            exclusion_roots = set()
            for path in sorted_selections:
                if not any(path.is_relative_to(p) for p in exclusion_roots):
                    exclusion_roots.add(path)

            if exclusion_roots:
                # Convert Path objects to strings for much faster startswith checks.
                import os
                dir_roots = {str(p) + os.path.sep for p in exclusion_roots if p.is_dir()}
                file_roots = {str(p) for p in exclusion_roots if p.is_file()}

                to_remove = set()
                for path in initial_set:
                    path_str = str(path)
                    if path_str in file_roots or any(path_str.startswith(dr) for dr in dir_roots):
                        to_remove.add(path)
                initial_set.difference_update(to_remove)

        # Re-include any files that were explicitly unchecked by the user.
        initial_set.update(manual_exclusions)

    files_in_scope = initial_set.copy() # For the tree view

    # 2. Apply exclude patterns
    if progress_callback: progress_callback(10, "Applying exclude patterns...")
    if exclude_patterns:
        files_in_scope = {
            p for p in files_in_scope
            if not _matches_pattern(p.relative_to(source_path), exclude_patterns)
        }

    # 3. Apply include patterns (can add files back)
    if progress_callback: progress_callback(15, "Applying include patterns...")
    if include_patterns:
        for path in all_files:
            if _matches_pattern(path.relative_to(source_path), include_patterns):
                files_in_scope.add(path)

    files_to_process = files_in_scope
    files_to_process_sorted = sorted(list(files_to_process))
    if cancel_event.is_set(): return 0

    with open(output_file, "w", encoding="utf-8", errors="ignore") as f:
        _write_report_header(f, include_mode)
        if progress_callback: progress_callback(20, "Writing project structure...")

        _write_project_structure(f, source_path, files_to_process, all_files, show_excluded)

        if not filenames_only:
            _write_file_contents(f, files_to_process_sorted, source_path, cancel_event, progress_callback)

    if progress_callback: progress_callback(100, "Report generated.")
    return len(files_to_process_sorted)