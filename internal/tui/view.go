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
	// 1. Handle Overlays (Help / New Tab / Global Search)
	if m.ShowNewTab {
		return m.renderNewTabView()
	} else if m.ShowGlobalSearch {
		return m.renderGlobalSearchView()
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
		footer := m.renderFooter(space, state)

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

	helpTab := lipgloss.NewStyle().
		Foreground(m.Styles.ColorSubtext).
		Background(m.Styles.ColorBase).
		Padding(0, 2).
		Render(iconKeyboard + " ? Help • Tab Switch • ^N New • ^W Close")

	tabs = append(tabs, helpTab)

	// Join all tabs
	tabBar := lipgloss.JoinHorizontal(lipgloss.Top, tabs...)

	// Wrap in a style that forces full width and adds background
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

	renderedInput := style.Width(35).Render(inputView)

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

	sidebarWidth := 39
	treeWidth := max(0, m.Width-sidebarWidth)

	contentWidth := treeWidth

	for i := startRow; i < endRow; i++ {
		node := state.VisibleNodes[i]

		// 1. Determine Row Background Color
		var rowBgColor lipgloss.Color
		var isSelected bool

		if i == state.CursorIndex {
			rowBgColor = m.Styles.ColorSurface
			isSelected = true
		} else {
			rowBgColor = m.Styles.ColorBase
			isSelected = false
		}

		// 2. Manual Padding (Left) - This replaces container padding
		leftPad := lipgloss.NewStyle().
			Background(rowBgColor).
			Render("  ")

		// 3. Render Indentation
		depth := calculateDepth(node, space.RootPath)
		indent := strings.Repeat(treeSpace, depth)
		styledIndent := lipgloss.NewStyle().
			Background(rowBgColor).
			Render(indent)

		// 4. Render Checkbox
		checkChar, checkStyle := getSelectionIcon(node, space, m.Styles)
		styledCheck := checkStyle.
			Background(rowBgColor).
			Render(checkChar + " ")

		// 5. Render Icon
		var iconChar string
		var iconStyle lipgloss.Style

		if isSelected {
			iconChar, iconStyle = getFileIcon(node, m.Styles)
		} else {
			iconChar, iconStyle = getFileIcon(node, m.Styles)
		}

		styledIcon := iconStyle.
			Background(rowBgColor).
			Render(iconChar + " ")

		// 6. Render Name with Substring Highlighting
		nameStyle := lipgloss.NewStyle().
			Foreground(m.Styles.ColorText).
			Background(rowBgColor)

		if isSelected {
			nameStyle = nameStyle.Foreground(m.Styles.ColorMauve).Bold(true)
		}

		var styledName string
		var matchCounter string

		// If there is an active search, perform substring matching and highlighting
		if state.SearchQuery != "" {
			// Perform case-insensitive search
			lowerName := strings.ToLower(node.Name)
			lowerQuery := strings.ToLower(state.SearchQuery)
			idx := strings.Index(lowerName, lowerQuery)

			if idx >= 0 {
				// Define highlight style: Yellow background + Base text (high contrast)
				highlightStyle := nameStyle.
					Background(m.Styles.ColorYellow).
					Foreground(m.Styles.ColorBase).
					Bold(true)

				// Calculate indices for slicing the ORIGINAL string
				start := idx
				end := idx + len(lowerQuery)

				// Safety check for bounds using min
				end = min(end, len(node.Name))

				prefix := node.Name[:start]
				match := node.Name[start:end]
				suffix := node.Name[end:]

				// Render the three parts individually
				styledName = nameStyle.Render(prefix) + highlightStyle.Render(match) + nameStyle.Render(suffix)

				// Calculate Match Counter (n/Total)
				for mIdx, matchedNodeIdx := range state.MatchIndices {
					if matchedNodeIdx == i {
						// Found the current node in the match list
						matchCounter = fmt.Sprintf(" (%d/%d)", mIdx+1, len(state.MatchIndices))
						break
					}
				}

			} else {
				styledName = nameStyle.Render(node.Name)
			}
		} else {
			styledName = nameStyle.Render(node.Name)
		}

		// 7. Render Match Counter if it exists
		var styledMatchCounter string
		if matchCounter != "" {
			styledMatchCounter = lipgloss.NewStyle().
				Foreground(m.Styles.ColorPeach). // Changed from Subtext to Peach
				Background(rowBgColor).
				Render(matchCounter)
		}

		// 8. Combine all parts
		leftContent := lipgloss.JoinHorizontal(lipgloss.Top,
			leftPad,
			styledIndent,
			styledCheck,
			styledIcon,
			styledName,
			styledMatchCounter, // Added counter here
		)

		// 9. Fill the remaining width
		currentWidth := lipgloss.Width(leftContent)
		fillWidth := max(0, contentWidth-currentWidth)

		filler := lipgloss.NewStyle().
			Background(rowBgColor).
			Width(fillWidth).
			Render(" ")

		line := lipgloss.JoinHorizontal(lipgloss.Top, leftContent, filler)
		treeRows = append(treeRows, line)
	}

	mainContent := lipgloss.JoinVertical(lipgloss.Left, treeRows...)

	return m.Styles.Main.
		Width(treeWidth).
		Height(height).
		Padding(1, 0).
		Background(m.Styles.ColorBase).
		Render(mainContent)
}

