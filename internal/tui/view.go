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
	// 1. Handle Overlays (Help / New Tab)
	if m.ShowNewTab {
		return m.renderNewTabView()
	} else if m.ShowHelp {
		return m.renderHelpView()
	}

	// 2. Main Application Layout
	space := m.Session.GetActiveSpace()
	var content string

	if space == nil {
		emptyMsg := lipgloss.NewStyle().
			Foreground(m.Styles.ColorSubtext).
			Render("No workspace open. Press ctrl+n to create a new tab.")

		content = lipgloss.Place(
			m.Width, m.Height,
			lipgloss.Center, lipgloss.Center,
			emptyMsg,
			lipgloss.WithWhitespaceBackground(m.Styles.ColorBase),
		)
	} else {
		state := m.TabStates[space.ID]

		// A. Render Header and Footer first to measure their height
		tabs := m.renderTabs()
		footer := m.renderFooter(space)

		headerHeight := lipgloss.Height(tabs)
		footerHeight := lipgloss.Height(footer)

		// B. Calculate exact remaining height for the middle section
		middleHeight := max(0, m.Height-headerHeight-footerHeight)

		// C. Render Middle Section with explicit height
		sidebar := m.renderSidebar(state, space, middleHeight)
		tree := m.renderTree(state, space, middleHeight)

		// Join sidebar and tree horizontally
		body := lipgloss.JoinHorizontal(lipgloss.Top, sidebar, tree)

		// Join everything vertically
		content = lipgloss.JoinVertical(lipgloss.Left, tabs, body, footer)
	}

	// 3. Final Canvas Composition
	return lipgloss.Place(
		m.Width, m.Height,
		lipgloss.Left, lipgloss.Top,
		content,
		lipgloss.WithWhitespaceBackground(m.Styles.ColorBase),
		lipgloss.WithWhitespaceChars(" "),
	)
}

func (m AppModel) renderTabs() string {
	var tabs []string

	branding := lipgloss.NewStyle().
		Foreground(m.Styles.ColorMauve).
		Background(m.Styles.ColorBase).
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

	helpTab := m.Styles.Tab.Render(iconKeyboard + " [Tab] Switch • [Ctrl+N] New • [Ctrl+W] Close")
	tabs = append(tabs, helpTab)

	tabBar := lipgloss.JoinHorizontal(lipgloss.Top, tabs...)

	return lipgloss.NewStyle().
		Width(m.Width).
		Background(m.Styles.ColorBase).
		Render(tabBar)
}

func (m AppModel) renderSidebar(state *TabState, space *core.DirectorySpace, height int) string {
	// Sidebar Header
	header := m.Styles.SectionHeader.Render(iconGear + " Configuration")

	// Inputs
	inputs := lipgloss.JoinVertical(lipgloss.Left,
		m.renderInput("Root", state.InputRoot, state.ActiveInput == 1, "r"),
		"",
		m.renderInput("Output", state.InputOutput, state.ActiveInput == 2, "o"),
		"",
		m.renderInput("Include", state.InputInclude, state.ActiveInput == 3, "f"),
		"",
		m.renderInput("Exclude", state.InputExclude, state.ActiveInput == 4, "g"),
	)

	// Options
	optionsHeader := m.Styles.SectionHeader.Render(iconFilter + " Options")
	options := lipgloss.JoinVertical(lipgloss.Left,
		m.renderCheckbox("Include Mode", space.Config.IncludeMode, "i"),
		m.renderCheckbox("Show Context", space.Config.ShowContext, "c"),
		m.renderCheckbox("Show Excluded", space.Config.ShowExcluded, "x"),
		m.renderCheckbox("Struct in View", space.Config.StructureView, "v"),
	)

	// Selection Count
	selectionCount := lipgloss.NewStyle().
		Foreground(m.Styles.ColorGreen).
		Bold(true).
		Background(m.Styles.ColorBase).
		Width(34).
		Render(fmt.Sprintf("%s Selected: %d", iconCheckSquare, len(space.Config.ManualSelections)))

	// Compose the content
	content := lipgloss.JoinVertical(lipgloss.Left,
		header,
		"",
		inputs,
		"",
		"",
		optionsHeader,
		options,
		"",
		"",
		selectionCount,
	)

	return m.Styles.Sidebar.
		Height(height).
		Background(m.Styles.ColorBase).
		Render(content)
}

// renderCheckbox replaces the external utility to ensure proper background styling
func (m AppModel) renderCheckbox(label string, checked bool, hotkey string) string {
	icon := iconSquare
	style := m.Styles.Option

	if checked {
		icon = iconCheckSquare
		style = m.Styles.OptionSelected
	}

	labelWithKey := fmt.Sprintf("%s %s (%s)", icon, label, hotkey)

	// Ensure the checkbox also consumes width to prevent background gaps,
	// similar to SectionHeader (34 width = 38 - 4 padding)
	return style.Width(34).Render(labelWithKey)
}

func (m AppModel) renderInput(label string, input textinput.Model, focused bool, hotkey string) string {
	labelWithKey := fmt.Sprintf("%s (%s):", label, hotkey)
	labelStyle := m.Styles.InputLabel.Render(labelWithKey)

	inputView := input.View()
	style := m.Styles.InputBox
	if focused {
		style = m.Styles.InputBoxFocused
	}

	renderedInput := style.Width(34).Render(inputView)

	return lipgloss.JoinVertical(
		lipgloss.Left,
		labelStyle,
		renderedInput,
	)
}

