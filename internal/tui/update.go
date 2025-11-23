package tui

import (
	"fmt"
	"path/filepath"

	"pandabrew/internal/core"

	"github.com/charmbracelet/bubbles/key"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
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
	}

	// Handle New Tab Input Mode (highest priority)
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

	// Handle Regular Inputs (second priority)
	if state != nil && state.ActiveInput > 0 {
		switch msg := msg.(type) {
		case tea.KeyMsg:
			switch msg.String() {
			case "esc":
				state.ActiveInput = 0
				blurAll(state)
				return m, nil
			case "enter":
				state.ActiveInput = 0
				blurAll(state)
				// Sync values back to Config
				if state.InputRoot.Value() != space.RootPath {
					space.RootPath = state.InputRoot.Value()
					// Reset tree on root change
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

				// Parse comma-separated lists for patterns
				space.Config.IncludePatterns = splitClean(state.InputInclude.Value())
				space.Config.ExcludePatterns = splitClean(state.InputExclude.Value())

				return m, tea.Batch(cmds...)
			}
		}

		// Forward to active input
		switch state.ActiveInput {
		case 1:
			state.InputRoot, cmd = state.InputRoot.Update(msg)
		case 2:
			state.InputOutput, cmd = state.InputOutput.Update(msg)
		case 3:
			state.InputInclude, cmd = state.InputInclude.Update(msg)
		case 4:
			state.InputExclude, cmd = state.InputExclude.Update(msg)
		}
		return m, cmd
	}

	switch msg := msg.(type) {

	// Async Results
	case DirLoadedMsg:
		m.Loading = false
		if msg.Err != nil {
			m.StatusMessage = "Error: " + msg.Err.Error()
		} else {
			if state != nil {
				m.populateChildren(state, msg.Path, msg.Entries)
				state.rebuildVisibleList()
				m.StatusMessage = fmt.Sprintf("Loaded %d items", len(msg.Entries))
			}
		}

	case NewTabValidatedMsg:
		if msg.Valid {
			// Add the new space
			sm := core.NewSessionManager("")
			newSpace, err := sm.AddSpaceFromPath(m.Session, msg.Path)
			if err == nil {
				m.TabStates[newSpace.ID] = newTabState(newSpace)
				m.StatusMessage = fmt.Sprintf("✓ Opened new tab: %s", filepath.Base(msg.Path))
				m.ShowNewTab = false
				m.NewTabInput.Blur()
				m.NewTabInput.SetValue("")
				cmds = append(cmds, loadDirectoryCmd(newSpace.RootPath))
			} else {
				m.StatusMessage = "Error: " + err.Error()
			}
		} else {
			m.StatusMessage = "Invalid path: " + msg.Error
			m.ShowNewTab = false
			m.NewTabInput.Blur()
			m.NewTabInput.SetValue("")
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
		case key.Matches(msg, m.keys.Quit):
			return m, tea.Quit

		case key.Matches(msg, m.keys.Help):
			m.ShowHelp = !m.ShowHelp

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
					// Remove the tab state
					delete(m.TabStates, space.ID)
					m.StatusMessage = fmt.Sprintf("✓ Closed tab: %s", filepath.Base(space.RootPath))

					// Load the new active space if needed
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
				currIdx := 0
				for i, s := range m.Session.Spaces {
					if s.ID == space.ID {
						currIdx = i
						break
					}
				}
				nextIdx := (currIdx + 1) % len(m.Session.Spaces)
				m.Session.ActiveSpaceID = m.Session.Spaces[nextIdx].ID
				// Init new tab if needed
				newSpace := m.Session.GetActiveSpace()
				if newSpace != nil {
					newState := m.TabStates[newSpace.ID]
					if newState != nil && len(newState.TreeRoot.Children) == 0 {
						cmds = append(cmds, loadDirectoryCmd(newSpace.RootPath))
					}
				}
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
					// Jump to parent
					for i, n := range state.VisibleNodes {
						if n == node.Parent {
							state.CursorIndex = i
							break
						}
					}
				}
			}

		case key.Matches(msg, m.keys.Save):
			sm := core.NewSessionManager("")
			if err := sm.Save(m.Session); err != nil {
				m.StatusMessage = iconSave + " Error: " + err.Error()
			} else {
				m.StatusMessage = iconSave + " Session Saved"
			}

		case key.Matches(msg, m.keys.Export):
			if space != nil {
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
