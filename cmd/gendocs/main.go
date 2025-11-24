package main

import (
	"fmt"
	"log"
	"os"

	"github.com/spf13/cobra"
	"github.com/spf13/cobra/doc"
	// Import your root command - adjust this path to match your project structure
	// "github.com/KazeFreeze/PandaBrew/cmd/pandabrew"
)

func main() {
	// Create the root command - replace this with your actual root command
	// For now, creating a placeholder structure
	rootCmd := createRootCommand()

	// Ensure directories exist
	if err := ensureDir("./docs"); err != nil {
		log.Fatalf("Failed to create docs directory: %v", err)
	}
	if err := ensureDir("./manpages"); err != nil {
		log.Fatalf("Failed to create manpages directory: %v", err)
	}

	// Generate Markdown documentation
	fmt.Println("Generating Markdown documentation...")
	if err := doc.GenMarkdownTree(rootCmd, "./docs"); err != nil {
		log.Fatalf("Failed to generate Markdown docs: %v", err)
	}
	fmt.Println("✓ Markdown docs generated in ./docs/")

	// Generate Man pages
	fmt.Println("Generating man pages...")
	header := &doc.GenManHeader{
		Title:   "PANDABREW",
		Section: "1",
		Source:  "PandaBrew",
		Manual:  "PandaBrew Manual",
	}
	if err := doc.GenManTree(rootCmd, header, "./manpages"); err != nil {
		log.Fatalf("Failed to generate man pages: %v", err)
	}
	fmt.Println("✓ Man pages generated in ./manpages/")

	// Generate additional documentation files
	if err := generateAdditionalDocs(); err != nil {
		log.Fatalf("Failed to generate additional docs: %v", err)
	}
	fmt.Println("✓ Additional documentation generated")

	fmt.Println("\nDocumentation generation complete!")
}

// createRootCommand creates your application's root command
// Replace this with your actual root command import
func createRootCommand() *cobra.Command {
	rootCmd := &cobra.Command{
		Use:   "pandabrew",
		Short: "A TUI tool for selective file extraction and project documentation",
		Long: `PandaBrew 🐼☕

A high-performance, headless-first tool to extract codebases into a single
text file for LLM context. Features an interactive TUI with workspace
management and smart file filtering.`,
		Version: "1.0.0",
	}

	// Add your subcommands here if you have any
	// rootCmd.AddCommand(versionCmd, extractCmd, etc.)

	return rootCmd
}

