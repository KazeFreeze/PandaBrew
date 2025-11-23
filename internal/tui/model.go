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

	newTabInput := textinput.New()
	newTabInput.Placeholder = "Enter directory path..."
	newTabInput.CharLimit = 200
	newTabInput.Width = 60

	h := help.New()

	// Style for the Keys (e.g., "q", "ctrl+c") -> Purple & Bold
	h.Styles.FullKey = lipgloss.NewStyle().Foreground(colorPurple).Bold(true)
	h.Styles.ShortKey = lipgloss.NewStyle().Foreground(colorPurple).Bold(true)

	// Style for the Descriptions (e.g., "quit app") -> White/Plain
	h.Styles.FullDesc = lipgloss.NewStyle().Foreground(colorLight)
	h.Styles.ShortDesc = lipgloss.NewStyle().Foreground(colorLight)
	// -------------------------------------

	model := AppModel{
		Session:     session,
		TabStates:   make(map[string]*TabState),
		Spinner:     s,
		Progress:    prog,
		Help:        h,
		NewTabInput: newTabInput,
		keys:        keys,
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
