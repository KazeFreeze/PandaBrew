// Package tui implements the terminal user interface using Bubble Tea.
package tui

import (
	"fmt"
	"path/filepath"
	"strings"

	"pandabrew/internal/core"

	"github.com/charmbracelet/bubbles/spinner"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// --- Styles ---
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
			Width(35).
			Padding(1).
			Border(lipgloss.NormalBorder(), false, true, false, false).
			BorderForeground(colorGray)

	styleMain = lipgloss.NewStyle().
			Padding(1).
			MarginLeft(1)

	styleSelected = lipgloss.NewStyle().
			Foreground(colorPurple).
			Bold(true)
)

// --- Model ---

type AppModel struct {
	Session       *core.Session
	TabStates     map[string]*TabState
	Spinner       spinner.Model
	Loading       bool
	StatusMessage string
	Width, Height int
}

type TabState struct {
	TreeRoot     *TreeNode
	VisibleNodes []*TreeNode
	CursorIndex  int

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

// --- Init ---

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
	tiRoot.CharLimit = 100

	tiOut := textinput.New()
	tiOut.Placeholder = "Output File"
	tiOut.SetValue(space.OutputFilePath)
	tiOut.CharLimit = 100

	rootNode := &TreeNode{
		Name:     space.RootPath,
		FullPath: space.RootPath,
		IsDir:    true,
		Expanded: true,
	}

	ts := &TabState{
		TreeRoot:    rootNode,
		InputRoot:   tiRoot,
		InputOutput: tiOut,
		CursorIndex: 0,
	}

	ts.rebuildVisibleList()
	return ts
}

func (m AppModel) Init() tea.Cmd {
	activeSpace := m.Session.GetActiveSpace()
	if activeSpace != nil {
		return tea.Batch(m.Spinner.Tick, loadDirectoryCmd(activeSpace.RootPath))
	}
	return m.Spinner.Tick
}

// --- Update ---

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
			switch msg.String() {
			case "esc":
				state.ActiveInput = 0
				state.InputRoot.Blur()
				state.InputOutput.Blur()
				return m, nil
			case "enter":
				state.ActiveInput = 0
				state.InputRoot.Blur()
				state.InputOutput.Blur()
				if state.InputRoot.Value() != space.RootPath {
					space.RootPath = state.InputRoot.Value()
					state.TreeRoot = &TreeNode{Name: space.RootPath, FullPath: space.RootPath, IsDir: true, Expanded: true}
					state.rebuildVisibleList()
					m.Loading = true
					cmds = append(cmds, loadDirectoryCmd(space.RootPath))
				}
				if state.InputOutput.Value() != space.OutputFilePath {
					space.OutputFilePath = state.InputOutput.Value()
				}
				// FIX: Execute any accumulated commands (like directory reload)
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
			state.rebuildVisibleList()
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

		case "tab":
			if len(m.Session.Spaces) > 1 {
				currIdx := 0
				for i, s := range m.Session.Spaces {
					if s.ID == space.ID {
						currIdx = i
						break
					}
				}
				nextIdx := (currIdx + 1) % len(m.Session.Spaces)
				m.Session.ActiveSpaceID = m.Session.Spaces[nextIdx].ID
				newSpace := m.Session.GetActiveSpace()
				newState := m.TabStates[newSpace.ID]
				if len(newState.TreeRoot.Children) == 0 {
					cmds = append(cmds, loadDirectoryCmd(newSpace.RootPath))
				}
			}

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

		case "up", "k":
			if state != nil && state.CursorIndex > 0 {
				state.CursorIndex--
			}
		case "down", "j":
			if state != nil && state.CursorIndex < len(state.VisibleNodes)-1 {
				state.CursorIndex++
			}

		case " ":
			if state != nil && len(state.VisibleNodes) > 0 {
				node := state.VisibleNodes[state.CursorIndex]
				p := node.FullPath

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

		case "enter", "right", "l":
			if state != nil && len(state.VisibleNodes) > 0 {
				node := state.VisibleNodes[state.CursorIndex]
				if node.IsDir {
					node.Expanded = !node.Expanded
					if node.Expanded && len(node.Children) == 0 {
						m.Loading = true
						m.StatusMessage = fmt.Sprintf("Loading %s...", node.Name)
						cmds = append(cmds, loadDirectoryCmd(node.FullPath))
					} else {
						state.rebuildVisibleList()
					}
				}
			}

		case "left", "h":
			if state != nil && len(state.VisibleNodes) > 0 {
				node := state.VisibleNodes[state.CursorIndex]
				if node.IsDir && node.Expanded {
					node.Expanded = false
					state.rebuildVisibleList()
				} else if node.Parent != nil {
					for i, n := range state.VisibleNodes {
						if n == node.Parent {
							state.CursorIndex = i
							break
						}
					}
				}
			}

		case "ctrl+s":
			sm := core.NewSessionManager("")
			if err := sm.Save(m.Session); err != nil {
				m.StatusMessage = "Error saving: " + err.Error()
			} else {
				m.StatusMessage = "Session Saved"
			}

		case "ctrl+e":
			if space != nil {
				m.Loading = true
				m.StatusMessage = "Exporting..."
				cmds = append(cmds, runExportCmd(space))
			}
		}
	}

	if m.Loading {
		m.Spinner, cmd = m.Spinner.Update(msg)
		cmds = append(cmds, cmd)
	}

	return m, tea.Batch(cmds...)
}

