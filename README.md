# <div align="center"><img src="pandabrew.png" alt="PandaBrew Logo" width="150"/></div>

# <h1 align="center">PandaBrew Code Extractor</h1>

<div align="center">

A modern GUI utility for selectively extracting and packaging project source code into a single, comprehensive text file. Perfect for creating project snapshots for LLMs, documentation, or code reviews.

[![Release Version](https://img.shields.io/github/v/release/KazeFreeze/PandaBrew?style=for-the-badge&logo=github)](https://github.com/KazeFreeze/PandaBrew/releases)
[![Build Status](https://img.shields.io/github/actions/workflow/status/KazeFreeze/PandaBrew/build-and-release.yml?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/KazeFreeze/PandaBrew/actions/workflows/build-and-release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

</div>

---

PandaBrew is a desktop application built with Python and `ttkbootstrap` that provides an intuitive interface for browsing a project directory, selecting specific files and folders, and consolidating their structure and content into a single output file. It's designed to be fast, user-friendly, and visually appealing, with a modern dark theme and a tabbed interface to manage multiple projects at once.

## ✨ Key Features

- **Modern Tabbed GUI**: Manage multiple project extractions in separate tabs, each with its own configuration.
- **Flexible File Selection**: A classic-style file tree allows you to check files and folders for processing.
- **Include/Exclude Modes**: Choose to either package _only_ the checked items or package _everything except_ the checked items.
- **Persistent Sessions**: The app remembers your open tabs, file selections, and window settings between sessions.
- **Responsive UI**: File processing is handled in a separate thread, so the UI never freezes, even with large projects.
- **Real-time Progress**: A progress bar and status label keep you updated on the extraction process.
- **Content Control**: Option to extract only the project structure and filenames without the file contents.
- **Automated Builds**: Includes a GitHub Actions workflow to automatically build and release a Windows executable when you push a new version tag.

## 📸 Screenshots

_(UI)_
![PandaBrew Application Screenshot](demo.png)

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- [Python 3.9+](https://www.python.org/downloads/)
- `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/KazeFreeze/PandaBrew.git](https://github.com/KazeFreeze/PandaBrew.git)
    cd YOUR_REPOSITORY
    ```
2.  **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```

## 🖥️ Usage

1.  **Run the application:**
    ```sh
    python main.py
    ```
2.  **Select Source**: In a tab, click `Browse` to choose the root directory of the project you want to extract.
3.  **Select Files**: Use the checkboxes in the tree view to select the files and folders you want to process.
4.  **Choose Mode**:
    - `Include checked`: Only the items you've checked will be in the output.
    - `Exclude checked`: All items will be in the output _except_ for the ones you've checked.
5.  **Set Output File**: Click `Save As` to specify where the final `.txt` report will be saved.
6.  **Extract**: Click the `Extract Code` button to begin the process. You can cancel at any time.

## 🛠️ Building from Source

This project uses `PyInstaller` to create a single executable file for Windows. An automated build process is already configured in `.github/workflows/build-and-release.yml`.

To build the executable manually:

1.  **Install PyInstaller:**
    ```sh
    pip install pyinstaller
    ```
2.  **Run the build command:**
    (This command is adapted from the project's build workflow file)
    ```sh
    pyinstaller --name "PandaBrew" --onefile --windowed --icon "pandabrew.ico" main.py
    ```
3.  The final executable will be located in the `dist` folder.

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🙏 Acknowledgements

- [ttkbootstrap](https://github.com/israel-dryer/ttkbootstrap) - For making modern Tkinter styling so accessible.
- [pywinstyles](https://github.com/CvlKul/pywinstyles) - For the beautiful mica window effect on Windows.
