// Package tui implements the terminal user interface using Bubble Tea.
package tui

import (
	"fmt"
	"path/filepath"
	"slices"
	"strings"

	"pandabrew/internal/core"

	"github.com/charmbracelet/bubbles/help"
	"github.com/charmbracelet/bubbles/key"
	"github.com/charmbracelet/bubbles/progress"
	"github.com/charmbracelet/bubbles/spinner"
	"github.com/charmbracelet/bubbles/textinput"
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// --- Nerd Font Icons ---
// Browse https://www.nerdfonts.com/cheat-sheet for more icons
// These use Unicode escape sequences to ensure proper encoding
const (
	iconFolder     = "\uf07b" // nf-fa-folder
	iconFolderOpen = "\uf07c" // nf-fa-folder_open
	iconFile       = "\uf016" // nf-fa-file_o
	iconGo         = "\ue627" // nf-seti-go
	iconMarkdown   = "\ue73e" // nf-dev-markdown
	iconJSON       = "\ue60b" // nf-seti-json
	iconYAML       = "\ue6a5" // nf-seti-yml
	iconGit        = "\ue702" // nf-dev-git
	iconDocker     = "\uf308" // nf-dev-docker
	iconJS         = "\ue74e" // nf-seti-javascript
	iconTS         = "\ue628" // nf-seti-typescript
	iconPython     = "\ue73c" // nf-dev-python
	iconRust       = "\ue7a8" // nf-dev-rust
	iconHTML       = "\ue736" // nf-dev-html5
	iconCSS        = "\ue749" // nf-dev-css3
	iconImage      = "\uf1c5" // nf-fa-file_image_o
	iconArchive    = "\uf1c6" // nf-fa-file_archive_o
	iconConfig     = "\uf013" // nf-fa-cog
	iconText       = "\uf0f6" // nf-fa-file_text_o
	iconCode       = "\uf121" // nf-fa-code

	iconCheckSquare = "\uf046" // nf-fa-check_square_o
	iconSquare      = "\uf096" // nf-fa-square_o
	iconDot         = "\uf111" // nf-fa-circle (filled)
	iconCircle      = "\uf10c" // nf-fa-circle_o (outline)

	iconKeyboard = "\uf11c" // nf-fa-keyboard_o
	iconSave     = "\uf0c7" // nf-fa-save
	iconExport   = "\uf019" // nf-fa-download
	iconHelp     = "\uf059" // nf-fa-question_circle
	iconGear     = "\uf013" // nf-fa-cog
	iconFilter   = "\uf0b0" // nf-fa-filter
	iconTree     = "\uf115" // nf-fa-folder_open (alternate tree icon)

	// Tree drawing characters
	treeSpace = "  "
)

// --- Styles ---
var (
	// Color Palette
	colorPurple    = lipgloss.Color("#7D56F4")
	colorGray      = lipgloss.Color("#626262")
	colorGrayLight = lipgloss.Color("#808080")
	colorGrayDark  = lipgloss.Color("#404040")
	colorLight     = lipgloss.Color("#FAFAFA")
	colorGreen     = lipgloss.Color("#42f584")
	colorYellow    = lipgloss.Color("#f5d442")
	colorBlue      = lipgloss.Color("#61AFEF")
	colorRed       = lipgloss.Color("#E06C75")
	colorOrange    = lipgloss.Color("#FF8C00")
	colorCyan      = lipgloss.Color("#56B6C2")

	// Tab Styles
	styleTab = lipgloss.NewStyle().
			Padding(0, 2).
			Foreground(colorGrayLight).
			Background(colorGrayDark)

	styleTabActive = lipgloss.NewStyle().
			Padding(0, 2).
			Foreground(colorLight).
			Background(colorPurple).
			Bold(true)

	// Sidebar Styles
	styleSidebar = lipgloss.NewStyle().
			Width(38).
			Padding(1, 2).
			Border(lipgloss.RoundedBorder(), false, true, false, false).
			BorderForeground(colorPurple)

	styleSectionHeader = lipgloss.NewStyle().
				Foreground(colorPurple).
				Bold(true).
				Underline(true).
				MarginBottom(1)

	styleInputLabel = lipgloss.NewStyle().
			Foreground(colorBlue).
			Bold(true).
			Width(10)

	styleInputBox = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colorGray).
			Padding(0, 1)

	styleInputBoxFocused = lipgloss.NewStyle().
				Border(lipgloss.RoundedBorder()).
				BorderForeground(colorPurple).
				Padding(0, 1)

	// Main Content Styles
	styleMain = lipgloss.NewStyle().
			Padding(1, 2).
			MarginLeft(1)

	styleCursor = lipgloss.NewStyle().
			Foreground(colorPurple).
			Bold(true)

	// Status Bar Styles
	styleStatusLeft = lipgloss.NewStyle().
			Foreground(colorLight).
			Background(colorPurple).
			Padding(0, 2).
			Bold(true)

	styleStatusMiddle = lipgloss.NewStyle().
				Foreground(colorLight).
				Background(colorGrayLight).
				Padding(0, 2)

	styleStatusRight = lipgloss.NewStyle().
				Foreground(colorGrayLight).
				Background(colorGrayDark).
				Padding(0, 2)

	// Breadcrumb Style
	styleBreadcrumb = lipgloss.NewStyle().
			Foreground(colorGray).
			MarginBottom(1)

	styleBreadcrumbLast = lipgloss.NewStyle().
				Foreground(colorPurple).
				Bold(true)

	styleBreadcrumbSep = lipgloss.NewStyle().
				Foreground(colorGray)
)

