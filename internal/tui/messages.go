package tui

import (
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
