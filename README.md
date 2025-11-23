# PandaBrew 🐼

A high-performance, headless-first tool to extract codebases into a single text file for LLM context. Written in Go.

---

## Installation

**Initialize:**

```sh
go mod tidy
```

**Build:**

```sh
go build -o bin/pandabrew cmd/pandabrew/main.go
```

**Run:**

```sh
./bin/pandabrew
```

---

## Usage

### Interactive TUI (Recommended)

```sh
./bin/pandabrew --root ./my-project
```

Running inside a directory (`.`) creates a Directory Space for that folder.

### Headless Mode

```sh
./bin/pandabrew --headless --root ./my-project --output context.txt
```

---

## TUI Guide

PandaBrew uses a **Workspace/Tab** model. You can keep multiple projects open as
tabs. Each tab is a **Directory Space** with its own isolated configuration.

---

## Conceptual Model

- **Directory Space (Tab):**  
  Represents one project root. Stores your selections (`src/`), filters (`*.py`), and output file (`project.txt`).

- **Session:**  
  Global state that stores all open tabs and settings automatically.

- **Recursive Selection:**  
  Selecting a folder implicitly includes all children unless manually unchecked.

---

## Keyboard Shortcuts

### Navigation

| Key           | Action                         |
| :------------ | :----------------------------- |
| ↑ / k         | Move cursor up                 |
| ↓ / j         | Move cursor down               |
| Tab           | Switch Directory Spaces (Tabs) |
| Enter / → / l | Expand directory               |
| ← / h         | Collapse directory             |

### Selection & Actions

| Key        | Action                       |
| :--------- | :--------------------------- |
| Space      | Toggle file/folder selection |
| Ctrl+E     | Export report                |
| Ctrl+S     | Save session manually        |
| q / Ctrl+C | Quit                         |

### Settings (Sidebar)

| Key | Action                                      |
| :-- | :------------------------------------------ |
| r   | Edit Root Path                              |
| o   | Edit Output Path                            |
| i   | Toggle Include Mode (Whitelist / Blacklist) |
| c   | Toggle Show Context                         |
| x   | Toggle Show Excluded                        |
