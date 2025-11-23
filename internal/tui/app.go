// Package tui implements the terminal user interface using Bubble Tea.
package tui

import (
	"fmt"
	"path/filepath"

	"pandabrew/internal/core"

	"github.com/charmbracelet/bubbles/spinner"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	colorPurple = lipgloss.Color("#7D56F4")
	colorGray   = lipgloss.Color("#626262")
	colorLight  = lipgloss.Color("#FAFAFA")

	styleTab = lipgloss.NewStyle().
			Padding(0, 1).
			Foreground(colorGray).
			Border(lipgloss.NormalBorder(), false, true, false, false).
			BorderForeground(colorGray)

	styleTabActive = styleTab.
			Foreground(colorLight).
			Background(colorPurple).
			BorderForeground(colorPurple)

	styleSidebar = lipgloss.NewStyle().
			Width(40).
			Padding(1).
			Border(lipgloss.NormalBorder(), false, true, false, false).
			BorderForeground(colorGray)

	styleMain = lipgloss.NewStyle().
			Padding(1)
)

// AppModel is the single source of truth for the UI state.
type AppModel struct {
	Session       *core.Session
	TabStates     map[string]*TabState
	Spinner       spinner.Model
	Loading       bool
	StatusMessage string
	Width, Height int
}

type TabState struct {
	TreeRoot    *TreeNode
	CursorNode  *TreeNode
	InputRoot   textinput.Model
	InputOutput textinput.Model
	ActiveInput int // 0=None, 1=Root, 2=Output
}

type TreeNode struct {
	Name     string
	FullPath string
	IsDir    bool
	Expanded bool
	Children []*TreeNode
	Parent   *TreeNode
}

func InitialModel(session *core.Session) AppModel {
	s := spinner.New()
	s.Spinner = spinner.Dot
	s.Style = lipgloss.NewStyle().Foreground(colorPurple)

	model := AppModel{
		Session:   session,
		TabStates: make(map[string]*TabState),
		Spinner:   s,
	}

	for _, space := range session.Spaces {
		model.TabStates[space.ID] = newTabState(space)
	}

	return model
}

func newTabState(space *core.DirectorySpace) *TabState {
	tiRoot := textinput.New()
	tiRoot.Placeholder = "Root Directory"
	tiRoot.SetValue(space.RootPath)

	tiOut := textinput.New()
	tiOut.Placeholder = "Output File"
	tiOut.SetValue(space.OutputFilePath)

	rootNode := &TreeNode{
		Name: space.RootPath, FullPath: space.RootPath, IsDir: true, Expanded: true,
	}

	return &TabState{
		TreeRoot:    rootNode,
		CursorNode:  rootNode,
		InputRoot:   tiRoot,
		InputOutput: tiOut,
	}
}

func (m AppModel) Init() tea.Cmd {
	activeSpace := m.Session.GetActiveSpace()
	if activeSpace != nil {
		return tea.Batch(m.Spinner.Tick, loadDirectoryCmd(activeSpace.RootPath))
	}
	return m.Spinner.Tick
}

