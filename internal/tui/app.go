// Package tui implements the terminal user interface using Bubble Tea.
package tui

import (
	"fmt"
	"maps"
	"sort"

	// Requires Go 1.21+
	"pandabrew/internal/core"

	"github.com/charmbracelet/bubbles/spinner"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// AppModel is the single source of truth for the UI state.
type AppModel struct {
	RootPath         string
	ManualSelections map[string]bool
	IncludeMode      bool

	TreeRoot      *TreeNode
	CursorNode    *TreeNode
	Loading       bool
	StatusMessage string

	Spinner spinner.Model
}

type TreeNode struct {
	Name     string
	FullPath string
	IsDir    bool
	Expanded bool
	Children []*TreeNode
	Parent   *TreeNode
}

func InitialModel(rootPath string) AppModel {
	s := spinner.New()
	s.Spinner = spinner.Dot
	s.Style = lipgloss.NewStyle().Foreground(lipgloss.Color("205"))

	rootNode := &TreeNode{
		Name:     rootPath,
		FullPath: rootPath,
		IsDir:    true,
		Expanded: true,
	}

	return AppModel{
		RootPath:         rootPath,
		ManualSelections: make(map[string]bool),
		IncludeMode:      true,
		Spinner:          s,
		TreeRoot:         rootNode,
		CursorNode:       rootNode,
		Loading:          true,
	}
}

func (m AppModel) Init() tea.Cmd {
	return tea.Batch(m.Spinner.Tick, loadDirectoryCmd(m.RootPath))
}

func (m AppModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd

	switch msg := msg.(type) {

	// --- Async Results ---
	case DirLoadedMsg:
		m.Loading = false
		if msg.Err != nil {
			m.StatusMessage = "Error: " + msg.Err.Error()
		} else {
			m.populateChildren(msg.Path, msg.Entries)
		}

	case ExportCompleteMsg:
		m.Loading = false
		if msg.Err != nil {
			m.StatusMessage = "Export Failed: " + msg.Err.Error()
		} else {
			m.StatusMessage = fmt.Sprintf("Success! Processed %d files.", msg.Count)
		}

	// --- User Input ---
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit
		}

		if m.Loading {
			return m, nil // Block input while processing
		}

		switch msg.String() {
		case " ": // Toggle Selection
			if m.CursorNode != nil {
				path := m.CursorNode.FullPath
				if m.ManualSelections[path] {
					delete(m.ManualSelections, path)
				} else {
					m.ManualSelections[path] = true
				}
			}

		case "enter", "right": // Expand
			if m.CursorNode != nil && m.CursorNode.IsDir {
				if !m.CursorNode.Expanded {
					m.CursorNode.Expanded = true
					// Lazy Load Check
					if len(m.CursorNode.Children) == 0 {
						m.Loading = true
						m.StatusMessage = "Scanning..."
						return m, tea.Batch(m.Spinner.Tick, loadDirectoryCmd(m.CursorNode.FullPath))
					}
				} else if msg.String() == "enter" {
					m.CursorNode.Expanded = false
				}
			}

		case "up", "k":
			// Simple traversal placeholder

		case "down", "j":
			// Placeholder

		case "e": // Export
			m.Loading = true
			m.StatusMessage = "Exporting..."

			// Efficient map copy (Go 1.21+)
			selectionsCopy := make(map[string]bool, len(m.ManualSelections))
			maps.Copy(selectionsCopy, m.ManualSelections)

			return m, tea.Batch(m.Spinner.Tick, runExportCmd(m.RootPath, selectionsCopy, m.IncludeMode))
		}
	}

	if m.Loading {
		m.Spinner, cmd = m.Spinner.Update(msg)
	}

	return m, cmd
}

func (m AppModel) View() string {
	header := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("#FAFAFA")).Background(lipgloss.Color("#7D56F4")).Padding(0, 1).Render("PandaBrew TUI")

	status := m.StatusMessage
	if m.Loading {
		status = fmt.Sprintf("%s %s", m.Spinner.View(), m.StatusMessage)
	}

	treeView := fmt.Sprintf("Current Root: %s\n\n[Press E to Export]\n[Press Space to Select]\n[Use Enter to Expand]", m.RootPath)

	return fmt.Sprintf("%s\n\n%s\n\n%s", header, treeView, status)
}

func (m *AppModel) populateChildren(parentPath string, entries []core.DirEntry) {
	targetNode := m.CursorNode
	if targetNode.FullPath != parentPath {
		return
	}

	var children []*TreeNode
	for _, e := range entries {
		children = append(children, &TreeNode{
			Name: e.Name, FullPath: e.FullPath, IsDir: e.IsDir, Parent: targetNode,
		})
	}
	targetNode.Children = children
}

// --- Commands ---

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

type ExportCompleteMsg struct {
	Count int
	Err   error
}

func runExportCmd(root string, selections map[string]bool, includeMode bool) tea.Cmd {
	return func() tea.Msg {
		var selList []string
		for p := range selections {
			selList = append(selList, p)
		}
		sort.Strings(selList)

		config := core.ExtractionConfig{
			RootPath:         root,
			OutputFilePath:   "pandabrew_export.txt",
			ManualSelections: selList,
			IncludeMode:      includeMode,
		}
		meta, err := core.RunExtraction(config)
		return ExportCompleteMsg{Count: meta.TotalFiles, Err: err}
	}
}
