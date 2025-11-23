package tui

import (
	"fmt"
	"path/filepath"
	"strings"

	"pandabrew/internal/core"

	"github.com/charmbracelet/bubbles/textinput"
	"github.com/charmbracelet/lipgloss"
)

// View renders the UI.
func (m AppModel) View() string {
	// Show new tab overlay
	if m.ShowNewTab {
		return m.renderNewTabView()
	}

	// Show help overlay
	if m.ShowHelp {
		return m.renderHelpView()
	}

	space := m.Session.GetActiveSpace()
	if space == nil {
		return "No workspace open. Press ctrl+n to create a new tab."
	}
	state := m.TabStates[space.ID]

	// 1. Tabs
	tabs := m.renderTabs()

	// 2. Sidebar
	sidebar := m.renderSidebar(state, space)

	// 3. File Tree
	tree := m.renderTree(state, space)

	// 4. Footer
	footer := m.renderFooter(space)

	// Combine
	body := lipgloss.JoinHorizontal(lipgloss.Top, sidebar, tree)
	main := lipgloss.JoinVertical(lipgloss.Left, tabs, body, footer)

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
	tabs = append(tabs, styleTab.Render(iconKeyboard+" [Tab] Switch • [Ctrl+N] New"))
	return lipgloss.JoinHorizontal(lipgloss.Top, tabs...)
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
	labelWithKey := fmt.Sprintf("%s (%s):", label, hotkey)
	labelStyle := styleInputLabel.Render(labelWithKey)

	inputView := input.View()
	if focused {
		inputView = styleInputBoxFocused.Render(inputView)
	} else {
		inputView = styleInputBox.Render(inputView)
	}

	return lipgloss.JoinVertical(
		lipgloss.Left,
		labelStyle,
		inputView,
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

	// Left: Status message with spinner or progress bar
	var leftSection string
	if m.Loading && m.ExportTotal > 0 {
		// Show progress bar during export
		progressBar := m.Progress.ViewAs(m.ExportProgress)
		leftSection = fmt.Sprintf("Exporting: %d/%d %s", m.ExportProcessed, m.ExportTotal, progressBar)
	} else if m.Loading {
		leftSection = fmt.Sprintf("%s %s", m.Spinner.View(), m.StatusMessage)
	} else {
		leftSection = m.StatusMessage
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
	// The key change: pass the keymap to the help View method
	helpView := m.Help.FullHelpView(m.keys.FullHelp())

	title := lipgloss.NewStyle().
		Bold(true).
		Foreground(colorPurple).
		Padding(1, 0).
		Render(iconHelp + " Keyboard Shortcuts")

	description := lipgloss.NewStyle().
		Foreground(colorGray).
		Padding(0, 0, 1, 0).
		Render("Navigation & Selection")

	box := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(colorPurple).
		Padding(2, 3).
		Width(min(m.Width-4, 100)).
		Render(lipgloss.JoinVertical(lipgloss.Left, title, description, helpView))

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

func (m AppModel) renderNewTabView() string {
	title := lipgloss.NewStyle().
		Bold(true).
		Foreground(colorPurple).
		Padding(1, 0).
		Render(iconFolder + " Open New Tab")

	description := lipgloss.NewStyle().
		Foreground(colorGray).
		Padding(0, 0, 1, 0).
		Render("Enter the full path to a directory:")

	inputBox := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(colorPurple).
		Padding(1, 2).
		Width(min(m.Width-10, 70)).
		Render(m.NewTabInput.View())

	hints := lipgloss.NewStyle().
		Foreground(colorGray).
		Italic(true).
		MarginTop(1).
		Render("Enter to confirm • Esc to cancel")

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		description,
		"",
		inputBox,
		"",
		hints,
	)

	box := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(colorPurple).
		Padding(2, 3).
		Render(content)

	return lipgloss.Place(
		m.Width, m.Height,
		lipgloss.Center, lipgloss.Center,
		box,
	)
}
