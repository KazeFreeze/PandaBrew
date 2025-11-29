// Package tui implements the terminal user interface logic.
package tui

import "github.com/charmbracelet/lipgloss"

// --- Nerd Font Icons ---
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
	iconPlusSquare  = "\uf0fe" // nf-fa-plus_square (Added)
	iconMinusSquare = "\uf146" // nf-fa-minus_square (Added)
	iconDot         = "\uf111" // nf-fa-circle (filled)
	iconCircle      = "\uf10c" // nf-fa-circle_o (outline)

	iconKeyboard = "\uf11c" // nf-fa-keyboard_o
	iconSave     = "\uf0c7" // nf-fa-save
	iconExport   = "\uf019" // nf-fa-download
	iconHelp     = "\uf059" // nf-fa-question_circle
	iconGear     = "\uf013" // nf-fa-cog
	iconFilter   = "\uf0b0" // nf-fa-filter

	treeSpace = "  "
)

// Styles holds all the lipgloss styles for the UI
type Styles struct {
	// Colors (Exposed for conditional rendering in utils)
	ColorBase     lipgloss.Color
	ColorSurface  lipgloss.Color
	ColorText     lipgloss.Color
	ColorSubtext  lipgloss.Color
	ColorMauve    lipgloss.Color
	ColorRed      lipgloss.Color
	ColorBlue     lipgloss.Color
	ColorGreen    lipgloss.Color
	ColorYellow   lipgloss.Color
	ColorPeach    lipgloss.Color
	ColorLavender lipgloss.Color

	// Components
	Tab             lipgloss.Style
	TabActive       lipgloss.Style
	Sidebar         lipgloss.Style
	SectionHeader   lipgloss.Style
	InputLabel      lipgloss.Style
	InputBox        lipgloss.Style
	InputBoxFocused lipgloss.Style
	Main            lipgloss.Style
	StatusLeft      lipgloss.Style
	StatusMiddle    lipgloss.Style
	StatusRight     lipgloss.Style
	TreeHighlight   lipgloss.Style
	TreeRow         lipgloss.Style
	Option          lipgloss.Style
	OptionSelected  lipgloss.Style
	HelpKey         lipgloss.Style
	HelpDesc        lipgloss.Style
}

// DefaultStyles generates the style sheet based on the provided palette
func DefaultStyles(p ThemePalette) Styles {
	s := Styles{
		ColorBase:     p.Base,
		ColorSurface:  p.Surface,
		ColorText:     p.Text,
		ColorSubtext:  p.Subtext,
		ColorMauve:    p.Mauve,
		ColorRed:      p.Red,
		ColorBlue:     p.Blue,
		ColorGreen:    p.Green,
		ColorYellow:   p.Yellow,
		ColorPeach:    p.Peach,
		ColorLavender: p.Lavender,
	}

	// Tab Styles - explicitly set background to match theme
	s.Tab = lipgloss.NewStyle().
		Padding(0, 2).
		Foreground(p.Overlay).
		Background(p.Surface)

	s.TabActive = lipgloss.NewStyle().
		Padding(0, 2).
		Foreground(p.Base).
		Background(p.Mauve).
		Bold(true)

	// Sidebar Styles
	// Important: Background is Base to blend with global background
	// Width(38) + Padding(4) + Border(1) = 43 Total Width
	s.Sidebar = lipgloss.NewStyle().
		Width(38).
		Padding(1, 2).
		Background(p.Base).
		Border(lipgloss.RoundedBorder(), false, true, false, false).
		BorderForeground(p.Mauve).
		BorderBackground(p.Base)

	s.SectionHeader = lipgloss.NewStyle().
		Foreground(p.Mauve).
		Background(p.Base).
		Bold(true).
		Underline(true).
		Width(34). // Fix: Force width to match Sidebar content area (38 - 4 padding)
		MarginBottom(1)

	s.InputLabel = lipgloss.NewStyle().
		Foreground(p.Blue).
		Background(p.Base).
		Bold(true).
		Width(34)

	s.InputBox = lipgloss.NewStyle().
		Background(p.Base)

	s.InputBoxFocused = lipgloss.NewStyle().
		Foreground(p.Mauve).
		Background(p.Base)

	// Main Content Area
	// Removed MarginLeft(1) to allow background color to propagate from the sidebar.
	// Padding(1, 2) provides the visual separation while maintaining the background.
	s.Main = lipgloss.NewStyle().
		Padding(1, 2).
		Background(p.Base)

	// Status Bar Styles
	s.StatusLeft = lipgloss.NewStyle().
		Foreground(p.Base).
		Background(p.Mauve).
		Padding(0, 2).
		Bold(true)

	s.StatusMiddle = lipgloss.NewStyle().
		Foreground(p.Base).
		Background(p.Blue).
		Padding(0, 2)

	s.StatusRight = lipgloss.NewStyle().
		Foreground(p.Text).
		Background(p.Surface).
		Padding(0, 2)

	// Tree Highlight (Full Row) - uses Surface for contrast against Base
	// We ensure the highlight also has a background set to avoid gaps
	s.TreeHighlight = lipgloss.NewStyle().
		Background(p.Surface).
		Foreground(p.Mauve).
		Bold(true)

	// Tree Row (Standard) - uses Base background to fill gaps in file names
	s.TreeRow = lipgloss.NewStyle().
		Background(p.Base).
		Foreground(p.Text) // Explicitly set foreground to prevent partial resets

	// Option Styles (Checkboxes)
	s.Option = lipgloss.NewStyle().
		Foreground(p.Subtext).
		Background(p.Base)

	s.OptionSelected = lipgloss.NewStyle().
		Foreground(p.Green).
		Background(p.Base).
		Bold(true)

	// Help Styles - ensure they work on base background
	s.HelpKey = lipgloss.NewStyle().
		Foreground(p.Mauve).
		Background(p.Base).
		Bold(true)

	s.HelpDesc = lipgloss.NewStyle().
		Foreground(p.Text).
		Background(p.Base)

	return s
}
