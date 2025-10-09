import sys
import pytest
from pathlib import Path
import threading

# Add project root to sys.path to allow importing 'app'
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app import core

@pytest.fixture
def test_project(tmp_path: Path) -> Path:
    """Creates a temporary directory structure for testing."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    (project_dir / "src").mkdir()
    (project_dir / "src" / "main.py").write_text("print('hello')")
    (project_dir / "src" / "utils.py").write_text("def helper(): pass")
    (project_dir / "docs").mkdir()
    (project_dir / "docs" / "guide.md").write_text("# Guide")
    (project_dir / ".secrets").write_text("API_KEY=123")
    (project_dir / "LICENSE").write_text("MIT")
    return project_dir

def run_core_logic(
    source_path: Path,
    output_path: Path,
    include_mode: bool = True,
    manual_selections: set = None,
    manual_exclusions: set = None,
    include_patterns: list = None,
    exclude_patterns: list = None,
    filenames_only: bool = False,
    show_excluded: bool = False,
) -> str:
    """Helper function to run the core logic and return the report content."""
    manual_selections = manual_selections or set()
    manual_exclusions = manual_exclusions or set()
    include_patterns = include_patterns or []
    exclude_patterns = exclude_patterns or []

    core.generate_report_to_file(
        output_file=str(output_path),
        source_path_str=str(source_path),
        include_mode=include_mode,
        manual_selections_str=manual_selections,
        manual_exclusions_str=manual_exclusions,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
        filenames_only=filenames_only,
        show_excluded=show_excluded,
        cancel_event=threading.Event(),
    )
    return output_path.read_text()

def test_folder_inclusion(test_project: Path, tmp_path: Path):
    """Test including only files from the 'src' directory."""
    output_file = tmp_path / "output.txt"
    manual_selections = {str(test_project / "src")}

    report = run_core_logic(test_project, output_file, manual_selections=manual_selections)

    assert "main.py" in report
    assert "utils.py" in report
    assert "guide.md" not in report
    assert "LICENSE" not in report

def test_folder_exclusion(test_project: Path, tmp_path: Path):
    """Test excluding the 'docs' directory."""
    output_file = tmp_path / "output.txt"
    manual_selections = {str(test_project / "docs")}

    report = run_core_logic(test_project, output_file, include_mode=False, manual_selections=manual_selections)

    assert "main.py" in report
    assert "utils.py" in report
    assert "guide.md" not in report
    assert "LICENSE" in report

def test_filenames_only(test_project: Path, tmp_path: Path):
    """Test that file content is omitted when filenames_only is True."""
    output_file = tmp_path / "output.txt"
    report = run_core_logic(test_project, output_file, include_mode=False, filenames_only=True)

    assert "### File Contents" not in report
    assert "print('hello')" not in report

def test_show_excluded_structure(test_project: Path, tmp_path: Path):
    """Test that the structure shows excluded files when the flag is set."""
    output_file = tmp_path / "output.txt"
    exclude_patterns = ["*.md", "*.py"]
    report = run_core_logic(test_project, output_file, include_mode=False, exclude_patterns=exclude_patterns, show_excluded=True)

    assert "main.py [EXCLUDED]" in report
    assert "utils.py [EXCLUDED]" in report
    assert "guide.md [EXCLUDED]" in report
    assert "LICENSE" in report
    assert ".secrets" in report

def test_hide_excluded_structure(test_project: Path, tmp_path: Path):
    """Test that the structure does not show excluded files by default."""
    output_file = tmp_path / "output.txt"
    exclude_patterns = ["*.md", "*.py"]
    report = run_core_logic(test_project, output_file, include_mode=False, exclude_patterns=exclude_patterns, show_excluded=False)

    assert "main.py" not in report
    assert "utils.py" not in report
    assert "guide.md" not in report
    assert "LICENSE" in report
    assert ".secrets" in report

def test_filter_precedence_pipeline(test_project: Path, tmp_path: Path):
    """
    Test the full filtering pipeline: Manual -> Exclude -> Include.
    1. Manual: Include only the 'src' dir.
    2. Exclude: Exclude all '*.py' files.
    3. Include: Include back 'main.py'.
    """
    output_file = tmp_path / "output.txt"
    manual_selections = {str(test_project / "src")}
    exclude_patterns = ["*.py"]
    include_patterns = ["src/main.py"]

    report = run_core_logic(
        test_project,
        output_file,
        manual_selections=manual_selections,
        exclude_patterns=exclude_patterns,
        include_patterns=include_patterns
    )

    assert "main.py" in report
    assert "utils.py" not in report
    assert "guide.md" not in report
    assert "print('hello')" in report
    assert "def helper(): pass" not in report

def test_folder_exclusion_with_explicit_children(test_project: Path, tmp_path: Path):
    """
    Test excluding the 'docs' directory where manual selections include
    the directory and all its children, mimicking the UI behavior.
    The output should contain all files EXCEPT those in the 'docs' directory.
    """
    output_file = tmp_path / "output.txt"

    docs_dir = test_project / "docs"
    # Mimic UI behavior: select the folder and all its contents
    manual_selections = {str(docs_dir)}
    manual_selections.update({str(p) for p in docs_dir.rglob("*")})

    report = run_core_logic(
        test_project,
        output_file,
        include_mode=False,
        manual_selections=manual_selections
    )

    # Expected: everything EXCEPT the contents of 'docs' should be present.
    assert "main.py" in report
    assert "utils.py" in report
    assert "LICENSE" in report
    assert ".secrets" in report
    assert "guide.md" not in report # Ensure the excluded file is gone

    # Stricter check: ensure the file count is correct.
    # The test project has 4 files not in 'docs'.
    assert report.count("--- file:") == 4
    assert "print('hello')" in report # Check content is present
    assert "def helper(): pass" in report


def test_include_mode_with_deselected_child(tmp_path: Path):
    """
    Test a core use case for include mode: a parent directory is selected,
    but a specific child file is deselected. The deselected file should
    not be in the output.
    """
    # Use the pre-made test data directory
    source_path = Path(__file__).parent / "test_data" / "include_mode_input"
    output_file = tmp_path / "output.txt"

    dir1_path = source_path / "dir1"
    file2_path = dir1_path / "file2.txt"
    file3_path = dir1_path / "file3.txt" # This file will be deselected

    # Mimic UI behavior: user checks 'dir1', which auto-checks children.
    # Then, user unchecks 'file3.txt'.
    manual_selections = {str(dir1_path), str(file2_path)}
    manual_exclusions = {str(file3_path)}

    report = run_core_logic(
        source_path,
        output_file,
        include_mode=True,
        manual_selections=manual_selections,
        manual_exclusions=manual_exclusions
    )

    # file2.txt was explicitly selected and should be present
    assert "file: dir1/file2.txt" in report
    # file3.txt was explicitly deselected and should NOT be present
    assert "file: dir1/file3.txt" not in report


def test_exclude_mode_selection(tmp_path: Path):
    """
    Test exclude mode: The user unchecks a directory and a specific file type.
    The output should not contain them.
    """
    source_path = Path(__file__).parent / "test_data" / "exclude_mode_input"
    output_file = tmp_path / "output.txt"

    dir_path = source_path / "dir"
    log_file_path = source_path / "file1.log"

    # Mimic UI behavior: user unchecks the 'dir' directory and '*.log' files.
    # In exclude mode, manual_selections are the items to BE EXCLUDED.
    manual_selections = {str(dir_path), str(log_file_path)}

    report = run_core_logic(
        source_path,
        output_file,
        include_mode=False,
        manual_selections=manual_selections,
    )

    # The python file was not excluded and should be present
    assert "file: file2.py" in report
    assert "This is a python file" in report
    # The log file was explicitly excluded
    assert "file: file1.log" not in report
    # The text file is in an excluded directory
    assert "file: dir/file3.txt" not in report


def test_exclude_mode_with_reincluded_child(tmp_path: Path):
    """
    Test exclude mode: a parent is excluded (checked), but a child is
    re-included (unchecked). The child should appear in the output.
    """
    source_path = Path(__file__).parent / "test_data" / "include_mode_input"
    output_file = tmp_path / "output.txt"

    dir1_path = source_path / "dir1"
    file2_path = dir1_path / "file2.txt"
    file3_path = dir1_path / "file3.txt"

    # Mimic UI: User checks 'dir1' (to exclude it), then unchecks 'file2.txt'
    # to re-include it.
    # `manual_selections` are the EXCLUDED items.
    manual_selections = {str(dir1_path), str(file3_path)}
    # `manual_exclusions` are the UNCHECKED items, used here for re-inclusion.
    manual_exclusions = {str(file2_path)}


    report = run_core_logic(
        source_path,
        output_file,
        include_mode=False,
        manual_selections=manual_selections,
        manual_exclusions=manual_exclusions,
    )

    # file2.txt was re-included and should be present
    assert "file: dir1/file2.txt" in report
    assert "This is file 2" in report
    # file3.txt was part of the excluded dir and was not re-included
    assert "file: dir1/file3.txt" not in report
    # file1.txt was never excluded and should be present
    assert "file: file1.txt" in report


def test_exclude_mode_performance_with_large_dataset(tmp_path: Path):
    """
    Test performance of exclude mode with a large number of files.
    This test will hang or be very slow without the string-based optimization.
    """
    source_path = tmp_path / "large_project"
    source_path.mkdir()

    # Create a large number of files in various directories
    total_dirs = 5
    files_per_dir = 500
    for i in range(total_dirs):
        dir_path = source_path / f"dir_{i}"
        dir_path.mkdir()
        for j in range(files_per_dir):
            (dir_path / f"file_{j}.txt").write_text(f"content_{i}_{j}")

    output_file = tmp_path / "output.txt"

    # Exclude two of the directories
    dir_to_exclude1 = source_path / "dir_1"
    dir_to_exclude2 = source_path / "dir_3"
    manual_selections = {str(dir_to_exclude1), str(dir_to_exclude2)}

    report = run_core_logic(
        source_path,
        output_file,
        include_mode=False,
        manual_selections=manual_selections,
    )

    # Assert that a file from an included directory is present
    assert "file: dir_0/file_0.txt" in report
    # Assert that a file from an excluded directory is NOT present
    assert "file: dir_1/file_0.txt" not in report
    # Assert that the total number of files is correct
    # Total files = 5 * 500 = 2500. Excluded files = 2 * 500 = 1000. Expected = 1500.
    assert report.count("--- file:") == 1500


def test_include_mode_performance_with_small_selection(tmp_path: Path):
    """
    Test performance of include mode with a small selection from a large project.
    This test would be slow without the include mode optimization.
    """
    source_path = tmp_path / "large_project_include"
    source_path.mkdir()

    # Create a large number of files
    total_dirs = 10
    files_per_dir = 200
    for i in range(total_dirs):
        dir_path = source_path / f"dir_{i}"
        dir_path.mkdir()
        for j in range(files_per_dir):
            (dir_path / f"file_{j}.txt").write_text(f"content_{i}_{j}")

    output_file = tmp_path / "output.txt"

    # Select only one of the directories
    dir_to_include = source_path / "dir_4"
    manual_selections = {str(dir_to_include)}

    report = run_core_logic(
        source_path,
        output_file,
        include_mode=True,
        manual_selections=manual_selections,
    )

    # Assert that a file from the included directory is present
    assert "file: dir_4/file_0.txt" in report
    # Assert that a file from a non-included directory is NOT present
    assert "file: dir_0/file_0.txt" not in report
    # Assert that the total number of files is correct (should only be files_per_dir)
    assert report.count("--- file:") == files_per_dir
