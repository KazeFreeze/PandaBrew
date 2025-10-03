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
    include_patterns: list = None,
    exclude_patterns: list = None,
    filenames_only: bool = False,
    show_excluded: bool = False,
) -> str:
    """Helper function to run the core logic and return the report content."""
    manual_selections = manual_selections or set()
    include_patterns = include_patterns or []
    exclude_patterns = exclude_patterns or []

    core.generate_report_to_file(
        output_file=str(output_path),
        source_path_str=str(source_path),
        include_mode=include_mode,
        manual_selections_str=manual_selections,
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
