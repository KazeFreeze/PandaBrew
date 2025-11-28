// Package tui implements the terminal user interface logic.
package tui

import (
	"path/filepath"
	"strings"

	"pandabrew/internal/core"

	"github.com/charmbracelet/bubbles/help"
	"github.com/charmbracelet/bubbles/progress"
	"github.com/charmbracelet/bubbles/spinner"
	"github.com/charmbracelet/bubbles/textinput"
	"github.com/charmbracelet/bubbles/viewport"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// --- Model ---

// AppModel is the single source of truth for the UI state.
type AppModel struct {
	Session         *core.Session
	TabStates       map[string]*TabState
	Spinner         spinner.Model
	Progress        progress.Model
	Help            help.Model
	Viewport        viewport.Model
	Loading         bool
	ShowHelp        bool
	ShowNewTab      bool
	NewTabInput     textinput.Model
	StatusMessage   string
	Width, Height   int
	keys            keyMap
	ExportProgress  float64
	ExportTotal     int
	ExportProcessed int
	Styles          Styles // Added: Store global styles
}

// TabState holds the UI state for a specific directory space (tab).
type TabState struct {
	TreeRoot     *TreeNode
	VisibleNodes []*TreeNode
	CursorIndex  int

	// State Restoration Targets
	TargetExpandedPaths map[string]bool
	TargetCursorPath    string

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
	if session.Theme == "" {
		session.Theme = "mocha"
	}

	palette := GetTheme(session.Theme)
	styles := DefaultStyles(palette)

	s := spinner.New()
	s.Spinner = spinner.Dot
	s.Style = lipgloss.NewStyle().Foreground(styles.ColorMauve)

	prog := progress.New(
		progress.WithDefaultGradient(),
		progress.WithWidth(40),
	)

	newTabInput := textinput.New()
	newTabInput.Placeholder = "Enter directory path..."
	newTabInput.CharLimit = 200
	newTabInput.Width = 60
	// Fix: Set background colors on the NewTabInput
	newTabInput.TextStyle = lipgloss.NewStyle().Background(styles.ColorSurface)
	newTabInput.PlaceholderStyle = lipgloss.NewStyle().
		Foreground(styles.ColorSubtext).
		Background(styles.ColorSurface)
	// CRITICAL FIX: Set cursor TextStyle background to match input background
	newTabInput.Cursor.Style = lipgloss.NewStyle().Foreground(styles.ColorMauve)
	newTabInput.Cursor.TextStyle = lipgloss.NewStyle().Background(styles.ColorSurface)

	h := help.New()
	h.Styles.FullKey = styles.HelpKey
	h.Styles.ShortKey = styles.HelpKey
	h.Styles.FullDesc = styles.HelpDesc
	h.Styles.ShortDesc = styles.HelpDesc

	model := AppModel{
		Session:     session,
		TabStates:   make(map[string]*TabState),
		Spinner:     s,
		Progress:    prog,
		Help:        h,
		NewTabInput: newTabInput,
		keys:        keys,
		Styles:      styles,
	}

	// Initialize tab states with styles
	for _, space := range session.Spaces {
		model.TabStates[space.ID] = newTabState(space, styles)
	}

	return model
}

// Updated to accept styles parameter
func newTabState(space *core.DirectorySpace, styles Styles) *TabState {
	newInput := func(placeholder, value string) textinput.Model {
		t := textinput.New()
		t.Placeholder = placeholder
		t.SetValue(value)
		t.CharLimit = 150
		t.Width = 34 // Match the container width
		// Fix: Set background colors for all inputs
		t.TextStyle = lipgloss.NewStyle().Background(styles.ColorBase)
		t.PlaceholderStyle = lipgloss.NewStyle().
			Foreground(styles.ColorSubtext).
			Background(styles.ColorBase)
		// CRITICAL FIX: Set cursor TextStyle background to match input background
		t.Cursor.Style = lipgloss.NewStyle().Foreground(styles.ColorMauve)
		t.Cursor.TextStyle = lipgloss.NewStyle().Background(styles.ColorBase)
		return t
	}

	ts := &TabState{
		InputRoot:           newInput("Root Directory", space.RootPath),
		InputOutput:         newInput("Output File", space.OutputFilePath),
		InputInclude:        newInput("*.go, src/", strings.Join(space.Config.IncludePatterns, ", ")),
		InputExclude:        newInput(".git, node_modules", strings.Join(space.Config.ExcludePatterns, ", ")),
		CursorIndex:         0,
		TargetExpandedPaths: make(map[string]bool),
		TargetCursorPath:    space.CursorPath,
	}

	for _, p := range space.ExpandedPaths {
		ts.TargetExpandedPaths[p] = true
	}

	ts.TreeRoot = &TreeNode{
		Name:     filepath.Base(space.RootPath),
		FullPath: space.RootPath,
		IsDir:    true,
		Expanded: true,
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

func (ts *TabState) rebuildVisibleList() {
	ts.VisibleNodes = make([]*TreeNode, 0)
	var walk func(*TreeNode)
	walk = func(n *TreeNode) {
		ts.VisibleNodes = append(ts.VisibleNodes, n)
		if n.Expanded {
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