func (m AppModel) renderFooter(space *core.DirectorySpace, state *TabState) string {
	// If Search is Active (Input Focused), render Search Bar instead of status
	if state.ActiveInput == 5 {
		searchLabel := lipgloss.NewStyle().
			Foreground(m.Styles.ColorBase).
			Background(m.Styles.ColorYellow).
			Bold(true).
			Padding(0, 1).
			Render("SEARCH /")

		searchInput := lipgloss.NewStyle().
			Background(m.Styles.ColorSurface).
			Padding(0, 1).
			Width(m.Width - lipgloss.Width(searchLabel)).
			Render(state.InputSearch.View())

		return lipgloss.JoinHorizontal(lipgloss.Top, searchLabel, searchInput)
	}

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

	rightSection := fmt.Sprintf("%s help • %s save • %s export • %s theme • / search • q quit",
		iconHelp, iconSave, iconExport, iconGear)
	sections = append(sections, m.Styles.StatusRight.Render(rightSection))

	footer := lipgloss.JoinHorizontal(lipgloss.Top, sections...)

	return lipgloss.NewStyle().
		Width(m.Width).
		Background(m.Styles.ColorBase).
		Render(footer)
}

func (m AppModel) renderGlobalSearchView() string {
	modalWidth := min(m.Width-10, 70)
	modalHeight := min(m.Height-10, 20)
	contentWidth := modalWidth - 4

	title := lipgloss.NewStyle().
		Bold(true).
		Foreground(m.Styles.ColorMauve).
		Background(m.Styles.ColorBase).
		Width(contentWidth).
		Align(lipgloss.Center).
		Render(iconFolder + " Global File Search")

	// Input Box
	inputBox := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(m.Styles.ColorMauve).
		BorderBackground(m.Styles.ColorBase).
		Background(m.Styles.ColorBase).
		Padding(0, 1).
		Width(contentWidth - 2).
		MarginTop(1).
		Render(m.GlobalSearchInput.View())

	// Results List
	var results []string
	if len(m.GlobalSearchFiles) == 0 && m.GlobalSearchInput.Value() != "" {
		results = append(results, lipgloss.NewStyle().Foreground(m.Styles.ColorSubtext).Render("No results found."))
	} else {
		// Calculate visible range for scrolling
		start := 0
		if m.GlobalSearchSelect > 10 {
			start = m.GlobalSearchSelect - 10
		}
		end := min(start+10, len(m.GlobalSearchFiles)) // Modernized using min

		space := m.Session.GetActiveSpace()
		query := m.GlobalSearchInput.Value()

		for i := start; i < end; i++ {
			file := m.GlobalSearchFiles[i]
			relPath, _ := filepath.Rel(space.RootPath, file)
			// Normalize for display consistency
			displayPath := filepath.ToSlash(relPath)

			style := lipgloss.NewStyle().Foreground(m.Styles.ColorText)
			if i == m.GlobalSearchSelect {
				style = style.Foreground(m.Styles.ColorMauve).Bold(true).Background(m.Styles.ColorSurface)
				displayPath = "➜ " + displayPath
			} else {
				displayPath = "  " + displayPath
			}

			// Highlight matches in result list
			var styledName string
			// We match against the normalized path
			if matched, indices := SimpleFuzzyMatch(query, displayPath); matched && query != "" {
				var sb strings.Builder
				lastIdx := 0

				// Fix deprecated style.Copy() by assignment
				highlightStyle := style
				highlightStyle = highlightStyle.Foreground(m.Styles.ColorYellow).Bold(true)

				for _, idx := range indices {
					// Append text before match
					sb.WriteString(style.Render(displayPath[lastIdx:idx]))
					// Append match with highlight
					sb.WriteString(highlightStyle.Render(string(displayPath[idx])))
					lastIdx = idx + 1
				}
				sb.WriteString(style.Render(displayPath[lastIdx:]))
				styledName = sb.String()
			} else {
				styledName = style.Render(displayPath)
			}

			results = append(results, styledName)
		}
	}

	resultsList := lipgloss.JoinVertical(lipgloss.Left, results...)
	resultsBox := lipgloss.NewStyle().
		Width(contentWidth).
		Height(modalHeight - 8). // Approximate remaining space
		MarginTop(1).
		Render(resultsList)

	hints := lipgloss.NewStyle().
		Foreground(m.Styles.ColorSubtext).
		Italic(true).
		Background(m.Styles.ColorBase).
		Width(contentWidth).
		Align(lipgloss.Center).
		MarginTop(1).
		Render("Up/Down to Navigate • Enter to Jump • Esc to Cancel")

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		inputBox,
		resultsBox,
		hints,
	)

	box := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(m.Styles.ColorMauve).
		BorderBackground(m.Styles.ColorBase).
		Background(m.Styles.ColorBase).
		Padding(1, 2).
		Width(modalWidth).
		Height(modalHeight).
		Render(content)

	return lipgloss.Place(
		m.Width, m.Height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceBackground(m.Styles.ColorBase),
		lipgloss.WithWhitespaceChars(" "),
	)
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
			Background(m.Styles.ColorBase). // Changed to Base
			Bold(true).
			Width(14).
			Render(keyText)

		descText := binding.Help().Desc
		descStyled := lipgloss.NewStyle().
			Foreground(m.Styles.ColorText).
			Background(m.Styles.ColorBase). // Changed to Base
			Width(22).
			Render(descText)

		itemContent := lipgloss.JoinHorizontal(lipgloss.Top, keyStyled, descStyled)

		item := lipgloss.NewStyle().
			Background(m.Styles.ColorBase). // Changed to Base
			Width(itemWidth).
			Render(itemContent)

		rowItems = append(rowItems, item)

		if len(rowItems) >= maxCols {
			row := lipgloss.JoinHorizontal(lipgloss.Top, rowItems...)

			rowWidth := lipgloss.Width(row)
			contentWidth := maxCols * itemWidth
			remainingWidth := max(0, contentWidth-rowWidth)

			if remainingWidth > 0 {
				filler := lipgloss.NewStyle().
					Background(m.Styles.ColorBase). // Changed to Base
					Width(remainingWidth).
					Render(" ")
				row = lipgloss.JoinHorizontal(lipgloss.Top, row, filler)
			}

			rows = append(rows, row)
			rowItems = nil
		}
	}

	if len(rowItems) > 0 {
		row := lipgloss.JoinHorizontal(lipgloss.Top, rowItems...)

		rowWidth := lipgloss.Width(row)
		contentWidth := maxCols * itemWidth
		remainingWidth := max(0, contentWidth-rowWidth)

		if remainingWidth > 0 {
			filler := lipgloss.NewStyle().
				Background(m.Styles.ColorBase). // Changed to Base
				Width(remainingWidth).
				Render(" ")
			row = lipgloss.JoinHorizontal(lipgloss.Top, row, filler)
		}

		rows = append(rows, row)
	}

	helpBlock := lipgloss.JoinVertical(lipgloss.Left, rows...)

	title := lipgloss.NewStyle().
		Bold(true).
		Foreground(m.Styles.ColorMauve).
		Background(m.Styles.ColorBase). // Changed to Base
		Width(maxCols * itemWidth).
		Align(lipgloss.Center).
		Render(iconHelp + " Keyboard Shortcuts")

	spacer := lipgloss.NewStyle().
		Background(m.Styles.ColorBase). // Changed to Base
		Width(maxCols * itemWidth).
		Height(1).
		Render(" ")

	content := lipgloss.JoinVertical(lipgloss.Left, title, spacer, helpBlock)

	boxWidth := min(m.Width-4, maxCols*itemWidth+4)

	// 1. Render the main box first
	box := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(m.Styles.ColorMauve).
		BorderBackground(m.Styles.ColorBase).
		Background(m.Styles.ColorBase). // Changed to Base
		Padding(1, 2).
		Width(boxWidth).
		Render(content)

	// 2. Measure the ACTUAL rendered width (includes border + padding)
	totalWidth := lipgloss.Width(box)

	// 3. Apply the TOTAL width to the footer elements
	closeHintRow := lipgloss.NewStyle().
		Foreground(m.Styles.ColorSubtext).
		Background(m.Styles.ColorBase).
		Italic(true).
		Width(totalWidth).
		Align(lipgloss.Center).
		Render("Press ? to close")

	spacerBeforeHint := lipgloss.NewStyle().
		Background(m.Styles.ColorBase).
		Width(totalWidth).
		Height(1).
		Render(" ")

	finalContent := lipgloss.JoinVertical(lipgloss.Center, box, spacerBeforeHint, closeHintRow)

	return lipgloss.Place(
		m.Width, m.Height,
		lipgloss.Center, lipgloss.Center,
		finalContent,
		lipgloss.WithWhitespaceBackground(m.Styles.ColorBase),
		lipgloss.WithWhitespaceChars(" "),
	)
}

