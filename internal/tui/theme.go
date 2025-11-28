// Package tui implements the terminal user interface logic.
package tui

import "github.com/charmbracelet/lipgloss"

// ThemePalette defines the semantic colors for the UI
type ThemePalette struct {
	Base     lipgloss.Color // Background
	Surface  lipgloss.Color // Panel/Tab background
	Overlay  lipgloss.Color // Borders/Inactive Text
	Text     lipgloss.Color // Main Text
	Subtext  lipgloss.Color // Dimmed Text
	Mauve    lipgloss.Color // Primary Accent (Focus, Borders)
	Red      lipgloss.Color // Error/Archives
	Blue     lipgloss.Color // Info/Folders
	Green    lipgloss.Color // Success/Markdown
	Yellow   lipgloss.Color // Warning/JSON
	Peach    lipgloss.Color // HTML/Orange
	Lavender lipgloss.Color // Secondary Accent
}

var (
	ThemeMocha = ThemePalette{
		Base:     lipgloss.Color("#1e1e2e"),
		Surface:  lipgloss.Color("#313244"),
		Overlay:  lipgloss.Color("#6c7086"),
		Text:     lipgloss.Color("#cdd6f4"),
		Subtext:  lipgloss.Color("#a6adc8"),
		Mauve:    lipgloss.Color("#cba6f7"),
		Red:      lipgloss.Color("#f38ba8"),
		Blue:     lipgloss.Color("#89b4fa"),
		Green:    lipgloss.Color("#a6e3a1"),
		Yellow:   lipgloss.Color("#f9e2af"),
		Peach:    lipgloss.Color("#fab387"),
		Lavender: lipgloss.Color("#b4befe"),
	}

	ThemeMacchiato = ThemePalette{
		Base:     lipgloss.Color("#24273a"),
		Surface:  lipgloss.Color("#363a4f"),
		Overlay:  lipgloss.Color("#6e738d"),
		Text:     lipgloss.Color("#cad3f5"),
		Subtext:  lipgloss.Color("#a5adcb"),
		Mauve:    lipgloss.Color("#c6a0f6"),
		Red:      lipgloss.Color("#ed8796"),
		Blue:     lipgloss.Color("#8aadf4"),
		Green:    lipgloss.Color("#a6da95"),
		Yellow:   lipgloss.Color("#eed49f"),
		Peach:    lipgloss.Color("#f5a97f"),
		Lavender: lipgloss.Color("#b7bdf8"),
	}

	ThemeFrappe = ThemePalette{
		Base:     lipgloss.Color("#303446"),
		Surface:  lipgloss.Color("#414559"),
		Overlay:  lipgloss.Color("#737994"),
		Text:     lipgloss.Color("#c6d0f5"),
		Subtext:  lipgloss.Color("#a5adce"),
		Mauve:    lipgloss.Color("#ca9ee6"),
		Red:      lipgloss.Color("#e78284"),
		Blue:     lipgloss.Color("#8caaee"),
		Green:    lipgloss.Color("#a6d189"),
		Yellow:   lipgloss.Color("#e5c890"),
		Peach:    lipgloss.Color("#ef9f76"),
		Lavender: lipgloss.Color("#babbf1"),
	}

	ThemeLatte = ThemePalette{
		Base:     lipgloss.Color("#eff1f5"),
		Surface:  lipgloss.Color("#ccd0da"),
		Overlay:  lipgloss.Color("#9ca0b0"),
		Text:     lipgloss.Color("#4c4f69"),
		Subtext:  lipgloss.Color("#6c6f85"),
		Mauve:    lipgloss.Color("#8839ef"),
		Red:      lipgloss.Color("#d20f39"),
		Blue:     lipgloss.Color("#1e66f5"),
		Green:    lipgloss.Color("#40a02b"),
		Yellow:   lipgloss.Color("#df8e1d"),
		Peach:    lipgloss.Color("#fe640b"),
		Lavender: lipgloss.Color("#7287fd"),
	}
)

func GetTheme(name string) ThemePalette {
	switch name {
	case "latte":
		return ThemeLatte
	case "frappe":
		return ThemeFrappe
	case "macchiato":
		return ThemeMacchiato
	default:
		return ThemeMocha
	}
}

func GetNextTheme(current string) string {
	switch current {
	case "mocha":
		return "latte"
	case "latte":
		return "frappe"
	case "frappe":
		return "macchiato"
	default:
		return "mocha"
	}
}
