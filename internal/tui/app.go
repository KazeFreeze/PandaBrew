// Package tui implements the terminal user interface using Bubble Tea.
package tui

import (
	"fmt"
	"path/filepath"
	"slices"
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
	colorGreen  = lipgloss.Color("#42f584")
	colorYellow = lipgloss.Color("#f5d442")

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

// AppModel is the single source of truth for the UI state.
type AppModel struct {
	Session       *core.Session
	TabStates     map[string]*TabState
	Spinner       spinner.Model
	Loading       bool
	StatusMessage string
	Width, Height int
}

// TabState holds the UI state for a specific directory space (tab).
type TabState struct {
	TreeRoot     *TreeNode
	VisibleNodes []*TreeNode
	CursorIndex  int

	// Inputs
	InputRoot    textinput.Model
	InputOutput  textinput.Model
	InputInclude textinput.Model // Patterns like *.go
	InputExclude textinput.Model // Patterns like node_modules

	ActiveInput int // 0=None, 1=Root, 2=Output, 3=Include, 4=Exclude
}

// TreeNode represents the VISUAL state of a file.
type TreeNode struct {
	Name     string
	FullPath string
	IsDir    bool
	Expanded bool
	Children []*TreeNode
	Parent   *TreeNode
}

// --- Init ---

// InitialModel creates the starting state of the TUI.
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
	// Helper to create standard inputs
	newInput := func(placeholder, value string) textinput.Model {
		t := textinput.New()
		t.Placeholder = placeholder
		t.SetValue(value)
		t.CharLimit = 100
		return t
	}

	ts := &TabState{
		InputRoot:    newInput("Root Directory", space.RootPath),
		InputOutput:  newInput("Output File", space.OutputFilePath),
		InputInclude: newInput("*.go, src/", strings.Join(space.Config.IncludePatterns, ", ")),
		InputExclude: newInput(".git, node_modules", strings.Join(space.Config.ExcludePatterns, ", ")),
		CursorIndex:  0,
	}

	// Initialize Tree
	ts.TreeRoot = &TreeNode{
		Name:     space.RootPath,
		FullPath: space.RootPath,
		IsDir:    true,
		Expanded: true,
	}

	ts.rebuildVisibleList()
	return ts
}

// Init handles the initial command to run when the app starts.
func (m AppModel) Init() tea.Cmd {
	activeSpace := m.Session.GetActiveSpace()
	if activeSpace != nil {
		return tea.Batch(m.Spinner.Tick, loadDirectoryCmd(activeSpace.RootPath))
	}
	return m.Spinner.Tick
}

// --- Update ---

// Update handles incoming messages and updates the model.
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

	// 1. Handle Inputs (Blocking)
	if state != nil && state.ActiveInput > 0 {
		switch msg := msg.(type) {
		case tea.KeyMsg:
			switch msg.String() {
			case "esc":
				state.ActiveInput = 0
				blurAll(state)
				return m, nil
			case "enter":
				state.ActiveInput = 0
				blurAll(state)
				// Sync values back to Config
				if state.InputRoot.Value() != space.RootPath {
					space.RootPath = state.InputRoot.Value()
					// Reset tree on root change
					state.TreeRoot = &TreeNode{Name: space.RootPath, FullPath: space.RootPath, IsDir: true, Expanded: true}
					state.rebuildVisibleList()
					m.Loading = true
					cmds = append(cmds, loadDirectoryCmd(space.RootPath))
				}
				space.OutputFilePath = state.InputOutput.Value()

				// Parse comma-separated lists for patterns
				space.Config.IncludePatterns = splitClean(state.InputInclude.Value())
				space.Config.ExcludePatterns = splitClean(state.InputExclude.Value())

				return m, tea.Batch(cmds...)
			}
		}

		// Forward to active input
		switch state.ActiveInput {
		case 1:
			state.InputRoot, cmd = state.InputRoot.Update(msg)
		case 2:
			state.InputOutput, cmd = state.InputOutput.Update(msg)
		case 3:
			state.InputInclude, cmd = state.InputInclude.Update(msg)
		case 4:
			state.InputExclude, cmd = state.InputExclude.Update(msg)
		}
		return m, cmd
	}

	switch msg := msg.(type) {

	// Async Results
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
			m.StatusMessage = fmt.Sprintf("Exported %d files (~%d tokens) to %s",
				msg.Count, msg.Tokens, filepath.Base(space.OutputFilePath))
		}

	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit

		// Tab Navigation
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
				// Init new tab if needed
				newSpace := m.Session.GetActiveSpace()
				newState := m.TabStates[newSpace.ID]
				if len(newState.TreeRoot.Children) == 0 {
					cmds = append(cmds, loadDirectoryCmd(newSpace.RootPath))
				}
			}

		// Input Hotkeys
		case "r":
			focusInput(state, 1)
			return m, textinput.Blink
		case "o":
			focusInput(state, 2)
			return m, textinput.Blink
		case "f": // "Filter" (Include)
			focusInput(state, 3)
			return m, textinput.Blink
		case "g": // "Global Exclude"
			focusInput(state, 4)
			return m, textinput.Blink

		// Toggles
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

		// Tree Nav
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
				toggleSelection(space, node.FullPath)
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
					// Jump to parent
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

