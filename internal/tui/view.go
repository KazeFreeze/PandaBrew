// Package tui implements the terminal user interface logic.
package tui

import (
	"fmt"
	"path/filepath"
	"strings"

	"pandabrew/internal/core"

	"github.com/charmbracelet/bubbles/key"
	"github.com/charmbracelet/bubbles/textinput"
	"github.com/charmbracelet/lipgloss"
)

// View renders the UI.
func (m AppModel) View() string {
	var content string

	// 1. Determine which view to render
	if m.ShowNewTab {
		content = m.renderNewTabView()
	} else if m.ShowHelp {
		content = m.renderHelpView()
	} else {
		space := m.Session.GetActiveSpace()
		if space == nil {
			content = lipgloss.Place(
				m.Width, m.Height,
				lipgloss.Center, lipgloss.Center,
				"No workspace open. Press ctrl+n to create a new tab.",
			)
		} else {
			state := m.TabStates[space.ID]

			tabs := m.renderTabs()
			sidebar := m.renderSidebar(state, space)
			tree := m.renderTree(state, space)
			footer := m.renderFooter(space)

			body := lipgloss.JoinHorizontal(lipgloss.Top, sidebar, tree)
			content = lipgloss.JoinVertical(lipgloss.Left, tabs, body, footer)
		}
	}

	// 2. Wrap the entire view in the global theme background
	// This ensures we don't bleed the terminal's default background
	return lipgloss.NewStyle().
		Background(m.Styles.ColorBase).
		Foreground(m.Styles.ColorText).
		Width(m.Width).
		Height(m.Height).
		Render(content)
}

func (m AppModel) renderTabs() string {
	var tabs []string

	branding := lipgloss.NewStyle().
		Foreground(m.Styles.ColorMauve).
		Bold(true).
		Padding(0, 2).
		Render("ʕ•ᴥ•ʔっ☕ PandaBrew")
	tabs = append(tabs, branding)

	for _, s := range m.Session.Spaces {
		name := iconFolder + " " + filepath.Base(s.RootPath)
		style := m.Styles.Tab
		if s.ID == m.Session.ActiveSpaceID {
			style = m.Styles.TabActive
		}
		tabs = append(tabs, style.Render(name))
	}
	tabs = append(tabs, m.Styles.Tab.Render(iconKeyboard+" [Tab] Switch • [Ctrl+N] New • [Ctrl+W] Close"))
	return lipgloss.JoinHorizontal(lipgloss.Top, tabs...)
}

func (m AppModel) renderSidebar(state *TabState, space *core.DirectorySpace) string {
	settings := lipgloss.JoinVertical(lipgloss.Left,
		m.Styles.SectionHeader.Render(iconGear+" Configuration"),
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
		m.Styles.SectionHeader.Render(iconFilter+" Options"),
		enhancedCheckbox("Include Mode", space.Config.IncludeMode, "i", m.Styles),
		enhancedCheckbox("Show Context", space.Config.ShowContext, "c", m.Styles),
		enhancedCheckbox("Show Excluded", space.Config.ShowExcluded, "x", m.Styles),
		enhancedCheckbox("Struct in View", space.Config.StructureView, "v", m.Styles),
		"",
		"",
		lipgloss.NewStyle().
			Foreground(m.Styles.ColorGreen).
			Bold(true).
			Render(fmt.Sprintf("%s Selected: %d", iconCheckSquare, len(space.Config.ManualSelections))),
	)

	return m.Styles.Sidebar.Height(m.Height - 7).Render(settings)
}

func (m AppModel) renderInput(label string, input textinput.Model, focused bool, hotkey string) string {
	labelWithKey := fmt.Sprintf("%s (%s):", label, hotkey)
	labelStyle := m.Styles.InputLabel.Render(labelWithKey)

	inputView := input.View()
	if focused {
		inputView = m.Styles.InputBoxFocused.Render(inputView)
	} else {
		inputView = m.Styles.InputBox.Render(inputView)
	}

	return lipgloss.JoinVertical(
		lipgloss.Left,
		labelStyle,
		inputView,
	)
}

func (m AppModel) renderTree(state *TabState, space *core.DirectorySpace) string {
	var treeRows []string

	maxRows := m.Height - 8
	startRow := 0

	totalNodes := len(state.VisibleNodes)
	if totalNodes > maxRows {
		bottomThreshold := totalNodes - maxRows
		if state.CursorIndex <= maxRows/2 {
			startRow = 0
		} else if state.CursorIndex >= bottomThreshold+maxRows/2 {
			startRow = bottomThreshold
		} else {
			startRow = state.CursorIndex - maxRows/2
		}
	}

	endRow := min(startRow+maxRows, totalNodes)

	treeWidth := m.Width - 45 - 4
	highlightStyle := m.Styles.TreeHighlight.Width(treeWidth)

	for i := startRow; i < endRow; i++ {
		node := state.VisibleNodes[i]

		depth := calculateDepth(node, space.RootPath)
		indent := strings.Repeat(treeSpace, depth)

		var line string
		if i == state.CursorIndex {
			icon := getRawFileIcon(node)
			checkIcon, _ := getSelectionIcon(node, space, m.Styles)

			lineContent := fmt.Sprintf("%s%s %s %s", indent, checkIcon, icon, node.Name)
			cursorSymbol := "▶ "
			fullLine := cursorSymbol + lineContent

			line = highlightStyle.Render(fullLine)
		} else {
			icon := getFileIcon(node, m.Styles)
			checkIcon, checkStyle := getSelectionIcon(node, space, m.Styles)

			lineContent := fmt.Sprintf("%s%s %s %s", indent, checkIcon, icon, node.Name)
			styledContent := checkStyle.Render(lineContent)
			line = "  " + styledContent
		}

		treeRows = append(treeRows, line)
	}

	mainContent := lipgloss.JoinVertical(lipgloss.Left, treeRows...)
	return m.Styles.Main.
		Width(m.Width - 45).
		Height(m.Height - 7).
		Render(mainContent)
}