// --- Key Bindings ---
type keyMap struct {
	Up      key.Binding
	Down    key.Binding
	Left    key.Binding
	Right   key.Binding
	Select  key.Binding
	Quit    key.Binding
	Save    key.Binding
	Export  key.Binding
	Help    key.Binding
	Tab     key.Binding
	Root    key.Binding
	Output  key.Binding
	Include key.Binding
	Exclude key.Binding
	ToggleI key.Binding
	ToggleC key.Binding
	ToggleX key.Binding
}

func (k keyMap) ShortHelp() []key.Binding {
	return []key.Binding{k.Help, k.Quit}
}

func (k keyMap) FullHelp() [][]key.Binding {
	return [][]key.Binding{
		{k.Up, k.Down, k.Left, k.Right},
		{k.Select, k.Tab, k.Save, k.Export},
		{k.Root, k.Output, k.Include, k.Exclude},
		{k.ToggleI, k.ToggleC, k.ToggleX, k.Quit},
	}
}

var keys = keyMap{
	Up: key.NewBinding(
		key.WithKeys("up", "k"),
		key.WithHelp("↑/k", "up"),
	),
	Down: key.NewBinding(
		key.WithKeys("down", "j"),
		key.WithHelp("↓/j", "down"),
	),
	Left: key.NewBinding(
		key.WithKeys("left", "h"),
		key.WithHelp("←/h", "collapse"),
	),
	Right: key.NewBinding(
		key.WithKeys("right", "l", "enter"),
		key.WithHelp("→/l", "expand"),
	),
	Select: key.NewBinding(
		key.WithKeys(" "),
		key.WithHelp("space", "select"),
	),
	Quit: key.NewBinding(
		key.WithKeys("q", "ctrl+c"),
		key.WithHelp("q", "quit"),
	),
	Save: key.NewBinding(
		key.WithKeys("ctrl+s"),
		key.WithHelp("ctrl+s", "save"),
	),
	Export: key.NewBinding(
		key.WithKeys("ctrl+e"),
		key.WithHelp("ctrl+e", "export"),
	),
	Help: key.NewBinding(
		key.WithKeys("?"),
		key.WithHelp("?", "help"),
	),
	Tab: key.NewBinding(
		key.WithKeys("tab"),
		key.WithHelp("tab", "next tab"),
	),
	Root: key.NewBinding(
		key.WithKeys("r"),
		key.WithHelp("r", "edit root"),
	),
	Output: key.NewBinding(
		key.WithKeys("o"),
		key.WithHelp("o", "edit output"),
	),
	Include: key.NewBinding(
		key.WithKeys("f"),
		key.WithHelp("f", "edit include"),
	),
	Exclude: key.NewBinding(
		key.WithKeys("g"),
		key.WithHelp("g", "edit exclude"),
	),
	ToggleI: key.NewBinding(
		key.WithKeys("i"),
		key.WithHelp("i", "toggle include mode"),
	),
	ToggleC: key.NewBinding(
		key.WithKeys("c"),
		key.WithHelp("c", "toggle context"),
	),
	ToggleX: key.NewBinding(
		key.WithKeys("x"),
		key.WithHelp("x", "toggle excluded"),
	),
}

