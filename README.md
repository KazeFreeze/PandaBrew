# <div align="center"><img src="pandabrew.png" alt="PandaBrew Logo" width="150"/></div>

# <h1 align="center">PandaBrew Code Extractor</h1>

<div align="center">

A modern, cross-platform GUI utility and CLI for selectively extracting and packaging project source code into a single, comprehensive text file. Perfect for creating project snapshots for LLMs, documentation, or code reviews.

[![Release Version](https://img.shields.io/github/v/release/KazeFreeze/PandaBrew?style=for-the-badge&logo=github)](https://github.com/KazeFreeze/PandaBrew/releases)
[![Build Status](https://img.shields.io/github/actions/workflow/status/KazeFreeze/PandaBrew/build-and-release.yml?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/KazeFreeze/PandaBrew/actions/workflows/build-and-release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

</div>

---

PandaBrew is a desktop application and command-line tool built with Python that provides an intuitive way to browse a project directory, select files and folders, and consolidate their structure and content into a single output file. It's designed to be fast, user-friendly, and powerful.

## ✨ Key Features

- **Cross-Platform**: Natively supports **Windows** and **Fedora Linux**.
- **Modern Tabbed GUI**: Manage multiple project extractions in separate tabs, each with its own configuration.
- **Flexible File Selection**: A classic-style file tree allows you to check files and folders for processing.
- **Include/Exclude Modes**: Choose to either package _only_ the checked items or package _everything except_ the checked items.
- **Advanced `.gitignore`-style Filtering**: Use global include/exclude patterns to finely control which files are processed across all projects.
- **Command-Line Interface**: A separate CLI for automation and scripting workflows.
- **Persistent Sessions**: The app remembers your open tabs, file selections, and window settings between sessions.
- **Responsive UI**: File processing is handled in a separate thread, so the UI never freezes.
- **Real-time Progress**: A progress bar and status label keep you updated on the extraction process.

## 📸 Screenshots

_(UI)_
![PandaBrew Application Screenshot](demo.png)

## 🚀 Getting Started

You can either download the latest executable for your operating system from the [Releases page](https://github.com/KazeFreeze/PandaBrew/releases) or run it from the source.

### Prerequisites

- [Python 3.9+](https://www.python.org/downloads/)
- `pip` (Python package installer)
- For Fedora/Linux: `sudo dnf install -y python3-tkinter`

### Installation from Source

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/KazeFreeze/PandaBrew.git
    cd PandaBrew
    ```
2.  **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```

## 🖥️ GUI Usage

1.  **Run the application:**
    - On Windows: `python main.py`
    - On Linux: `python3 main.py`
2.  **Select Source**: In a tab, click `Browse` to choose the root directory of the project.
3.  **Select Files**: Use the checkboxes in the tree view to manually select files and folders.
4.  **Choose Mode**:
    - `Include checked`: Only the items you've checked will be in the output.
    - `Exclude checked`: All items will be in the output _except_ for the ones you've checked.
5.  **Configure Global Filters (Optional)**: Use the text boxes at the bottom to enter global `.gitignore`-style patterns. These apply to all tabs and override manual selections.
6.  **Set Output File**: Click `Save As` to specify where the final `.txt` report will be saved.
7.  **Extract**: Click the `Extract Code` button to begin the process.

## 🤖 Command-Line Usage

PandaBrew can also be run as a command-line tool, perfect for scripting and automation.

```sh
python cli.py [SOURCE_DIRECTORY] [OUTPUT_FILE] [OPTIONS]
```

### Arguments

-   `source`: The source directory to process.
-   `output`: The path to the output text file.

### Options

-   `--include-file FILE`: Path to a file containing newline-separated `.gitignore`-style patterns to include. These patterns have the highest precedence and can "un-ignore" files.
-   `--exclude-file FILE`: Path to a file containing newline-separated `.gitignore`-style patterns to exclude.
-   `--filenames-only`: If set, only the project structure and filenames will be extracted, not their content.

### Example

Create an `include.txt` file:
```
# Include all python and markdown files
*.py
*.md
```

Create an `exclude.txt` file:
```
# Exclude virtual environments and dotfiles
.venv/
.git/
__pycache__/
```

Run the CLI:
```sh
python cli.py ./my_project ./output.txt --include-file include.txt --exclude-file exclude.txt
```

## 🛠️ Building from Source

This project uses `PyInstaller` to create single-file executables. An automated build process is configured in `.github/workflows/build-and-release.yml`.

To build the executable manually, first install PyInstaller (`pip install pyinstaller`), then run the appropriate build command.

- **For Windows:**
  ```sh
  pyinstaller --name "PandaBrew" --onefile --windowed --icon "pandabrew.ico" main.py
  ```
- **For Linux (from the project root):**
  ```sh
  pyinstaller --name "PandaBrew" --onefile --windowed --icon "pandabrew.ico" --hidden-import=PIL._tkinter_finder main.py
  ```

The final executable will be located in the `dist` folder.

## 🤝 Contributing

Contributions are greatly appreciated. Please fork the project and submit a pull request.

## 📄 License

Distributed under the MIT License.

## 🙏 Acknowledgements

- [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap)
- [pywinstyles](https://github.com/CvlKul/pywinstyles)
