# Code Extractor

A simple, powerful GUI tool for extracting and organizing code from project directories.

## Overview

Code Extractor is a desktop application that allows you to easily extract all or selected files from your project directory into a single, organized text file. This is particularly useful for:

- Sharing code samples without sending multiple files
- Creating documentation of your project structure
- Making code backups in a human-readable format
- Preparing code submissions for review

## Features

- **Intuitive File Browser**: Navigate your project structure with an expandable tree view
- **Selective Extraction**: Include or exclude specific files and directories
- **Two Extraction Modes**:
  - Include Mode: Only extracts checked items
  - Exclude Mode: Extracts everything except checked items
- **Recent Folders**: Remembers your recently used source and output locations
- **Progress Tracking**: Visual progress bar and status updates during extraction
- **Clean Output Format**: Creates a well-structured output file with:
  - Project structure overview
  - File contents with clear separators
  - Minimal header information for maximum readability

## Installation

### Prerequisites

- Python 3.6 or higher
- Tkinter (usually included with Python)

### Option 1: Run from Source

1. Clone this repository:
   ```
   git clone https://github.com/KazeFreeze/project-extractor.git
   cd code-extractor
   ```
2. Run the application:
   ```
   python code_extractor.py
   ```

### Option 2: Create Executable (Windows)

1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```
2. Create executable:
   ```
   pyinstaller --onefile --windowed code_extractor.py
   ```
3. Find the executable in the `dist` folder

## Usage Guide

### Basic Usage

1. **Select Source Directory**: Click "Browse" to select the project folder you want to extract code from
2. **Select Output File**: Choose where to save the extracted code
3. **Configure Extraction**:
   - Navigate the file tree and check boxes next to files/folders you want to include/exclude
   - Select either "Include checked items" or "Exclude checked items" mode
4. **Extract**