func (m AppModel) renderFooter(space *core.DirectorySpace) string {
	var sections []string

	var leftSection string
	if m.Loading && m.ExportTotal > 0 {
		progressBar := m.Progress.ViewAs(m.ExportProgress)
		leftSection = fmt.Sprintf("Exporting: %d/%d %s", m.ExportProcessed, m.ExportTotal, progressBar)
	} else if m.Loading {
		leftSection = fmt.Sprintf("%s %s", m.Spinner.View(), m.StatusMessage)
	} else {
		leftSection = m.StatusMessage
	}
	sections = append(sections, m.Styles.StatusLeft.Render(leftSection))

	middleSection := fmt.Sprintf("%s %d selected", iconCheckSquare, len(space.Config.ManualSelections))
	sections = append(sections, m.Styles.StatusMiddle.Render(middleSection))

	rightSection := fmt.Sprintf("%s help • %s save • %s export • %s theme • q quit",
		iconHelp, iconSave, iconExport, iconGear)
	sections = append(sections, m.Styles.StatusRight.Render(rightSection))

	footer := lipgloss.JoinHorizontal(lipgloss.Top, sections...)
	return lipgloss.NewStyle().Width(m.Width).Render(footer)
}

func (m AppModel) renderHelpView() string {
	groups := m.keys.FullHelp()

	const itemWidth = 38
	maxCols := max(1, (m.Width-10)/itemWidth)

	var allBindings []key.Binding
	for _, group := range groups {
		allBindings = append(allBindings, group...)
	}

	var rows []string
	var rowItems []string

	for _, binding := range allBindings {
		keyText := binding.Help().Key
		keyStyled := lipgloss.NewStyle().
			Foreground(m.Styles.ColorMauve).
			Bold(true).
			Width(14).
			Render(keyText)

		descText := binding.Help().Desc
		descStyled := lipgloss.NewStyle().
			Foreground(m.Styles.ColorText).
			Width(22).
			Render(descText)

		item := lipgloss.NewStyle().
			Width(itemWidth).
			Render(fmt.Sprintf("%s %s", keyStyled, descStyled))

		rowItems = append(rowItems, item)

		if len(rowItems) >= maxCols {
			rows = append(rows, lipgloss.JoinHorizontal(lipgloss.Top, rowItems...))
			rowItems = nil
		}
	}

	if len(rowItems) > 0 {
		rows = append(rows, lipgloss.JoinHorizontal(lipgloss.Top, rowItems...))
	}

	helpBlock := lipgloss.JoinVertical(lipgloss.Left, rows...)

	title := lipgloss.NewStyle().Bold(true).Foreground(m.Styles.ColorMauve).Render(iconHelp + " Keyboard Shortcuts")

	boxWidth := min(m.Width-4, maxCols*itemWidth+4)

	box := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(m.Styles.ColorMauve).
		Padding(1, 2).
		Width(boxWidth).
		Render(lipgloss.JoinVertical(lipgloss.Left, title, "", helpBlock))

	closeHint := lipgloss.NewStyle().Foreground(m.Styles.ColorSubtext).Italic(true).Render("Press ? to close")

	return lipgloss.Place(
		m.Width, m.Height,
		lipgloss.Center, lipgloss.Center,
		lipgloss.JoinVertical(lipgloss.Center, box, "", closeHint),
	)
}

func (m AppModel) renderNewTabView() string {
	title := lipgloss.NewStyle().
		Bold(true).
		Foreground(m.Styles.ColorMauve).
		Render(iconFolder + " Open New Tab")

	description := lipgloss.NewStyle().
		Foreground(m.Styles.ColorSubtext).
		Render("Enter the full path to a directory:")

	inputBox := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(m.Styles.ColorMauve).
		Padding(0, 1).
		Width(min(m.Width-10, 70)).
		Render(m.NewTabInput.View())

	hints := lipgloss.NewStyle().
		Foreground(m.Styles.ColorSubtext).
		Italic(true).
		Render("Enter to confirm • Esc to cancel")

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		"",
		description,
		"",
		inputBox,
		"",
		hints,
	)

	box := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(m.Styles.ColorMauve).
		Padding(1, 2).
		Render(content)

	return lipgloss.Place(
		m.Width, m.Height,
		lipgloss.Center, lipgloss.Center,
		box,
	)
}