func (m AppModel) renderNewTabView() string {
	// Calculate dynamic width based on screen size, capped at 60
	modalWidth := min(m.Width-10, 60)
	contentWidth := modalWidth - 4 // Account for padding (2 on each side)

	title := lipgloss.NewStyle().
		Bold(true).
		Foreground(m.Styles.ColorMauve).
		Background(m.Styles.ColorBase). // Changed to Base
		Width(contentWidth).
		Align(lipgloss.Center).
		Render(iconFolder + " Open New Tab")

	description := lipgloss.NewStyle().
		Foreground(m.Styles.ColorSubtext).
		Background(m.Styles.ColorBase). // Changed to Base
		Width(contentWidth).
		Align(lipgloss.Center).
		MarginTop(1).
		Render("Enter the full path to a directory:")

	// Input Box
	inputBox := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(m.Styles.ColorMauve).
		BorderBackground(m.Styles.ColorBase). // Changed to Base
		Background(m.Styles.ColorBase).       // Changed to Base
		Padding(0, 1).
		Width(contentWidth - 2). // Ensure it fills the modal
		MarginTop(1).
		Render(m.NewTabInput.View())

	hints := lipgloss.NewStyle().
		Foreground(m.Styles.ColorSubtext).
		Italic(true).
		Background(m.Styles.ColorBase). // Changed to Base
		Width(contentWidth).
		Align(lipgloss.Center).
		MarginTop(1).
		Render("Enter to confirm • Esc to cancel")

	// Join vertically without empty string spacers
	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		description,
		inputBox,
		hints,
	)

	box := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(m.Styles.ColorMauve).
		BorderBackground(m.Styles.ColorBase).
		Background(m.Styles.ColorBase). // Changed to Base
		Padding(1, 2).
		Width(modalWidth).
		Render(content)

	return lipgloss.Place(
		m.Width, m.Height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceBackground(m.Styles.ColorBase),
		lipgloss.WithWhitespaceChars(" "),
	)
}
