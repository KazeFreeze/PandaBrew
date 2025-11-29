// Package tui implements the terminal user interface logic.
package tui

import (
	"fmt"
	"path/filepath"
	"strings"

	"pandabrew/internal/core"

	"github.com/charmbracelet/bubbles/key"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

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
		m.Help.Width = msg.Width

	case NewTabValidatedMsg:
		if msg.Valid {
			sm := core.NewSessionManager("")
			newSpace, err := sm.AddSpaceFromPath(m.Session, msg.Path)
			if err == nil {
				m.TabStates[newSpace.ID] = newTabState(newSpace, m.Styles)
				m.StatusMessage = fmt.Sprintf("✓ Opened new tab: %s", filepath.Base(msg.Path))
				m.ShowNewTab = false
				m.NewTabInput.Blur()
				m.NewTabInput.SetValue("")
				cmds = append(cmds, loadDirectoryCmd(newSpace.RootPath))
				_ = sm.Save(m.Session)
			} else {
				m.StatusMessage = "Error: " + err.Error()
			}
		} else {
			m.StatusMessage = "Invalid path: " + msg.Error
			m.ShowNewTab = false
			m.NewTabInput.Blur()
			m.NewTabInput.SetValue("")
		}
		return m, tea.Batch(cmds...)
	}

	// Handle New Tab Input Mode
	if m.ShowNewTab {
		switch msg := msg.(type) {
		case tea.KeyMsg:
			switch msg.String() {
			case "esc":
				m.ShowNewTab = false
				m.NewTabInput.Blur()
				m.NewTabInput.SetValue("")
				return m, nil
			case "enter":
				path := m.NewTabInput.Value()
				if path != "" {
					m.StatusMessage = "Validating path..."
					return m, validateNewTabCmd(path)
				}
				m.ShowNewTab = false
				m.NewTabInput.Blur()
				return m, nil
			}
		}
		m.NewTabInput, cmd = m.NewTabInput.Update(msg)
		return m, cmd
	}

	// Handle Regular Inputs (including Search - ActiveInput 5)
	if state != nil && state.ActiveInput > 0 {
		switch msg := msg.(type) {
		case tea.KeyMsg:
			switch msg.String() {
			case "esc":
				state.ActiveInput = 0
				state.InputSearch.SetValue("") // Clear search input on cancel
				blurAll(state)
				return m, nil
			case "enter":
				state.ActiveInput = 0
				blurAll(state)

				// Handle Config Inputs
				if state.InputRoot.Value() != space.RootPath {
					space.RootPath = state.InputRoot.Value()
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
				space.Config.IncludePatterns = splitClean(state.InputInclude.Value())
				space.Config.ExcludePatterns = splitClean(state.InputExclude.Value())

				// Handle Search Input Confirmation
				if state.InputSearch.Value() != "" {
					state.SearchQuery = state.InputSearch.Value()
					state.PerformSearch()
					if len(state.MatchIndices) > 0 {
						state.CursorIndex = state.MatchIndices[0]
						state.MatchPtr = 0
						m.StatusMessage = fmt.Sprintf("Found %d matches", len(state.MatchIndices))
					} else {
						m.StatusMessage = "No matches found"
					}
					// Keep search query but clear input box logic for cleaner UI next time?
					// No, keep value so user can edit it.
				}

				sm := core.NewSessionManager("")
				_ = sm.Save(m.Session)
				return m, tea.Batch(cmds...)
			}
		}

		switch state.ActiveInput {
		case 1:
			state.InputRoot, cmd = state.InputRoot.Update(msg)
		case 2:
			state.InputOutput, cmd = state.InputOutput.Update(msg)
		case 3:
			state.InputInclude, cmd = state.InputInclude.Update(msg)
		case 4:
			state.InputExclude, cmd = state.InputExclude.Update(msg)
		case 5:
			state.InputSearch, cmd = state.InputSearch.Update(msg)
		}
		return m, cmd
	}

	switch msg := msg.(type) {

	case DirLoadedMsg:
		m.Loading = false
		if msg.Err != nil {
			m.StatusMessage = "Error: " + msg.Err.Error()
		} else {
			if state != nil {
				m.populateChildren(state, msg.Path, msg.Entries)

				var newCmds []tea.Cmd
				var checkChildren func(node *TreeNode)
				checkChildren = func(node *TreeNode) {
					for _, child := range node.Children {
						if child.IsDir && state.TargetExpandedPaths[child.FullPath] {
							if !child.Expanded {
								child.Expanded = true
								newCmds = append(newCmds, loadDirectoryCmd(child.FullPath))
							}
							if len(child.Children) > 0 {
								checkChildren(child)
							}
						}
					}
				}

				var find func(n *TreeNode) *TreeNode
				find = func(n *TreeNode) *TreeNode {
					if n.FullPath == msg.Path {
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
					loadedNode := find(state.TreeRoot)
					if loadedNode != nil {
						checkChildren(loadedNode)
					}
				}
				cmds = append(cmds, newCmds...)

				state.rebuildVisibleList()

				if state.TargetCursorPath != "" {
					for i, node := range state.VisibleNodes {
						if node.FullPath == state.TargetCursorPath {
							state.CursorIndex = i
							state.TargetCursorPath = ""
							break
						}
					}
				}

				m.StatusMessage = fmt.Sprintf("Loaded %d items", len(msg.Entries))
			}
		}

	case ExportProgressMsg:
		m.ExportProcessed = msg.Processed
		m.ExportTotal = msg.Total
		if msg.Total > 0 {
			m.ExportProgress = float64(msg.Processed) / float64(msg.Total)
		}

	case ExportCompleteMsg:
		m.Loading = false
		m.ExportProgress = 0
		m.ExportTotal = 0
		m.ExportProcessed = 0
		if msg.Err != nil {
			m.StatusMessage = "Failed: " + msg.Err.Error()
		} else {
			m.StatusMessage = fmt.Sprintf("✓ Exported %d files (~%d tokens) to %s",
				msg.Count, msg.Tokens, filepath.Base(space.OutputFilePath))
		}

	case tea.KeyMsg:
		switch {
		// Restore ToggleTheme logic with dynamic input styling
		case key.Matches(msg, m.keys.ToggleTheme):
			nextTheme := GetNextTheme(m.Session.Theme)
			m.Session.Theme = nextTheme

			palette := GetTheme(nextTheme)
			m.Styles = DefaultStyles(palette)

			m.Help.Styles.FullKey = m.Styles.HelpKey
			m.Help.Styles.ShortKey = m.Styles.HelpKey
			m.Help.Styles.FullDesc = m.Styles.HelpDesc
			m.Help.Styles.ShortDesc = m.Styles.HelpDesc
			m.Spinner.Style = lipgloss.NewStyle().Foreground(m.Styles.ColorMauve)

			// Fix: Dynamically update all text inputs to use the new theme's background color
			updateInputStyle(&m.NewTabInput, m.Styles)
			for _, ts := range m.TabStates {
				updateInputStyle(&ts.InputRoot, m.Styles)
				updateInputStyle(&ts.InputOutput, m.Styles)
				updateInputStyle(&ts.InputInclude, m.Styles)
				updateInputStyle(&ts.InputExclude, m.Styles)
				updateInputStyle(&ts.InputSearch, m.Styles) // Update Search Input
			}

			sm := core.NewSessionManager("")
			_ = sm.Save(m.Session)

			displayTheme := strings.ToUpper(string(nextTheme[0])) + nextTheme[1:]
			m.StatusMessage = "Theme: " + displayTheme

		case key.Matches(msg, m.keys.Quit):
			m.syncStateToSession()
			sm := core.NewSessionManager("")
			_ = sm.Save(m.Session)
			return m, tea.Quit

		case key.Matches(msg, m.keys.ClearSearch):
			if state != nil {
				// Escape clears search logic
				if state.SearchQuery != "" {
					state.SearchQuery = ""
					state.MatchIndices = []int{}
					state.InputSearch.SetValue("")
					m.StatusMessage = "Search cleared"
				}
			}

		case key.Matches(msg, m.keys.SelectAll):
			if space != nil {
				selectAll(space)
				sm := core.NewSessionManager("")
				_ = sm.Save(m.Session)
				m.StatusMessage = "✓ Selected All"
			}

		case key.Matches(msg, m.keys.DeselectAll):
			if space != nil {
				deselectAll(space)
				sm := core.NewSessionManager("")
				_ = sm.Save(m.Session)
				m.StatusMessage = "✓ Deselected All"
			}
		case key.Matches(msg, m.keys.Help):
			m.ShowHelp = !m.ShowHelp

		case key.Matches(msg, m.keys.Refresh):
			if state != nil && state.TreeRoot != nil {
				m.Loading = true
				m.StatusMessage = "Refreshing view..."
				cmds = append(cmds, loadDirectoryCmd(space.RootPath))
				expanded := CollectExpandedPaths(state.TreeRoot)
				for _, p := range expanded {
					if p != space.RootPath {
						cmds = append(cmds, loadDirectoryCmd(p))
					}
				}
			}

		case key.Matches(msg, m.keys.NewTab):
			m.ShowNewTab = true
			m.NewTabInput.Focus()
			return m, textinput.Blink

		case key.Matches(msg, m.keys.CloseTab):
			if space != nil && len(m.Session.Spaces) > 1 {
				sm := core.NewSessionManager("")
				if err := sm.RemoveSpace(m.Session, space.ID); err != nil {
					m.StatusMessage = "Error: " + err.Error()
				} else {
					delete(m.TabStates, space.ID)
					m.StatusMessage = fmt.Sprintf("✓ Closed tab: %s", filepath.Base(space.RootPath))
					newSpace := m.Session.GetActiveSpace()
					if newSpace != nil {
						newState := m.TabStates[newSpace.ID]
						if newState != nil && len(newState.TreeRoot.Children) == 0 {
							cmds = append(cmds, loadDirectoryCmd(newSpace.RootPath))
						}
					}
				}
			} else {
				m.StatusMessage = "Cannot close the last tab"
			}

		case key.Matches(msg, m.keys.Tab):
			if len(m.Session.Spaces) > 1 {
				m.syncStateToSession()
				currIdx := 0
				for i, s := range m.Session.Spaces {
					if s.ID == space.ID {
						currIdx = i
						break
					}
				}
				nextIdx := (currIdx + 1) % len(m.Session.Spaces)
				m.Session.ActiveSpaceID = m.Session.Spaces[nextIdx].ID
				newSpace := m.Session.GetActiveSpace()
				if newSpace != nil {
					newState := m.TabStates[newSpace.ID]
					if newState != nil && len(newState.TreeRoot.Children) == 0 {
						cmds = append(cmds, loadDirectoryCmd(newSpace.RootPath))
					}
				}
				sm := core.NewSessionManager("")
				_ = sm.Save(m.Session)
			}

		case key.Matches(msg, m.keys.Root):
			if state != nil {
				focusInput(state, 1)
			}
			return m, textinput.Blink
		case key.Matches(msg, m.keys.Output):
			if state != nil {
				focusInput(state, 2)
			}
			return m, textinput.Blink
		case key.Matches(msg, m.keys.Include):
			if state != nil {
				focusInput(state, 3)
			}
			return m, textinput.Blink
		case key.Matches(msg, m.keys.Exclude):
			if state != nil {
				focusInput(state, 4)
			}
			return m, textinput.Blink

		// Search Trigger
		case key.Matches(msg, m.keys.Search):
			if state != nil {
				focusInput(state, 5) // 5 = Search
			}
			return m, textinput.Blink

		// Search Navigation
		case key.Matches(msg, m.keys.NextMatch):
			if state != nil && len(state.MatchIndices) > 0 {
				state.MatchPtr++
				if state.MatchPtr >= len(state.MatchIndices) {
					state.MatchPtr = 0
				}
				state.CursorIndex = state.MatchIndices[state.MatchPtr]
			}

		case key.Matches(msg, m.keys.PrevMatch):
			if state != nil && len(state.MatchIndices) > 0 {
				state.MatchPtr--
				if state.MatchPtr < 0 {
					state.MatchPtr = len(state.MatchIndices) - 1
				}
				state.CursorIndex = state.MatchIndices[state.MatchPtr]
			}

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
		case key.Matches(msg, m.keys.ToggleV):
			if space != nil {
				space.Config.StructureView = !space.Config.StructureView
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
				sm := core.NewSessionManager("")
				_ = sm.Save(m.Session)
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
					for i, n := range state.VisibleNodes {
						if n == node.Parent {
							state.CursorIndex = i
							break
						}
					}
				}
			}

		case key.Matches(msg, m.keys.Save):
			m.syncStateToSession()
			sm := core.NewSessionManager("")
			if err := sm.Save(m.Session); err != nil {
				m.StatusMessage = iconSave + " Error: " + err.Error()
			} else {
				m.StatusMessage = iconSave + " Session Saved"
			}

		case key.Matches(msg, m.keys.Export):
			if space != nil {
				space.Config.AlwaysShowStructure = []string{}
				if space.Config.StructureView && state != nil && state.TreeRoot != nil {
					space.Config.AlwaysShowStructure = CollectExpandedPaths(state.TreeRoot)
				}

				m.Loading = true
				m.ExportProgress = 0
				m.StatusMessage = "Starting export..."
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

func updateInputStyle(t *textinput.Model, s Styles) {
	t.TextStyle = lipgloss.NewStyle().Background(s.ColorBase)
	t.PlaceholderStyle = lipgloss.NewStyle().
		Foreground(s.ColorSubtext).
		Background(s.ColorBase)
	t.Cursor.Style = lipgloss.NewStyle().Foreground(s.ColorMauve)
	t.Cursor.TextStyle = lipgloss.NewStyle().Background(s.ColorBase)
}