// generateAdditionalDocs creates supplementary documentation
func generateAdditionalDocs() error {
	// Generate CLI reference
	cliRef := `# PandaBrew CLI Reference

This document provides a complete reference for all PandaBrew commands and options.

## Quick Start

` + "```bash" + `
# Interactive TUI mode
pandabrew --root ./my-project

# Headless mode
pandabrew --headless --root ./my-project --output context.txt
` + "```" + `

## Global Options

These options are available for all commands:

- ` + "`--root <path>`" + ` - Set the project root directory (default: current directory)
- ` + "`--output <path>`" + ` - Set the output file path (default: project_extraction.txt)
- ` + "`--headless`" + ` - Run in headless mode without TUI
- ` + "`--help`" + ` - Display help information
- ` + "`--version`" + ` - Display version information

## Interactive TUI Mode

The default mode provides a full-featured terminal UI with:

- Multi-workspace/tab support
- Recursive file selection
- Real-time filtering
- Session persistence

### Keyboard Shortcuts

See the main README.md for complete keyboard shortcut reference.

## Headless Mode

For CI/CD and automation workflows:

` + "```bash" + `
pandabrew --headless \
  --root ./my-project \
  --output llm-context.txt \
  --include "*.go,*.md" \
  --exclude "vendor/,*_test.go"
` + "```" + `

## Configuration

PandaBrew stores session data in ` + "`pandabrew_session.json`" + ` in the current directory.

Session data includes:
- Open workspace tabs
- File selections
- Filter configurations
- Output paths

## Exit Codes

- ` + "`0`" + ` - Success
- ` + "`1`" + ` - General error
- ` + "`2`" + ` - Invalid arguments

## Examples

### Extract Go Project
` + "```bash" + `
pandabrew --root ~/projects/myapp --output go-context.txt
` + "```" + `

### Headless with Filters
` + "```bash" + `
pandabrew --headless \
  --root . \
  --output docs.txt \
  --include "*.md,*.txt"
` + "```" + `

### Multiple Projects
` + "```bash" + `
# Open multiple projects in tabs
pandabrew --root ~/project1
# Then use Tab key to open additional workspaces
` + "```" + `
`

	if err := os.WriteFile("./docs/CLI_REFERENCE.md", []byte(cliRef), 0o644); err != nil {
		return fmt.Errorf("failed to write CLI reference: %w", err)
	}

	// Generate INSTALLATION.md
	installDoc := `# Installation Guide

## Package Managers

### Homebrew (macOS/Linux)

` + "```bash" + `
brew install kazefreeze/tap/pandabrew
` + "```" + `

### AUR (Arch Linux)

` + "```bash" + `
yay -S pandabrew
# or
paru -S pandabrew
` + "```" + `

## Pre-built Binaries

Download the latest release for your platform from:
https://github.com/KazeFreeze/PandaBrew/releases/latest

### Linux

` + "```bash" + `
# Download and extract
curl -L https://github.com/KazeFreeze/PandaBrew/releases/latest/download/PandaBrew_<version>_Linux_x86_64.tar.gz | tar xz

# Install globally
sudo mv pandabrew /usr/local/bin/
sudo chmod +x /usr/local/bin/pandabrew

# Verify installation
pandabrew --version
` + "```" + `

### macOS

` + "```bash" + `
# Download and extract
curl -L https://github.com/KazeFreeze/PandaBrew/releases/latest/download/PandaBrew_<version>_Darwin_x86_64.tar.gz | tar xz

# Install globally
sudo mv pandabrew /usr/local/bin/
sudo chmod +x /usr/local/bin/pandabrew

# Verify installation
pandabrew --version
` + "```" + `

### Windows

1. Download the ZIP file for Windows from the releases page
2. Extract to a directory (e.g., ` + "`C:\\Program Files\\PandaBrew`" + `)
3. Add the directory to your PATH environment variable
4. Open a new terminal and verify: ` + "`pandabrew --version`" + `

## Build from Source

### Requirements

- Go 1.23 or later
- Git

### Steps

` + "```bash" + `
# Clone the repository
git clone https://github.com/KazeFreeze/PandaBrew.git
cd PandaBrew

# Install dependencies
go mod tidy

# Build
go build -o pandabrew ./cmd/pandabrew

# Install globally (optional)
sudo mv pandabrew /usr/local/bin/
` + "```" + `

## Verify Installation

` + "```bash" + `
pandabrew --version
pandabrew --help
` + "```" + `

## Troubleshooting

### Permission Denied (Linux/macOS)

` + "```bash" + `
sudo chmod +x /usr/local/bin/pandabrew
` + "```" + `

### Command Not Found (Windows)

Make sure the PandaBrew directory is in your PATH environment variable.

### Man Pages Not Showing

` + "```bash" + `
# Linux/macOS - ensure man pages are installed
man pandabrew
` + "```" + `

If man pages don't work, reinstall using a package manager or check that
` + "`/usr/share/man/man1/`" + ` contains ` + "`pandabrew.1.gz`" + `.
`

	if err := os.WriteFile("./docs/INSTALLATION.md", []byte(installDoc), 0o644); err != nil {
		return fmt.Errorf("failed to write installation guide: %w", err)
	}

	return nil
}

// ensureDir creates a directory if it doesn't exist
func ensureDir(path string) error {
	return os.MkdirAll(path, 0o755)
}
