// Package tui implements the terminal user interface using Bubble Tea.
package tui

import "github.com/charmbracelet/lipgloss"

// --- Nerd Font Icons ---
// Browse https://www.nerdfonts.com/cheat-sheet for more icons
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
			Width(34) // Adjusted to sidebar width

	// Slim Input Box (No Border)
	styleInputBox = lipgloss.NewStyle()

	// Slim Focused Input Box (Text Color Change only)
	styleInputBoxFocused = lipgloss.NewStyle().
				Foreground(colorPurple)

	// Main Content Styles
	styleMain = lipgloss.NewStyle().
			Padding(1, 2).
			MarginLeft(1)

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
)
