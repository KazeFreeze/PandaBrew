// Package tui implements the terminal user interface logic.
package tui

import (
	"os"
	"path/filepath"

	"pandabrew/internal/core"

	tea "github.com/charmbracelet/bubbletea"
)

// --- Messages ---

// DirLoadedMsg carries the result of a directory listing operation.
type DirLoadedMsg struct {
	Path    string
	Entries []core.DirEntry
	Err     error
}

func loadDirectoryCmd(path string) tea.Cmd {
	return func() tea.Msg {
		entries, err := core.ListDir(path)
		return DirLoadedMsg{Path: path, Entries: entries, Err: err}
	}
}

// ExportProgressMsg indicates progress during export.
type ExportProgressMsg struct {
	Processed int
	Total     int
}

// ExportCompleteMsg carries the result of an extraction operation.
type ExportCompleteMsg struct {
	Count  int
	Tokens int
	Err    error
}

func runExportCmd(space *core.DirectorySpace) tea.Cmd {
	return func() tea.Msg {
		meta, err := core.RunExtraction(space)
		return ExportCompleteMsg{
			Count:  meta.TotalFiles,
			Tokens: meta.TotalTokens,
			Err:    err,
		}
	}
}

// NewTabValidatedMsg confirms the new tab path is valid.
type NewTabValidatedMsg struct {
	Path  string
	Valid bool
	Error string
}

func validateNewTabCmd(path string) tea.Cmd {
	return func() tea.Msg {
		// Expand home directory if needed
		if len(path) > 0 && path[0] == '~' {
			home, err := os.UserHomeDir()
			if err == nil {
				path = filepath.Join(home, path[1:])
			}
		}

		// Convert to absolute path
		absPath, err := filepath.Abs(path)
		if err != nil {
			return NewTabValidatedMsg{
				Path:  path,
				Valid: false,
				Error: err.Error(),
			}
		}

		// Check if directory exists
		info, err := os.Stat(absPath)
		if err != nil {
			return NewTabValidatedMsg{
				Path:  path,
				Valid: false,
				Error: "path does not exist",
			}
		}

		// Check if it's a directory
		if !info.IsDir() {
			return NewTabValidatedMsg{
				Path:  path,
				Valid: false,
				Error: "path is not a directory",
			}
		}

		return NewTabValidatedMsg{
			Path:  absPath,
			Valid: true,
		}
	}
}
