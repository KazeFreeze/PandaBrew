// Package tui implements the terminal user interface logic.
package tui

import "github.com/charmbracelet/bubbles/key"

// --- Key Bindings ---
type keyMap struct {
	Up          key.Binding
	Down        key.Binding
	Left        key.Binding
	Right       key.Binding
	Select      key.Binding
	Quit        key.Binding
	Save        key.Binding
	Export      key.Binding
	Help        key.Binding
	Tab         key.Binding
	NewTab      key.Binding
	CloseTab    key.Binding
	Root        key.Binding
	Output      key.Binding
	Include     key.Binding
	Exclude     key.Binding
	ToggleI     key.Binding
	ToggleC     key.Binding
	ToggleX     key.Binding
	ToggleV     key.Binding
	Refresh     key.Binding
	SelectAll   key.Binding
	DeselectAll key.Binding
	ToggleTheme key.Binding
	// Search Bindings
	Search      key.Binding
	NextMatch   key.Binding
	PrevMatch   key.Binding
	ClearSearch key.Binding
}

func (k keyMap) ShortHelp() []key.Binding {
	return []key.Binding{k.Help, k.Quit}
}

func (k keyMap) FullHelp() [][]key.Binding {
	return [][]key.Binding{
		{k.Up, k.Down, k.Left, k.Right},
		{k.Select, k.Tab, k.NewTab, k.CloseTab},
		{k.Search, k.NextMatch, k.PrevMatch, k.ClearSearch}, // Added Search row
		{k.Save, k.Export, k.Root, k.Output},
		{k.Include, k.Exclude, k.Refresh},
		{k.ToggleI, k.ToggleC, k.ToggleX, k.ToggleV},
		{k.ToggleTheme, k.Help, k.Quit},
	}
}

var keys = keyMap{
	Up: key.NewBinding(
		key.WithKeys("up", "k"),
		key.WithHelp("↑/k", "move up"),
	),
	Down: key.NewBinding(
		key.WithKeys("down", "j"),
		key.WithHelp("↓/j", "move down"),
	),
	Left: key.NewBinding(
		key.WithKeys("left", "h"),
		key.WithHelp("←/h", "collapse"),
	),
	Right: key.NewBinding(
		key.WithKeys("right", "l", "enter"),
		key.WithHelp("→/l", "expand"),
	),
	Select: key.NewBinding(
		key.WithKeys(" "),
		key.WithHelp("space", "toggle select"),
	),
	Quit: key.NewBinding(
		key.WithKeys("q", "ctrl+c"),
		key.WithHelp("q", "quit"),
	),
	Save: key.NewBinding(
		key.WithKeys("ctrl+s"),
		key.WithHelp("ctrl+s", "save session"),
	),
	Export: key.NewBinding(
		key.WithKeys("ctrl+e"),
		key.WithHelp("ctrl+e", "export"),
	),
	Help: key.NewBinding(
		key.WithKeys("?"),
		key.WithHelp("?", "toggle help"),
	),
	Tab: key.NewBinding(
		key.WithKeys("tab"),
		key.WithHelp("tab", "switch tab"),
	),
	NewTab: key.NewBinding(
		key.WithKeys("ctrl+n"),
		key.WithHelp("ctrl+n", "new tab"),
	),
	CloseTab: key.NewBinding(
		key.WithKeys("ctrl+w"),
		key.WithHelp("ctrl+w", "close tab"),
	),
	Refresh: key.NewBinding(
		key.WithKeys("ctrl+r"),
		key.WithHelp("ctrl+r", "refresh dir"),
	),
	Root: key.NewBinding(
		key.WithKeys("r"),
		key.WithHelp("r", "edit root"),
	),
	Output: key.NewBinding(
		key.WithKeys("o"),
		key.WithHelp("o", "edit output"),
	),
	Include: key.NewBinding(
		key.WithKeys("f"),
		key.WithHelp("f", "incl pattern"),
	),
	Exclude: key.NewBinding(
		key.WithKeys("g"),
		key.WithHelp("g", "excl pattern"),
	),
	ToggleI: key.NewBinding(
		key.WithKeys("i"),
		key.WithHelp("i", "toggle include mode"),
	),
	ToggleC: key.NewBinding(
		key.WithKeys("c"),
		key.WithHelp("c", "toggle context"),
	),
	ToggleX: key.NewBinding(
		key.WithKeys("x"),
		key.WithHelp("x", "toggle excluded"),
	),
	ToggleV: key.NewBinding(
		key.WithKeys("v"),
		key.WithHelp("v", "toggle view structure"),
	),
	SelectAll: key.NewBinding(
		key.WithKeys("ctrl+a"),
		key.WithHelp("ctrl+a", "select all"),
	),
	DeselectAll: key.NewBinding(
		key.WithKeys("ctrl+d"),
		key.WithHelp("ctrl+d", "deselect all"),
	),
	ToggleTheme: key.NewBinding(
		key.WithKeys("ctrl+t"),
		key.WithHelp("ctrl+t", "switch theme"),
	),
	// Search Implementation
	Search: key.NewBinding(
		key.WithKeys("/"),
		key.WithHelp("/", "search"),
	),
	NextMatch: key.NewBinding(
		key.WithKeys("n"),
		key.WithHelp("n", "next match"),
	),
	PrevMatch: key.NewBinding(
		key.WithKeys("N"),
		key.WithHelp("N", "prev match"),
	),
	ClearSearch: key.NewBinding(
		key.WithKeys("esc"),
		key.WithHelp("esc", "clear/cancel"),
	),
}
