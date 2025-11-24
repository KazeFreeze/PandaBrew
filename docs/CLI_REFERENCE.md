# PandaBrew CLI Reference

This document provides a complete reference for all PandaBrew commands and options.

## Quick Start

```bash
# Interactive TUI mode
pandabrew --root ./my-project

# Headless mode
pandabrew --headless --root ./my-project --output context.txt
```

## Global Options

These options are available for all commands:

- `--root <path>` - Set the project root directory (default: current directory)
- `--output <path>` - Set the output file path (default: project_extraction.txt)
- `--headless` - Run in headless mode without TUI
- `--help` - Display help information
- `--version` - Display version information

## Interactive TUI Mode

The default mode provides a full-featured terminal UI with:

- Multi-workspace/tab support
- Recursive file selection
- Real-time filtering
- Session persistence

### Keyboard Shortcuts

#### Navigation
- `↑/↓` or `k/j` - Move cursor up/down
- `PgUp/PgDn` - Page up/down
- `Home/End` - Jump to top/bottom
- `→/←` or `l/h` - Expand/collapse directories

#### Selection
- `Space` - Toggle selection (recursive for directories)
- `a` - Select all visible items
- `A` - Deselect all items
- `Enter` - Toggle directory expansion

#### Actions
- `e` - Export selected files
- `/` - Start filtering
- `Esc` - Clear filter/exit input mode
- `?` - Show help

#### Workspace Management
- `Tab` - Next workspace
- `Shift+Tab` - Previous workspace
- `Ctrl+n` - New workspace
- `Ctrl+w` - Close current workspace

#### Application
- `Ctrl+c` or `q` - Quit application

## Headless Mode

For CI/CD and automation workflows:

```bash
pandabrew --headless \
  --root ./my-project \
  --output llm-context.txt
```

### Use Cases

**CI/CD Integration:**
```bash
# In GitHub Actions
- name: Generate codebase context
  run: pandabrew --headless --root . --output context.txt
```

**Pre-commit Hook:**
```bash
#!/bin/bash
pandabrew --headless --root . --output docs/codebase.txt
git add docs/codebase.txt
```

**Documentation Generation:**
```bash
# Generate context for different modules
pandabrew --headless --root ./backend --output backend-context.txt
pandabrew --headless --root ./frontend --output frontend-context.txt
```

## Configuration

PandaBrew stores session data in `pandabrew_session.json` in the current directory.

### Session Data

The session file contains:
- Open workspace tabs
- File selections per workspace
- Filter configurations
- Output file paths
- Window state

### Session File Format

```json
{
  "workspaces": [
    {
      "root": "/path/to/project",
      "output": "project_extraction.txt",
      "selections": {
        "path/to/file.go": true
      }
    }
  ],
  "active_workspace": 0
}
```

## Exit Codes

- `0` - Success
- `1` - General error (invalid arguments, file access errors, etc.)
- `2` - Invalid command-line arguments

## Output Format

The generated output file contains:

```
--- Project Extraction Report ---
Timestamp: 2024-01-15T10:30:00Z
Selection Mode: INCLUDE checked items
---

### Project Structure

project/
├── src/
│   ├── main.go
│   └── utils.go
└── README.md

### File Contents

--- file: src/main.go ---
package main
...

--- file: src/utils.go ---
package utils
...
```

## Examples

### Extract Go Project
```bash
pandabrew --root ~/projects/myapp --output go-context.txt
```

### Multiple Projects in Tabs
```bash
# Start with first project
pandabrew --root ~/project1

# In TUI:
# 1. Press Ctrl+n to open new workspace
# 2. Navigate to different directory
# 3. Select files and export
```

### Automated Documentation
```bash
#!/bin/bash
# Generate context for LLM analysis
pandabrew --headless \
  --root . \
  --output docs/codebase-snapshot-$(date +%Y%m%d).txt

echo "Context generated for $(git rev-parse --short HEAD)"
```

## Troubleshooting

### Permission Denied
```bash
# Ensure write permissions
chmod +w project_extraction.txt
```

### Session File Corrupted
```bash
# Remove and restart
rm pandabrew_session.json
pandabrew
```

### Large Projects Performance
For very large projects (10,000+ files):
- Use filtering to narrow scope
- Consider processing subdirectories separately
- Use headless mode for automated tasks

## Tips and Best Practices

1. **Use filters** - Press `/` to filter by name patterns
2. **Keyboard-first** - Learn shortcuts for faster navigation
3. **Save sessions** - Session data persists between runs
4. **Multiple workspaces** - Work on related projects simultaneously
5. **Headless for CI** - Integrate into build pipelines
6. **Version control output** - Track changes to extracted context

## Integration Examples

### With Claude/ChatGPT
```bash
# Generate context
pandabrew --headless --root . --output context.txt

# Then upload context.txt to Claude/ChatGPT for:
# - Code review
# - Architecture analysis
# - Documentation generation
# - Bug investigation
```

### With Git Hooks
```bash
# .git/hooks/pre-commit
#!/bin/bash
pandabrew --headless --root . --output .context-snapshot.txt
```

### In Makefiles
```makefile
.PHONY: context
context:
	pandabrew --headless --root . --output docs/codebase.txt
	@echo "Codebase context updated"
```