// --- Model ---

// AppModel is the single source of truth for the UI state.
type AppModel struct {
	Session       *core.Session
	TabStates     map[string]*TabState
	Spinner       spinner.Model
	Progress      progress.Model
	Help          help.Model
	Viewport      viewport.Model
	Loading       bool
	ShowHelp      bool
	StatusMessage string
	Width, Height int
	keys          keyMap
}

// TabState holds the UI state for a specific directory space (tab).
type TabState struct {
	TreeRoot     *TreeNode
	VisibleNodes []*TreeNode
	CursorIndex  int

	// Inputs
	InputRoot    textinput.Model
	InputOutput  textinput.Model
	InputInclude textinput.Model
	InputExclude textinput.Model

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
	IsLast   bool // For tree rendering
}

// --- Init ---

// InitialModel creates the starting state of the TUI.
func InitialModel(session *core.Session) AppModel {
	s := spinner.New()
	s.Spinner = spinner.Dot
	s.Style = lipgloss.NewStyle().Foreground(colorPurple)

	prog := progress.New(
		progress.WithDefaultGradient(),
		progress.WithWidth(40),
	)

	model := AppModel{
		Session:   session,
		TabStates: make(map[string]*TabState),
		Spinner:   s,
		Progress:  prog,
		Help:      help.New(),
		keys:      keys,
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
		t.CharLimit = 150
		t.Width = 30
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
		Name:     filepath.Base(space.RootPath),
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
					state.TreeRoot = &TreeNode{
						Name:     filepath.Base(space.RootPath),
						FullPath: space.RootPath,
						IsDir:    true,
						Expanded: true,
					}
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
			m.StatusMessage = fmt.Sprintf("✓ Exported %d files (~%d tokens) to %s",
				msg.Count, msg.Tokens, filepath.Base(space.OutputFilePath))
		}

	case tea.KeyMsg:
		switch {
		case key.Matches(msg, m.keys.Quit):
			return m, tea.Quit

		case key.Matches(msg, m.keys.Help):
			m.ShowHelp = !m.ShowHelp

		case key.Matches(msg, m.keys.Tab):
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

		case key.Matches(msg, m.keys.Root):
			focusInput(state, 1)
			return m, textinput.Blink
		case key.Matches(msg, m.keys.Output):
			focusInput(state, 2)
			return m, textinput.Blink
		case key.Matches(msg, m.keys.Include):
			focusInput(state, 3)
			return m, textinput.Blink
		case key.Matches(msg, m.keys.Exclude):
			focusInput(state, 4)
			return m, textinput.Blink

		case key.Matches(msg, m.keys.ToggleI):
			if space != nil {
				space.Config.IncludeMode = !space.Config.IncludeMode
			}
		case key.Matches(msg, m.keys.ToggleC):
			if space != nil {
				space.Config.ShowContext = !space.Config.ShowContext
			}
		case key.Matches(msg, m.keys.ToggleX):
			if space != nil {
				space.Config.ShowExcluded = !space.Config.ShowExcluded
			}

		case key.Matches(msg, m.keys.Up):
			if state != nil && state.CursorIndex > 0 {
				state.CursorIndex--
			}
		case key.Matches(msg, m.keys.Down):
			if state != nil && state.CursorIndex < len(state.VisibleNodes)-1 {
				state.CursorIndex++
			}

		case key.Matches(msg, m.keys.Select):
			if state != nil && len(state.VisibleNodes) > 0 {
				node := state.VisibleNodes[state.CursorIndex]
				toggleSelection(space, node.FullPath)
			}

		case key.Matches(msg, m.keys.Right):
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

		case key.Matches(msg, m.keys.Left):
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

		case key.Matches(msg, m.keys.Save):
			sm := core.NewSessionManager("")
			if err := sm.Save(m.Session); err != nil {
				m.StatusMessage = iconSave + " Error: " + err.Error()
			} else {
				m.StatusMessage = iconSave + " Session Saved"
			}

		case key.Matches(msg, m.keys.Export):
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
			// Mark last child for tree rendering
			for i, child := range n.Children {
				child.IsLast = (i == len(n.Children)-1)
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

	// Show help overlay
	if m.ShowHelp {
		return m.renderHelpView()
	}

	// 1. Tabs
	tabs := m.renderTabs()

	// 2. Breadcrumbs
	breadcrumbs := m.renderBreadcrumbs(space.RootPath)

	// 3. Sidebar
	sidebar := m.renderSidebar(state, space)

	// 4. File Tree
	tree := m.renderTree(state, space)

	// 5. Footer
	footer := m.renderFooter(space)

	// Combine
	body := lipgloss.JoinHorizontal(lipgloss.Top, sidebar, tree)
	main := lipgloss.JoinVertical(lipgloss.Left, tabs, breadcrumbs, body, footer)

	return main
}

func (m AppModel) renderTabs() string {
	var tabs []string
	for _, s := range m.Session.Spaces {
		name := iconFolder + " " + filepath.Base(s.RootPath)
		style := styleTab
		if s.ID == m.Session.ActiveSpaceID {
			style = styleTabActive
		}
		tabs = append(tabs, style.Render(name))
	}
	tabs = append(tabs, styleTab.Render(iconKeyboard+" [Tab] Switch"))
	return lipgloss.JoinHorizontal(lipgloss.Top, tabs...)
}

func (m AppModel) renderBreadcrumbs(path string) string {
	parts := strings.Split(path, string(filepath.Separator))
	var styled []string

	for i, part := range parts {
		if part == "" {
			continue
		}
		if i == len(parts)-1 {
			styled = append(styled, styleBreadcrumbLast.Render(part))
		} else {
			styled = append(styled, styleBreadcrumb.Render(part))
		}
	}

	sep := styleBreadcrumbSep.Render(" › ")
	return lipgloss.NewStyle().
		Padding(0, 2).
		Render(iconTree + " " + strings.Join(styled, sep))
}

func (m AppModel) renderSidebar(state *TabState, space *core.DirectorySpace) string {
	settings := lipgloss.JoinVertical(lipgloss.Left,
		styleSectionHeader.Render(iconGear+" Configuration"),
		"",
		m.renderInput("Root", state.InputRoot, state.ActiveInput == 1, "r"),
		"",
		m.renderInput("Output", state.InputOutput, state.ActiveInput == 2, "o"),
		"",
		m.renderInput("Include", state.InputInclude, state.ActiveInput == 3, "f"),
		"",
		m.renderInput("Exclude", state.InputExclude, state.ActiveInput == 4, "g"),
		"",
		"",
		styleSectionHeader.Render(iconFilter+" Options"),
		enhancedCheckbox("Include Mode", space.Config.IncludeMode, "i"),
		enhancedCheckbox("Show Context", space.Config.ShowContext, "c"),
		enhancedCheckbox("Show Excluded", space.Config.ShowExcluded, "x"),
		"",
		"",
		lipgloss.NewStyle().
			Foreground(colorGreen).
			Bold(true).
			Render(fmt.Sprintf("%s Selected: %d", iconCheckSquare, len(space.Config.ManualSelections))),
	)

	return styleSidebar.Height(m.Height - 7).Render(settings)
}

func (m AppModel) renderInput(label string, input textinput.Model, focused bool, hotkey string) string {
	labelWithKey := fmt.Sprintf("%s (%s)", label, hotkey)
	labelStyle := styleInputLabel.Render(labelWithKey)

	inputStyle := styleInputBox
	if focused {
		inputStyle = styleInputBoxFocused
	}

	return lipgloss.JoinVertical(
		lipgloss.Left,
		labelStyle,
		inputStyle.Render(input.View()),
	)
}

func (m AppModel) renderTree(state *TabState, space *core.DirectorySpace) string {
	var treeRows []string

	// Calculate visible window
	maxRows := m.Height - 8
	startRow := 0
	if state.CursorIndex > maxRows/2 {
		startRow = state.CursorIndex - maxRows/2
	}
	endRow := min(startRow+maxRows, len(state.VisibleNodes))

	for i := startRow; i < endRow; i++ {
		node := state.VisibleNodes[i]

		// Calculate depth
		depth := calculateDepth(node, space.RootPath)
		indent := strings.Repeat(treeSpace, depth)

		// Get appropriate icon
		icon := getFileIcon(node)

		// Selection indicator
		checkIcon, checkStyle := getSelectionIcon(node, space)

		// Build line
		line := fmt.Sprintf("%s%s %s %s", indent, checkIcon, icon, node.Name)
		line = checkStyle.Render(line)

		// Cursor
		if i == state.CursorIndex {
			line = styleCursor.Render("▶ ") + line
		} else {
			line = "  " + line
		}

		treeRows = append(treeRows, line)
	}

	mainContent := lipgloss.JoinVertical(lipgloss.Left, treeRows...)
	return styleMain.
		Width(m.Width - 45).
		Height(m.Height - 7).
		Render(mainContent)
}

func (m AppModel) renderFooter(space *core.DirectorySpace) string {
	var sections []string

	// Left: Status message
	leftSection := m.StatusMessage
	if m.Loading {
		leftSection = fmt.Sprintf("%s %s", m.Spinner.View(), m.StatusMessage)
	}
	sections = append(sections, styleStatusLeft.Render(leftSection))

	// Middle: File count
	middleSection := fmt.Sprintf("%s %d selected", iconCheckSquare, len(space.Config.ManualSelections))
	sections = append(sections, styleStatusMiddle.Render(middleSection))

	// Right: Key hints
	rightSection := fmt.Sprintf("%s help • %s save • %s export • q quit",
		iconHelp, iconSave, iconExport)
	sections = append(sections, styleStatusRight.Render(rightSection))

	footer := lipgloss.JoinHorizontal(lipgloss.Top, sections...)
	return lipgloss.NewStyle().Width(m.Width).Render(footer)
}

func (m AppModel) renderHelpView() string {
	helpView := m.Help.View(m.keys)

	title := lipgloss.NewStyle().
		Bold(true).
		Foreground(colorPurple).
		Padding(1, 0).
		Render(iconHelp + " Keyboard Shortcuts")

	box := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(colorPurple).
		Padding(1, 2).
		Width(m.Width - 4).
		Render(lipgloss.JoinVertical(lipgloss.Left, title, "", helpView))

	closeHint := lipgloss.NewStyle().
		Foreground(colorGray).
		Italic(true).
		MarginTop(1).
		Render("Press ? to close")

	return lipgloss.Place(
		m.Width, m.Height,
		lipgloss.Center, lipgloss.Center,
		lipgloss.JoinVertical(lipgloss.Center, box, closeHint),
	)
}

// --- Helper Functions ---

func calculateDepth(node *TreeNode, rootPath string) int {
	rootDepth := strings.Count(rootPath, string(filepath.Separator))
	nodeDepth := strings.Count(node.FullPath, string(filepath.Separator))
	depth := nodeDepth - rootDepth
	if depth < 0 {
		return 0
	}
	return depth
}

func getFileIcon(node *TreeNode) string {
	if node.IsDir {
		if node.Expanded {
			return lipgloss.NewStyle().Foreground(colorYellow).Render(iconFolderOpen)
		}
		return lipgloss.NewStyle().Foreground(colorBlue).Render(iconFolder)
	}

	ext := strings.ToLower(filepath.Ext(node.Name))
	name := strings.ToLower(node.Name)

	// Special files
	switch name {
	case "dockerfile", ".dockerignore":
		return lipgloss.NewStyle().Foreground(colorBlue).Render(iconDocker)
	case ".gitignore", ".gitattributes":
		return lipgloss.NewStyle().Foreground(colorOrange).Render(iconGit)
	case "readme.md", "readme":
		return lipgloss.NewStyle().Foreground(colorGreen).Render(iconMarkdown)
	case "package.json", "tsconfig.json":
		return lipgloss.NewStyle().Foreground(colorYellow).Render(iconJSON)
	}

	// By extension
	iconStyle := lipgloss.NewStyle()
	var icon string

	switch ext {
	case ".go":
		icon = iconGo
		iconStyle = iconStyle.Foreground(colorCyan)
	case ".md", ".markdown":
		icon = iconMarkdown
		iconStyle = iconStyle.Foreground(colorGreen)
	case ".json":
		icon = iconJSON
		iconStyle = iconStyle.Foreground(colorYellow)
	case ".yaml", ".yml":
		icon = iconYAML
		iconStyle = iconStyle.Foreground(colorPurple)
	case ".js", ".jsx":
		icon = iconJS
		iconStyle = iconStyle.Foreground(colorYellow)
	case ".ts", ".tsx":
		icon = iconTS
		iconStyle = iconStyle.Foreground(colorBlue)
	case ".py":
		icon = iconPython
		iconStyle = iconStyle.Foreground(colorBlue)
	case ".rs":
		icon = iconRust
		iconStyle = iconStyle.Foreground(colorOrange)
	case ".html", ".htm":
		icon = iconHTML
		iconStyle = iconStyle.Foreground(colorOrange)
	case ".css", ".scss", ".sass":
		icon = iconCSS
		iconStyle = iconStyle.Foreground(colorBlue)
	case ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp":
		icon = iconImage
		iconStyle = iconStyle.Foreground(colorPurple)
	case ".zip", ".tar", ".gz", ".rar", ".7z":
		icon = iconArchive
		iconStyle = iconStyle.Foreground(colorRed)
	case ".toml", ".ini", ".conf", ".config":
		icon = iconConfig
		iconStyle = iconStyle.Foreground(colorGray)
	case ".txt", ".log":
		icon = iconText
		iconStyle = iconStyle.Foreground(colorGray)
	default:
		if isCodeFile(ext) {
			icon = iconCode
			iconStyle = iconStyle.Foreground(colorGrayLight)
		} else {
			icon = iconFile
			iconStyle = iconStyle.Foreground(colorGray)
		}
	}

	return iconStyle.Render(icon)
}

func isCodeFile(ext string) bool {
	codeExts := []string{
		".c", ".cpp", ".cc", ".h", ".hpp",
		".java", ".kt", ".scala",
		".rb", ".php", ".swift",
		".sh", ".bash", ".zsh",
		".vim", ".lua", ".r",
	}
	return slices.Contains(codeExts, ext)
}

func getSelectionIcon(node *TreeNode, space *core.DirectorySpace) (string, lipgloss.Style) {
	style := lipgloss.NewStyle()

	// 1. Exact match
	isExact := slices.Contains(space.Config.ManualSelections, node.FullPath)
	if isExact {
		return iconCheckSquare, style.Foreground(colorGreen).Bold(true)
	}

	// 2. Implicit/Ancestor match (this file/folder is under a selected parent)
	for _, s := range space.Config.ManualSelections {
		if strings.HasPrefix(node.FullPath, s+string(filepath.Separator)) {
			return iconDot, style.Foreground(colorGreen)
		}
	}

	// 3. Partial/Descendant match (some children are selected)
	if node.IsDir {
		prefix := node.FullPath + string(filepath.Separator)
		for _, s := range space.Config.ManualSelections {
			if strings.HasPrefix(s, prefix) {
				return iconCircle, style.Foreground(colorYellow)
			}
		}
	}

	return iconSquare, style.Foreground(colorGray)
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

func enhancedCheckbox(label string, checked bool, hotkey string) string {
	icon := iconSquare
	style := lipgloss.NewStyle().Foreground(colorGray)

	if checked {
		icon = iconCheckSquare
		style = lipgloss.NewStyle().Foreground(colorGreen).Bold(true)
	}

	labelWithKey := fmt.Sprintf("%s %s (%s)", icon, label, hotkey)
	return style.Render(labelWithKey)
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
			Name:     e.Name,
			FullPath: e.FullPath,
			IsDir:    e.IsDir,
			Parent:   targetNode,
		})
	}
	targetNode.Children = children
}

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