func (m AppModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmd tea.Cmd
	var cmds []tea.Cmd

	space := m.Session.GetActiveSpace()
	var state *TabState
	if space != nil {
		state = m.TabStates[space.ID]
	}

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.Width = msg.Width
		m.Height = msg.Height
	}

	if state != nil && state.ActiveInput > 0 {
		switch msg := msg.(type) {
		case tea.KeyMsg:
			if msg.String() == "esc" || msg.String() == "enter" {
				state.ActiveInput = 0
				state.InputRoot.Blur()
				state.InputOutput.Blur()
				if state.InputRoot.Value() != space.RootPath {
					space.RootPath = state.InputRoot.Value()
					m.Loading = true
					cmds = append(cmds, loadDirectoryCmd(space.RootPath))
				}
				// FIX: Return the accumulated commands (e.g. reload directory)
				return m, tea.Batch(cmds...)
			}
		}
		if state.ActiveInput == 1 {
			state.InputRoot, cmd = state.InputRoot.Update(msg)
		} else {
			state.InputOutput, cmd = state.InputOutput.Update(msg)
		}
		return m, cmd
	}

	switch msg := msg.(type) {

	case DirLoadedMsg:
		m.Loading = false
		if msg.Err != nil {
			m.StatusMessage = "Error: " + msg.Err.Error()
		} else {
			m.populateChildren(state, msg.Path, msg.Entries)
		}

	case ExportCompleteMsg:
		m.Loading = false
		if msg.Err != nil {
			m.StatusMessage = "Failed: " + msg.Err.Error()
		} else {
			m.StatusMessage = fmt.Sprintf("Saved %d files to %s", msg.Count, space.OutputFilePath)
		}

	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit

		case "r":
			if state != nil {
				state.ActiveInput = 1
				state.InputRoot.Focus()
				return m, textinput.Blink
			}
		case "o":
			if state != nil {
				state.ActiveInput = 2
				state.InputOutput.Focus()
				return m, textinput.Blink
			}

		case "i":
			if space != nil {
				space.Config.IncludeMode = !space.Config.IncludeMode
			}
		case "c":
			if space != nil {
				space.Config.ShowContext = !space.Config.ShowContext
			}
		case "x":
			if space != nil {
				space.Config.ShowExcluded = !space.Config.ShowExcluded
			}

		case " ":
			if state != nil && state.CursorNode != nil {
				p := state.CursorNode.FullPath
				found := false
				for i, existing := range space.Config.ManualSelections {
					if existing == p {
						space.Config.ManualSelections = append(space.Config.ManualSelections[:i], space.Config.ManualSelections[i+1:]...)
						found = true
						break
					}
				}
				if !found {
					space.Config.ManualSelections = append(space.Config.ManualSelections, p)
				}
			}

		case "enter":
			if state != nil && state.CursorNode != nil && state.CursorNode.IsDir {
				state.CursorNode.Expanded = !state.CursorNode.Expanded
				if state.CursorNode.Expanded && len(state.CursorNode.Children) == 0 {
					m.Loading = true
					return m, loadDirectoryCmd(state.CursorNode.FullPath)
				}
			}

		case "ctrl+s":
			sm := core.NewSessionManager("")
			// FIX: Check error return from Save
			if err := sm.Save(m.Session); err != nil {
				m.StatusMessage = "Error saving session: " + err.Error()
			} else {
				m.StatusMessage = "Session Saved"
			}

		case "ctrl+e":
			if space != nil {
				m.Loading = true
				m.StatusMessage = "Exporting..."
				return m, runExportCmd(space)
			}
		}
	}

	if m.Loading {
		m.Spinner, cmd = m.Spinner.Update(msg)
		cmds = append(cmds, cmd)
	}

	return m, tea.Batch(cmds...)
}

func (m AppModel) View() string {
	space := m.Session.GetActiveSpace()

	if space == nil {
		return "No workspace open. Run with --root ."
	}

	state := m.TabStates[space.ID]

	var tabs []string
	for _, s := range m.Session.Spaces {
		name := filepath.Base(s.RootPath)
		style := styleTab
		if s.ID == m.Session.ActiveSpaceID {
			style = styleTabActive
		}
		tabs = append(tabs, style.Render(name))
	}
	tabs = append(tabs, styleTab.Render("[ Ctrl+S Save ]"))
	tabRow := lipgloss.JoinHorizontal(lipgloss.Top, tabs...)

	settings := lipgloss.JoinVertical(lipgloss.Left,
		"Directory Settings:",
		state.InputRoot.View(),
		state.InputOutput.View(),
		"",
		"Extraction Options:",
		checkbox("Include Mode (i)", space.Config.IncludeMode),
		checkbox("Show Context (c)", space.Config.ShowContext),
		checkbox("Show Excluded (x)", space.Config.ShowExcluded),
	)
	sidebar := styleSidebar.Render(settings)

	treeContent := fmt.Sprintf("Root: %s\n\n[Tree View Placeholder]\nUse [Space] to Select\nUse [Enter] to Expand\n\nSelected: %d items",
		space.RootPath, len(space.Config.ManualSelections))
	main := styleMain.Render(treeContent)

	body := lipgloss.JoinHorizontal(lipgloss.Top, sidebar, main)

	status := m.StatusMessage
	if m.Loading {
		status = fmt.Sprintf("%s %s", m.Spinner.View(), m.StatusMessage)
	}

	return lipgloss.JoinVertical(lipgloss.Left, tabRow, body, status)
}

func checkbox(label string, checked bool) string {
	if checked {
		return fmt.Sprintf("[x] %s", label)
	}
	return fmt.Sprintf("[ ] %s", label)
}

func (m *AppModel) populateChildren(state *TabState, parentPath string, entries []core.DirEntry) {
	targetNode := state.CursorNode
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

func runExportCmd(space *core.DirectorySpace) tea.Cmd {
	return func() tea.Msg {
		// Deep copy config manually if needed to avoid race condition
		// For MVP, passing pointer is acceptable as core functions are read-only on config
		meta, err := core.RunExtraction(space)
		return ExportCompleteMsg{Count: meta.TotalFiles, Err: err}
	}
}
