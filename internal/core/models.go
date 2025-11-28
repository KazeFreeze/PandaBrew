// Package core implements the headless logic for file traversal,
// filtering, and report generation.
package core

import (
	"time"
)

// Session represents the global application state.
type Session struct {
	ID            string            `json:"id"`
	ActiveSpaceID string            `json:"active_space_id"`
	Spaces        []*DirectorySpace `json:"spaces"`
	Theme         string            `json:"theme"` // Added for persistence
	CreatedAt     time.Time         `json:"created_at"`
	UpdatedAt     time.Time         `json:"updated_at"`
}

// DirectorySpace represents a single project workspace (a "Tab").
type DirectorySpace struct {
	ID             string           `json:"id"`
	RootPath       string           `json:"root_path"`
	OutputFilePath string           `json:"output_path"`
	Config         ExtractionConfig `json:"config"`
	ExpandedPaths  []string         `json:"expanded_paths"`
	CursorPath     string           `json:"cursor_path"`
}

// ExtractionConfig controls how the walker and generator behave.
type ExtractionConfig struct {
	IncludePatterns  []string `json:"include_patterns"`
	ExcludePatterns  []string `json:"exclude_patterns"`
	ManualSelections []string `json:"manual_selections"`

	// AlwaysShowStructure contains paths (directories) whose immediate children
	// should be listed in the structure view regardless of exclusion status.
	// This is the data payload derived from the TUI state.
	AlwaysShowStructure []string `json:"always_show_structure"`

	// Options
	IncludeMode   bool `json:"include_mode"`
	FilenamesOnly bool `json:"filenames_only"`
	MinifyContent bool `json:"minify_content"`

	// Visibility Options
	ShowExcluded  bool `json:"show_excluded"`  // Show EVERYTHING
	ShowContext   bool `json:"show_context"`   // Show SIBLINGS of selected items
	StructureView bool `json:"structure_view"` // Toggle: If true, expanded TUI folders are added to AlwaysShowStructure
}

// ReportMetadata holds data for the final report header.
type ReportMetadata struct {
	Timestamp     time.Time
	TotalFiles    int
	TotalTokens   int
	SelectionMode string
}

// DirEntry represents a single file/folder for lazy loading.
type DirEntry struct {
	Name     string
	FullPath string
	IsDir    bool
	Size     int64
}
