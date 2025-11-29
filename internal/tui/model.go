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
	Session    *core.Session
	TabStates  map[string]*TabState
	Spinner    spinner.Model
	Progress   progress.Model
	Help       help.Model
	Viewport   viewport.Model
	Loading    bool
	ShowHelp   bool
	ShowNewTab bool

	// Global Search State
	ShowGlobalSearch     bool
	GlobalSearchInput    textinput.Model
	GlobalSearchCache    map[string][]string // Cache files per root path
	GlobalSearchFiles    []string            // Currently filtered files
	GlobalSearchSelect   int                 // Selected index in the filtered list
	GlobalSearchSelected map[string]bool     // Multi-select state (path -> isSelected)

	NewTabInput     textinput.Model
	StatusMessage   string
	Width, Height   int
	keys            keyMap
	ExportProgress  float64
	ExportTotal     int
	ExportProcessed int
	Styles          Styles
}

// TabState holds the UI state for a specific directory space (tab).
type TabState struct {
	TreeRoot     *TreeNode
	VisibleNodes []*TreeNode
	CursorIndex  int

	// Search State
	InputSearch  textinput.Model
	SearchQuery  string
	MatchIndices []int
	MatchPtr     int

	// State Restoration Targets
	TargetExpandedPaths map[string]bool
	TargetCursorPath    string

	// Inputs
	InputRoot    textinput.Model
	InputOutput  textinput.Model
	InputInclude textinput.Model
	InputExclude textinput.Model

	ActiveInput int
}

// TreeNode represents the VISUAL state of a file.
type TreeNode struct {
	Name     string
	FullPath string
	IsDir    bool
	Expanded bool
	Children []*TreeNode
	Parent   *TreeNode
	IsLast   bool
}

// --- Init ---

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
	newTabInput.TextStyle = lipgloss.NewStyle().Background(styles.ColorBase)
	newTabInput.PlaceholderStyle = lipgloss.NewStyle().
		Foreground(styles.ColorSubtext).
		Background(styles.ColorBase)
	newTabInput.Cursor.Style = lipgloss.NewStyle().Foreground(styles.ColorMauve)
	newTabInput.Cursor.TextStyle = lipgloss.NewStyle().Background(styles.ColorBase)

	// Global Search Input
	globalSearchInput := textinput.New()
	globalSearchInput.Placeholder = "Type to search files..."
	globalSearchInput.CharLimit = 100
	globalSearchInput.Width = 60
	globalSearchInput.TextStyle = lipgloss.NewStyle().Background(styles.ColorBase)
	globalSearchInput.PlaceholderStyle = lipgloss.NewStyle().
		Foreground(styles.ColorSubtext).
		Background(styles.ColorBase)
	globalSearchInput.Cursor.Style = lipgloss.NewStyle().Foreground(styles.ColorMauve)
	globalSearchInput.Cursor.TextStyle = lipgloss.NewStyle().Background(styles.ColorBase)

	h := help.New()
	h.Styles.FullKey = styles.HelpKey
	h.Styles.ShortKey = styles.HelpKey
	h.Styles.FullDesc = styles.HelpDesc
	h.Styles.ShortDesc = styles.HelpDesc

	model := AppModel{
		Session:              session,
		TabStates:            make(map[string]*TabState),
		Spinner:              s,
		Progress:             prog,
		Help:                 h,
		NewTabInput:          newTabInput,
		GlobalSearchInput:    globalSearchInput,
		GlobalSearchCache:    make(map[string][]string),
		GlobalSearchSelected: make(map[string]bool),
		keys:                 keys,
		Styles:               styles,
	}

	for _, space := range session.Spaces {
		model.TabStates[space.ID] = newTabState(space, styles)
	}

	return model
}

func newTabState(space *core.DirectorySpace, styles Styles) *TabState {
	newInput := func(placeholder, value string) textinput.Model {
		t := textinput.New()
		t.Placeholder = placeholder
		t.SetValue(value)
		t.CharLimit = 150
		t.Width = 34
		t.TextStyle = lipgloss.NewStyle().Background(styles.ColorBase)
		t.PlaceholderStyle = lipgloss.NewStyle().
			Foreground(styles.ColorSubtext).
			Background(styles.ColorBase)
		t.Cursor.Style = lipgloss.NewStyle().Foreground(styles.ColorMauve)
		t.Cursor.TextStyle = lipgloss.NewStyle().Background(styles.ColorBase)
		return t
	}

	searchInput := textinput.New()
	searchInput.Placeholder = "Search..."
	searchInput.CharLimit = 50
	searchInput.Width = 20
	searchInput.TextStyle = lipgloss.NewStyle().Background(styles.ColorBase)
	searchInput.PlaceholderStyle = lipgloss.NewStyle().Foreground(styles.ColorSubtext).Background(styles.ColorBase)
	searchInput.Cursor.Style = lipgloss.NewStyle().Foreground(styles.ColorMauve)
	searchInput.Cursor.TextStyle = lipgloss.NewStyle().Background(styles.ColorBase)

	ts := &TabState{
		InputRoot:           newInput("Root Directory", space.RootPath),
		InputOutput:         newInput("Output File", space.OutputFilePath),
		InputInclude:        newInput("*.go, src/", strings.Join(space.Config.IncludePatterns, ", ")),
		InputExclude:        newInput(".git, node_modules", strings.Join(space.Config.ExcludePatterns, ", ")),
		InputSearch:         searchInput,
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

	if ts.SearchQuery != "" {
		ts.PerformSearch()
	}
}

func (ts *TabState) PerformSearch() {
	ts.MatchIndices = []int{}
	if ts.SearchQuery == "" {
		return
	}

	query := strings.ToLower(ts.SearchQuery)
	for i, node := range ts.VisibleNodes {
		if strings.Contains(strings.ToLower(node.Name), query) {
			ts.MatchIndices = append(ts.MatchIndices, i)
		}
	}

	if ts.MatchPtr >= len(ts.MatchIndices) {
		ts.MatchPtr = 0
	}
}