func (m AppModel) renderTree(state *TabState, space *core.DirectorySpace, height int) string {
	var treeRows []string

	availableRows := max(0, height-2)

	startRow := 0
	totalNodes := len(state.VisibleNodes)

	if totalNodes > availableRows {
		bottomThreshold := totalNodes - availableRows
		if state.CursorIndex <= availableRows/2 {
			startRow = 0
		} else if state.CursorIndex >= bottomThreshold+availableRows/2 {
			startRow = bottomThreshold
		} else {
			startRow = state.CursorIndex - availableRows/2
		}
	}

	endRow := min(startRow+availableRows, totalNodes)

	// Width Layout Logic
	// Sidebar Width: 38 (content) + 2L+2R (pad) + 1R (border) = 43
	// Tree Padding: 2L+2R = 4
	// Total Fixed Width to subtract = 43 + 4 = 47
	sidebarWidth := 47
	treeWidth := max(0, m.Width-sidebarWidth)
	contentWidth := max(0, treeWidth-4)

	for i := startRow; i < endRow; i++ {
		node := state.VisibleNodes[i]

		// 1. Determine Row Background Color
		var rowBgColor lipgloss.Color
		var isSelected bool

		if i == state.CursorIndex {
			rowBgColor = m.Styles.ColorSurface // Highlight Color
			isSelected = true
		} else {
			rowBgColor = m.Styles.ColorBase // Standard Background
			isSelected = false
		}

		// 2. Render Indentation (Canvas)
		depth := calculateDepth(node, space.RootPath)
		indent := strings.Repeat(treeSpace, depth)
		styledIndent := lipgloss.NewStyle().
			Background(rowBgColor).
			Render(indent)

		// 3. Render Checkbox (Canvas)
		checkChar, checkStyle := getSelectionIcon(node, space, m.Styles)
		styledCheck := checkStyle.
			Background(rowBgColor).
			Render(checkChar + " ") // Add space after check

		// 4. Render Icon (Canvas)
		// Now we get style + char separate, so we can inject the background
		var iconChar string
		var iconStyle lipgloss.Style

		if isSelected {
			// For selection, we stick to a simpler high-contrast icon style
			// or we can use the colored one but with the highlight background.
			// Let's use the colored one for better visuals, but ensure background matches.
			iconChar, iconStyle = getFileIcon(node, m.Styles)
		} else {
			iconChar, iconStyle = getFileIcon(node, m.Styles)
		}

		styledIcon := iconStyle.
			Background(rowBgColor).
			Render(iconChar + " ") // Add space after icon

		// 5. Render Name (Canvas)
		nameStyle := lipgloss.NewStyle().
			Foreground(m.Styles.ColorText).
			Background(rowBgColor)

		if isSelected {
			nameStyle = nameStyle.Foreground(m.Styles.ColorMauve).Bold(true)
		}

		styledName := nameStyle.Render(node.Name)

		// 6. Combine all parts into a solid line
		// Since every part has the correct background, joining them should look seamless
		leftContent := lipgloss.JoinHorizontal(lipgloss.Top,
			styledIndent,
			styledCheck,
			styledIcon,
			styledName,
		)

		// 7. Fill the remaining width to ensure the background extends to the edge
		// We use a "filler" style
		// Calculate length of visible chars (rough approximation or using lipgloss.Width)
		currentWidth := lipgloss.Width(leftContent)
		fillWidth := max(0, contentWidth-currentWidth)
		filler := lipgloss.NewStyle().
			Background(rowBgColor).
			Width(fillWidth).
			Render(" ")

		line := lipgloss.JoinHorizontal(lipgloss.Top, leftContent, filler)

		// 8. Add left/right padding if needed (part of tree container)
		// The container handles the margins, but we can wrap this in a padder if strictly necessary.
		// For now, we return the raw line which is a full "canvas" for this row.
		treeRows = append(treeRows, line)
	}

	mainContent := lipgloss.JoinVertical(lipgloss.Left, treeRows...)

	return m.Styles.Main.
		Width(treeWidth).
		Height(height).
		Background(m.Styles.ColorBase).
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

	return lipgloss.NewStyle().
		Width(m.Width).
		Background(m.Styles.ColorBase).
		Render(footer)
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

	title := lipgloss.NewStyle().
		Bold(true).
		Foreground(m.Styles.ColorMauve).
		Render(iconHelp + " Keyboard Shortcuts")

	boxWidth := min(m.Width-4, maxCols*itemWidth+4)

	box := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(m.Styles.ColorMauve).
		Background(m.Styles.ColorSurface).
		Padding(1, 2).
		Width(boxWidth).
		Render(lipgloss.JoinVertical(lipgloss.Left, title, "", helpBlock))

	closeHint := lipgloss.NewStyle().
		Foreground(m.Styles.ColorSubtext).
		Italic(true).
		Render("Press ? to close")

	content := lipgloss.JoinVertical(lipgloss.Center, box, "", closeHint)

	return lipgloss.Place(
		m.Width, m.Height,
		lipgloss.Center, lipgloss.Center,
		content,
		lipgloss.WithWhitespaceBackground(m.Styles.ColorBase),
		lipgloss.WithWhitespaceChars(" "),
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
		Background(m.Styles.ColorSurface).
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
		Background(m.Styles.ColorSurface).
		Padding(1, 2).
		Render(content)

	return lipgloss.Place(
		m.Width, m.Height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceBackground(m.Styles.ColorBase),
		lipgloss.WithWhitespaceChars(" "),
	)
}