func (ts *TabState) rebuildVisibleList() {
	ts.VisibleNodes = make([]*TreeNode, 0)
	var walk func(*TreeNode)
	walk = func(n *TreeNode) {
		ts.VisibleNodes = append(ts.VisibleNodes, n)
		if n.Expanded {
			for _, child := range n.Children {
				walk(child)
			}
		}
	}
	if ts.TreeRoot != nil {
		walk(ts.TreeRoot)
	}

	if ts.CursorIndex >= len(ts.VisibleNodes) {
		ts.CursorIndex = len(ts.VisibleNodes) - 1
	}
	if ts.CursorIndex < 0 {
		ts.CursorIndex = 0
	}
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
	tabs = append(tabs, styleTab.Render(" [Tab] Next Space "))
	tabs = append(tabs, styleTab.Render(" [Ctrl+S] Save "))
	tabRow := lipgloss.JoinHorizontal(lipgloss.Top, tabs...)

	settings := lipgloss.JoinVertical(lipgloss.Left,
		lipgloss.NewStyle().Bold(true).Render("Directory Settings"),
		"",
		"Root (r):",
		state.InputRoot.View(),
		"",
		"Output (o):",
		state.InputOutput.View(),
		"",
		lipgloss.NewStyle().Bold(true).Render("Extraction Options"),
		"",
		checkbox("Include Mode (i)", space.Config.IncludeMode),
		checkbox("Show Context (c)", space.Config.ShowContext),
		checkbox("Show Excluded (x)", space.Config.ShowExcluded),
		"",
		lipgloss.NewStyle().Foreground(colorGray).Render("Stats:"),
		fmt.Sprintf("%d Selections", len(space.Config.ManualSelections)),
	)
	sidebar := styleSidebar.Height(m.Height - 5).Render(settings)

	var treeRows []string
	startRow := 0
	if state.CursorIndex > (m.Height / 2) {
		startRow = state.CursorIndex - (m.Height / 2)
	}
	endRow := startRow + (m.Height - 6)

	// FIX: Modernized min usage
	endRow = min(endRow, len(state.VisibleNodes))

	for i := startRow; i < endRow; i++ {
		node := state.VisibleNodes[i]

		depth := strings.Count(node.FullPath, string(filepath.Separator)) - strings.Count(space.RootPath, string(filepath.Separator))
		// FIX: Modernized max usage
		depth = max(0, depth)
		indent := strings.Repeat("  ", depth)

		icon := "📄"
		if node.IsDir {
			if node.Expanded {
				icon = "📂"
			} else {
				icon = "📁"
			}
		}

		check := "[ ]"
		for _, s := range space.Config.ManualSelections {
			if s == node.FullPath {
				check = "[x]"
				break
			}
			if strings.HasPrefix(node.FullPath, s+string(filepath.Separator)) {
				check = "[*]"
				break
			}
		}

		line := fmt.Sprintf("%s%s %s %s", indent, check, icon, node.Name)

		if i == state.CursorIndex {
			line = styleSelected.Render("> " + line)
		} else {
			line = "  " + line
		}
		treeRows = append(treeRows, line)
	}

	if len(state.VisibleNodes) == 0 {
		treeRows = append(treeRows, "  (Empty or Loading...)")
	}

	mainContent := lipgloss.JoinVertical(lipgloss.Left, treeRows...)
	main := styleMain.Width(m.Width - 45).Height(m.Height - 5).Render(mainContent)

	body := lipgloss.JoinHorizontal(lipgloss.Top, sidebar, main)

	status := m.StatusMessage
	if m.Loading {
		status = fmt.Sprintf("%s %s", m.Spinner.View(), m.StatusMessage)
	}
	footer := lipgloss.NewStyle().Foreground(colorLight).Background(colorGray).Width(m.Width).Render(" " + status)

	return lipgloss.JoinVertical(lipgloss.Left, tabRow, body, footer)
}

func checkbox(label string, checked bool) string {
	if checked {
		return fmt.Sprintf("[x] %s", label)
	}
	return fmt.Sprintf("[ ] %s", label)
}

func (m *AppModel) populateChildren(state *TabState, parentPath string, entries []core.DirEntry) {
	var targetNode *TreeNode

	var find func(*TreeNode) *TreeNode
	find = func(n *TreeNode) *TreeNode {
		if n.FullPath == parentPath {
			return n
		}
		for _, c := range n.Children {
			if res := find(c); res != nil {
				return res
			}
		}
		return nil
	}

	if state.TreeRoot != nil {
		targetNode = find(state.TreeRoot)
	}

	if targetNode == nil {
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
		meta, err := core.RunExtraction(space)
		return ExportCompleteMsg{Count: meta.TotalFiles, Err: err}
	}
}
