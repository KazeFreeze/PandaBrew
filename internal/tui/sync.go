// Package tui implements the terminal user interface logic.
package tui

func (m AppModel) syncStateToSession() {
	space := m.Session.GetActiveSpace()
	if space == nil {
		return
	}
	state := m.TabStates[space.ID]
	if state == nil {
		return
	}

	// 1. Save Expanded Paths
	if state.TreeRoot != nil {
		space.ExpandedPaths = CollectExpandedPaths(state.TreeRoot)
	}

	// 2. Save Cursor Path
	if len(state.VisibleNodes) > 0 && state.CursorIndex >= 0 && state.CursorIndex < len(state.VisibleNodes) {
		space.CursorPath = state.VisibleNodes[state.CursorIndex].FullPath
	}
}