// View renders the UI.
func (m AppModel) View() string {
	space := m.Session.GetActiveSpace()
	if space == nil {
		return "No workspace open."
	}
	state := m.TabStates[space.ID]

	// 1. Tabs
	var tabs []string
	for _, s := range m.Session.Spaces {
		name := filepath.Base(s.RootPath)
		style := styleTab
		if s.ID == m.Session.ActiveSpaceID {
			style = styleTabActive
		}
		tabs = append(tabs, style.Render(name))
	}
	tabs = append(tabs, styleTab.Render(" [Tab] Next "))
	tabRow := lipgloss.JoinHorizontal(lipgloss.Top, tabs...)

	// 2. Sidebar
	settings := lipgloss.JoinVertical(lipgloss.Left,
		lipgloss.NewStyle().Bold(true).Render("Settings"),
		"",
		"Root (r):", state.InputRoot.View(), "",
		"Output (o):", state.InputOutput.View(), "",
		"Include (f):", state.InputInclude.View(), "",
		"Exclude (g):", state.InputExclude.View(), "",
		lipgloss.NewStyle().Bold(true).Render("Options"),
		checkbox("Include Mode (i)", space.Config.IncludeMode),
		checkbox("Show Context (c)", space.Config.ShowContext),
		checkbox("Show Excluded (x)", space.Config.ShowExcluded),
		"",
		lipgloss.NewStyle().Foreground(colorGray).Render(fmt.Sprintf("Selected: %d", len(space.Config.ManualSelections))),
	)
	sidebar := styleSidebar.Height(m.Height - 5).Render(settings)

	// 3. File Tree
	var treeRows []string
	startRow := 0
	if state.CursorIndex > (m.Height / 2) {
		startRow = state.CursorIndex - (m.Height / 2)
	}
	endRow := startRow + (m.Height - 6)
	endRow = min(endRow, len(state.VisibleNodes))

	for i := startRow; i < endRow; i++ {
		node := state.VisibleNodes[i]

		depth := max(0, strings.Count(node.FullPath, string(filepath.Separator))-strings.Count(space.RootPath, string(filepath.Separator)))
		indent := strings.Repeat("  ", depth)

		icon := "📄"
		if node.IsDir {
			if node.Expanded {
				icon = "📂"
			} else {
				icon = "📁"
			}
		}

		// --- Visual Selection Logic ---
		check := "[ ]"
		style := lipgloss.NewStyle()

		// 1. Check Exact Match (Priority 1)
		isExact := slices.Contains(space.Config.ManualSelections, node.FullPath)
		if isExact {
			check = "[x]"
			style = style.Foreground(colorGreen)
		}

		// 2. Check Implicit/Ancestor Match (Priority 2)
		if !isExact {
			for _, s := range space.Config.ManualSelections {
				if strings.HasPrefix(node.FullPath, s+string(filepath.Separator)) {
					check = "[*]"
					style = style.Foreground(colorGreen)
					break
				}
			}
		}

		// 3. Check Partial/Descendant Match (Priority 3)
		if check == "[ ]" && node.IsDir {
			prefix := node.FullPath + string(filepath.Separator)
			for _, s := range space.Config.ManualSelections {
				if strings.HasPrefix(s, prefix) {
					check = "[-]"
					style = style.Foreground(colorYellow)
					break
				}
			}
		}

		line := fmt.Sprintf("%s%s %s %s", indent, check, icon, node.Name)
		line = style.Render(line)

		if i == state.CursorIndex {
			line = styleSelected.Render("> " + line)
		} else {
			line = "  " + line
		}
		treeRows = append(treeRows, line)
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

// --- Actions ---

func toggleSelection(space *core.DirectorySpace, path string) {
	found := false
	for i, existing := range space.Config.ManualSelections {
		if existing == path {
			space.Config.ManualSelections = append(space.Config.ManualSelections[:i], space.Config.ManualSelections[i+1:]...)
			found = true
			break
		}
	}
	if !found {
		space.Config.ManualSelections = append(space.Config.ManualSelections, path)
	}
}

func focusInput(state *TabState, idx int) {
	state.ActiveInput = idx
	blurAll(state)
	switch idx {
	case 1:
		state.InputRoot.Focus()
	case 2:
		state.InputOutput.Focus()
	case 3:
		state.InputInclude.Focus()
	case 4:
		state.InputExclude.Focus()
	}
}

func blurAll(state *TabState) {
	state.InputRoot.Blur()
	state.InputOutput.Blur()
	state.InputInclude.Blur()
	state.InputExclude.Blur()
}

func splitClean(s string) []string {
	if s == "" {
		return []string{}
	}
	parts := strings.Split(s, ",")
	var res []string
	for _, p := range parts {
		t := strings.TrimSpace(p)
		if t != "" {
			res = append(res, t)
		}
	}
	return res
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

// ExportCompleteMsg carries the result of an extraction operation, including file count and token estimate.
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
