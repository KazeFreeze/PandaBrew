package tui

import "github.com/charmbracelet/bubbles/key"

// --- Key Bindings ---
type keyMap struct {
	Up      key.Binding
	Down    key.Binding
	Left    key.Binding
	Right   key.Binding
	Select  key.Binding
	Quit    key.Binding
	Save    key.Binding
	Export  key.Binding
	Help    key.Binding
	Tab     key.Binding
	NewTab  key.Binding
	Root    key.Binding
	Output  key.Binding
	Include key.Binding
	Exclude key.Binding
	ToggleI key.Binding
	ToggleC key.Binding
	ToggleX key.Binding
}

func (k keyMap) ShortHelp() []key.Binding {
	return []key.Binding{k.Help, k.Quit}
}

func (k keyMap) FullHelp() [][]key.Binding {
	return [][]key.Binding{
		{k.Up, k.Down, k.Left, k.Right},
		{k.Select, k.Tab, k.NewTab, k.Save},
		{k.Export, k.Root, k.Output, k.Include},
		{k.Exclude, k.ToggleI, k.ToggleC, k.ToggleX},
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
		key.WithHelp("←/h", "collapse folder"),
	),
	Right: key.NewBinding(
		key.WithKeys("right", "l", "enter"),
		key.WithHelp("→/l/enter", "expand folder"),
	),
	Select: key.NewBinding(
		key.WithKeys(" "),
		key.WithHelp("space", "toggle selection"),
	),
	Quit: key.NewBinding(
		key.WithKeys("q", "ctrl+c"),
		key.WithHelp("q/ctrl+c", "quit app"),
	),
	Save: key.NewBinding(
		key.WithKeys("ctrl+s"),
		key.WithHelp("ctrl+s", "save session"),
	),
	Export: key.NewBinding(
		key.WithKeys("ctrl+e"),
		key.WithHelp("ctrl+e", "export to file"),
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
	Root: key.NewBinding(
		key.WithKeys("r"),
		key.WithHelp("r", "edit root path"),
	),
	Output: key.NewBinding(
		key.WithKeys("o"),
		key.WithHelp("o", "edit output file"),
	),
	Include: key.NewBinding(
		key.WithKeys("f"),
		key.WithHelp("f", "edit include patterns"),
	),
	Exclude: key.NewBinding(
		key.WithKeys("g"),
		key.WithHelp("g", "edit exclude patterns"),
	),
	ToggleI: key.NewBinding(
		key.WithKeys("i"),
		key.WithHelp("i", "toggle include mode"),
	),
	ToggleC: key.NewBinding(
		key.WithKeys("c"),
		key.WithHelp("c", "toggle show context"),
	),
	ToggleX: key.NewBinding(
		key.WithKeys("x"),
		key.WithHelp("x", "toggle show excluded"),
	),
}
